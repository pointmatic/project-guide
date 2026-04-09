# tech-spec.md -- {{ project_name }}

Define **how** the project is built -- architecture, module layout, dependencies, data models, API signatures, and cross-cutting concerns.

The high-level concept (why) should be captured in `concept.md`. The requirements and behavior (what) should be captured in `features.md`. The breakdown of this implementation plan (step-by-step tasks) should be written in `stories.md`.

{% include "modes/_header-sequence.md" %}

## Prerequisites

Before starting, the developer must provide (or the LLM must ask for):

1. **Language / runtime** -- e.g. Python 3.14, Node 22, Go 1.23, etc.
2. **Preferred frameworks, libraries, or tools** (if any)

The approved `docs/specs/concept.md` and `docs/specs/features.md` must exist before starting this mode.

## Steps

1. Read `docs/specs/features.md` to understand the requirements.

2. Gather additional technical details from the developer (ask questions if needed):
   - runtime_and_tooling: Language version, package manager, linter, test runner, type checker
   - dependencies: Runtime, optional, system, and development dependencies with purpose for each
   - package_structure: Full directory tree with one-line descriptions per file
   - filename_conventions: Naming rules for different file types (see guidelines below)
   - key_components: For each major module -- function signatures, behavior, edge cases handled
   - data_models: Full model definitions with field types and defaults
   - configuration: Settings model with all fields, types, defaults, and precedence rules
   - cli_design: Subcommands table, shared flags, exit codes (if applicable)
   - library_api: Public API with usage examples (if applicable)
   - cross_cutting: Retry strategy, rate limiting, logging, caching, atomic writes, etc.
   - performance_implementation: Concurrency model, connection pooling, batching strategy, resource limits (if applicable)
   - testing_strategy: Unit tests, integration tests, and what each covers
   - packaging_and_distribution: Package metadata, registry (PyPI/npm/crates.io), installation methods, console scripts, package data inclusion (if applicable)

3. Generate `docs/specs/tech-spec.md` using the artifact template at `templates/artifacts/tech-spec.md`

4. Present the complete document to the developer for approval. Iterate as needed.

**Note:** Adapt sections to fit the project type:
- **Web apps**: Add routing, database schema, API endpoints, deployment
- **Mobile apps**: Add screen navigation, platform APIs, build targets
- **Data pipelines**: Add data models, transformations, scheduling
- **Bash utilities**: May only need sections 1-6; skip data models and API design

## Filename Convention Guidelines

Include a **Filename Conventions** section in the tech spec:

| File Type | Convention | Examples |
|-----------|------------|----------|
| **Documentation** (Markdown) | Hyphens | `getting-started.md`, `api-reference.md` |
| **Workflow files** | Hyphens | `deploy-docs.yml`, `run-tests.yml` |
| **Python modules** | Underscores (PEP 8) | `my_module.py`, `data_processor.py` |
| **Python packages** | Underscores (PEP 8) | `my_package/`, `utils/` |
| **JavaScript/TypeScript** | Hyphens or camelCase | `api-client.ts`, `dataProcessor.ts` |
| **Configuration files** | Hyphens or dots | `mkdocs.yml`, `.gitignore`, `pyproject.toml` |
