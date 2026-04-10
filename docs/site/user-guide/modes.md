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
| **Artifact** | `docs/specs/tech-spec.md` |
| **Prerequisites** | `concept.md`, `features.md` |

Generate a technical specification — how the project is built. Details architecture, modules, dependencies, and data models, but not actual code.

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
| **Artifacts** | `docs/specs/new-phase-<name>.md`, `docs/specs/stories.md` (modify) |
| **Prerequisites** | `concept.md`, `features.md`, `tech-spec.md`, `stories.md` |

Generate a feature phase prompt for an existing project. Combines mini-concept, features, and technical details to describe a gap to fill, then adds a new phase to the existing stories document.

```bash
project-guide mode plan_phase
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
| **Prerequisites** | None |

Rewrite or update existing planning documents (concept, features, tech-spec) because of new features or improvements. Can also migrate legacy project-guide planning documents — preserves information while restructuring into standardized sections.

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
- **`plan_phase`** — when adding a new feature phase
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
