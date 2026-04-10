# Default Mode -- Getting Started

This is the default mode for new projects. It provides an overview of the full project lifecycle. For focused work, switch to a specific mode with `project-guide mode <name>`.

---

## Project Lifecycle

| Step | Mode | What it does |
|------|------|-------------|
| 1 | `plan_concept` | Define the problem and solution space |
| 2 | `plan_features` | Define requirements, inputs, outputs, behavior |
| 3 | `plan_tech_spec` | Define architecture, modules, dependencies |
| 4 | `plan_stories` | Break into phases and stories with checklists |
| 5 | `project_scaffold` | Scaffold LICENSE, headers, manifest, README, CHANGELOG, .gitignore |
| 6 | `code_velocity` | Implement stories with fast iteration |

## Get Started

To begin a new project, run:

```bash
project-guide mode plan_concept
```

## All Available Modes

### Planning (sequence)
| Mode | Command | Output |
|------|---------|--------|
| **Concept** | `project-guide mode plan_concept` | `docs/specs/concept.md` |
| **Features** | `project-guide mode plan_features` | `docs/specs/features.md` |
| **Tech Spec** | `project-guide mode plan_tech_spec` | `docs/specs/tech-spec.md` |
| **Stories** | `project-guide mode plan_stories` | `docs/specs/stories.md` |
| **Phase** | `project-guide mode plan_phase` | Add a new phase to an existing project |

### Scaffold (sequence)
| Mode | Command | Purpose |
|------|---------|---------|
| **Project Scaffold** | `project-guide mode project_scaffold` | One-time project scaffolding |

### Coding (cycle)
| Mode | Command | Workflow |
|------|---------|----------|
| **Velocity** | `project-guide mode code_velocity` | Direct commits, fast iteration |
| **Test-First** | `project-guide mode code_test_first` | TDD red-green-refactor cycle |
| **Debug** | `project-guide mode debug` | Test-driven debugging |

### Documentation (sequence)
| Mode | Command | Output |
|------|---------|--------|
| **Branding** | `project-guide mode document_brand` | `docs/specs/brand-descriptions.md` |
| **Landing Page** | `project-guide mode document_landing` | GitHub Pages + MkDocs docs |
