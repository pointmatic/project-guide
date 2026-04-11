# Modes

A mode is a focused workflow that the LLM follows. Each mode has its own steps, prerequisites, and completion criteria. Switch modes to match the task at hand — planning, setup, coding, debugging, documentation, or refactoring.

## How Modes Work

When you run `project-guide mode <name>`, the tool:

1. Sets the active mode in `.project-guide.yml`
2. Re-renders `docs/project-guide/go.md` with the mode's template content
3. The LLM re-reads `go.md` to follow the new workflow

Each mode is either a **sequence** (one-time progression through steps) or a **cycle** (repeatable workflow you stay in). Sequence modes have a `next_mode` to suggest where to go after completion.

## Mode Reference

### Default

| Field | Value |
|-|-|
| **Type** | Sequence |
| **Next** | `plan_concept` |
| **Prerequisites** | None |

Getting started — full project lifecycle overview. The default mode for new projects walks through setup, planning, and implementation with links to specific modes. Use this when you're new to project-guide or starting fresh.

```bash
project-guide mode default
```

---

### Planning Modes

The planning sequence builds up the foundational documents for the project: concept → features → tech-spec → stories. Each mode produces a single artifact and points to the next.

#### plan_concept

| Field | Value |
|-|-|
| **Type** | Sequence |
| **Next** | `plan_features` |
| **Artifact** | `docs/specs/concept.md` |
| **Prerequisites** | None |

Define the problem space (problem statement, pain points, target users, value criteria) and the solution space (solution statement, goals, scope, constraints), plus the pain-point-to-solution mapping.

```bash
project-guide mode plan_concept
```

#### plan_features

| Field | Value |
|-|-|
| **Type** | Sequence |
| **Next** | `plan_tech_spec` |
| **Artifact** | `docs/specs/features.md` |
| **Prerequisites** | `concept.md` |

Generate feature requirements — what the project does. Defines functional and presentation requirements without specifying implementation.

```bash
project-guide mode plan_features
```

#### plan_tech_spec

| Field | Value |
|-|-|
| **Type** | Sequence |
| **Next** | `plan_stories` |
| **Artifacts** | `docs/specs/tech-spec.md`, `docs/specs/project-essentials.md` (initial) |
| **Prerequisites** | `concept.md`, `features.md` |

Generate a technical specification — how the project is built. Details architecture, modules, dependencies, and data models, but not actual code.

After the tech-spec is approved, the mode prompts for **project-essentials** content — must-know facts future LLMs need to avoid blunders (workflow rules, tool-wrapper conventions, architecture quirks, hidden coupling, dogfooding notes). If the developer provides facts, `docs/specs/project-essentials.md` is generated from the artifact template. If there are none, the file is deliberately not created (the "skip if none" escape hatch — see the mode template for details).

```bash
project-guide mode plan_tech_spec
```

#### plan_stories

| Field | Value |
|-|-|
| **Type** | Sequence |
| **Next** | `project_scaffold` |
| **Artifact** | `docs/specs/stories.md` |
| **Prerequisites** | `concept.md`, `features.md`, `tech-spec.md` |

Generate user stories. Based on the concept, features, and tech-spec, scaffold the project, determine implementation phases, and break everything down into independently completable stories.

```bash
project-guide mode plan_stories
```

#### plan_phase

| Field | Value |
|-|-|
| **Type** | Sequence |
| **Next** | `code_velocity` |
| **Artifacts** | `docs/specs/new-phase-<name>.md`, `docs/specs/stories.md` (modify), `docs/specs/project-essentials.md` (modify, append-only) |
| **Prerequisites** | `concept.md`, `features.md`, `tech-spec.md`, `stories.md` |

Generate a feature phase prompt for an existing project. Combines mini-concept, features, and technical details to describe a gap to fill, then adds a new phase to the existing stories document.

`plan_phase` handles two `stories.md` shapes: **populated** (existing phases — append after the highest) and **empty post-archive** (header + `## Future` only — read `docs/specs/.archive/stories-vX.Y.Z.md` to find the highest archived phase letter and continue from there). Phase letters continue across the archive boundary.

After the new stories are approved, `plan_phase` runs a terminal step (once per phase, not per-story) that asks whether the phase introduced any new must-know facts — new architecture boundaries, new workflow rules, new hidden coupling — and **appends** them to `docs/specs/project-essentials.md` (or creates it from the artifact template if the project is a legacy migration that hasn't captured essentials yet). The append-only semantics are deliberate: `plan_phase` is not the place to refactor existing project-essentials content — that is `refactor_plan`'s Final Step job.

```bash
project-guide mode plan_phase
```

---

### Post-Release Modes

#### archive_stories

| Field | Value |
|-|-|
| **Type** | Sequence |
| **Next** | `plan_phase` |
| **Artifact** | `docs/specs/stories.md` (`action: archive`) |
| **Prerequisites** | `stories.md` |

Archive the completed `docs/specs/stories.md` so the next phase can start with a clean slate. The current file is moved to `docs/specs/.archive/stories-vX.Y.Z.md` (version derived from the latest story) and a fresh empty `stories.md` is re-rendered from the artifact template, preserving the `## Future` section verbatim.

The mode is conversational (warns about non-`[Done]` stories, shows the planned archive path, awaits approval) but the actual mutation runs through `project-guide archive-stories`, which wraps a deterministic transactional action with rollback on failure.

Run this when all stories in the current phase are `[Done]` and you want each completed phase as a self-contained file in `.archive/` for cleaner planning.

```bash
project-guide mode archive_stories
project-guide archive-stories  # after developer approval
```

---

### Scaffold Mode

#### project_scaffold

| Field | Value |
|-|-|
| **Type** | Sequence |
| **Next** | `code_velocity` |
| **Prerequisites** | `concept.md`, `features.md`, `tech-spec.md`, `stories.md` |

One-time project scaffolding after planning is complete. Creates LICENSE, copyright headers, package manifest, README with badges, CHANGELOG, and `.gitignore` based on decisions made during planning.

```bash
project-guide mode project_scaffold
```

---

### Coding Modes

Coding modes are cycles — you stay in the mode and repeat the workflow per story or task.

#### code_velocity

| Field | Value |
|-|-|
| **Type** | Cycle |
| **Prerequisites** | `stories.md`, `CHANGELOG.md` |

Generate code with velocity. Fast iteration workflow with commit-per-story, version-per-story, and a HITLoop checklist approach. Best for greenfield development where you want to move fast and iterate.

```bash
project-guide mode code_velocity
```

#### code_test_first

| Field | Value |
|-|-|
| **Type** | Cycle |
| **Prerequisites** | `stories.md` |

Generate code with a test-first (TDD) approach. Write a failing test first, then implement code to make it pass, then refactor. Best for code where correctness is critical and tests can capture intent clearly.

```bash
project-guide mode code_test_first
```

#### debug

| Field | Value |
|-|-|
| **Type** | Cycle |
| **Prerequisites** | `stories.md` |

Debug code with a test-first approach. Reproduce the bug, isolate the cause, write a failing test that captures the bug, fix it, and verify the test passes.

```bash
project-guide mode debug
```

---

### Documentation Modes

#### document_brand

| Field | Value |
|-|-|
| **Type** | Sequence |
| **Artifact** | `docs/specs/brand-descriptions.md` |
| **Prerequisites** | `concept.md`, `features.md` |

Define the canonical source of truth for all descriptive language about the project brand. All consumer files (README.md, landing page, package metadata, features.md) should draw from these definitions.

```bash
project-guide mode document_brand
```

#### document_landing

| Field | Value |
|-|-|
| **Type** | Sequence |
| **Artifacts** | `docs/site/index.md`, MkDocs framework |
| **Prerequisites** | `concept.md`, `features.md`, `tech-spec.md`, `stories.md`, `brand-descriptions.md` |

Generate a GitHub landing page and markdown support documentation using MkDocs.

```bash
project-guide mode document_landing
```

---

### Refactoring Modes

Refactoring modes are cycles for updating existing documents — either because of new features or to migrate legacy formats.

#### refactor_plan

| Field | Value |
|-|-|
| **Type** | Cycle |
| **Artifact** | `docs/specs/project-essentials.md` (modify, terminal step) |
| **Prerequisites** | None |

Rewrite or update existing planning documents (concept, features, tech-spec) because of new features or improvements. Can also migrate legacy project-guide planning documents — preserves information while restructuring into standardized sections.

After all document cycles are complete, `refactor_plan` runs a terminal **"Revisit Project Essentials"** step (once per refactor session, not per-document) that asks whether the refactor introduced any new must-know facts with refactor-specific framing: switched or added an environment manager, split runtime from dev environment, renamed module or moved source-of-truth, changed domain conventions, new auto-generated or hidden-coupling files. For legacy projects that have never had a `project-essentials.md`, this is the create path (and is flagged as the highest-value capture moment because none of the conventions have been written down). For existing projects, it's a read-modify-write refresh.

```bash
project-guide mode refactor_plan
```

#### refactor_document

| Field | Value |
|-|-|
| **Type** | Cycle |
| **Prerequisites** | None |

Update existing documentation files (README, brand descriptions, landing page, MkDocs configuration) because of new features or improvements. Can also migrate legacy project-guide documentation.

```bash
project-guide mode refactor_document
```

---

## Mode Flow

### New Project Flow

The typical project lifecycle flows through modes in this order:

```
default
  └─> plan_concept
        └─> plan_features
              └─> plan_tech_spec
                    └─> plan_stories
                          └─> project_scaffold
                                └─> code_velocity (cycle)
```

### Ongoing Project Flow

Once in a coding cycle, switch to specialized modes as needed:

- **`debug`** — when something breaks
- **`code_test_first`** — for critical correctness
- **`archive_stories`** — when all stories in the current phase are `[Done]` and you want a clean slate before planning the next phase
- **`plan_phase`** — when adding a new feature phase (works with both populated and post-archive `stories.md`)
- **`refactor_plan`** / **`refactor_document`** — when planning artifacts or docs need updating
- **`document_brand`** / **`document_landing`** — when preparing for release

## Listing Modes

Run `project-guide mode` (no argument) to see all available modes with the current mode highlighted:

```bash
project-guide mode
```

## Switching Modes

```bash
project-guide mode <mode-name>
```

This re-renders `docs/project-guide/go.md` with the new mode's template. Tell your LLM to re-read the file (most efficient in a fresh chat window) to begin the new workflow.

## Next Steps

- [Commands Reference](commands.md) - Detailed command documentation
- [Workflow Guide](workflow.md) - See modes in action
- [Override Management](overrides.md) - Lock customized mode templates
