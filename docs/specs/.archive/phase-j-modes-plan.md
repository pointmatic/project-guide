# Phase J Plan: Mode-Driven Template System (v2.0.0)

This document defines the gaps between the current v1.5.x static file-sync system and the new v2.0.0 mode-driven template architecture described in `concept.md` and `project-guide-metadata.yml`. It covers the features, technical changes, and constraints needed to implement Phase J.

---

## What Exists Today (v1.5.x)

**Architecture:** Static markdown files bundled as package data, copied to `docs/guides/` on `init`, version-tracked and synced via `update`.

**CLI commands:** `init`, `update`, `status`, `override`, `unoverride`, `overrides`, `purge`

**Config:** `.project-guide.yml` with `version`, `installed_version`, `target_dir`, `overrides`

**Modules:** `cli.py` (299 lines), `config.py` (Config dataclass + YAML I/O), `sync.py` (copy/compare/backup), `exceptions.py`, `version.py`

**Templates:** Static `.md` files in `project_guide/templates/guides/` (old, now removed) and a partially restructured `project_guide/templates/project-guide/` directory with mode templates, artifact templates, header partials, and metadata.yml.

**Dependencies:** `click`, `pyyaml`, `packaging`

---

## What v2.0.0 Needs

### Feature 1: Jinja2 Template Rendering

The core architectural change. `go-project-guide.md` is no longer a static file — it is dynamically rendered from mode templates, header partials, and metadata variables using Jinja2.

**What changes:**
- New runtime dependency: `jinja2>=3.1`
- New module: `render.py` — loads metadata.yml, resolves `{{variable}}` references in metadata, renders mode templates with Jinja2
- Template inclusion: mode templates use `{% include %}` (or a custom `{{template "path"}}` directive) to pull in `_header-common.md`, `_header-sequence.md` / `_header-cycle.md`
- The rendered output is written to the project's `go-project-guide.md` path (a build artifact, not committed to git)

**Constraints:**
- Jinja2 `{{ }}` delimiters conflict with the artifact template convention (e.g., `{{problem_statement}}` in `concept.md`). Artifact templates are LLM instruction placeholders, not Jinja2 variables. The renderer must only process mode templates and the go-project-guide entry point — not artifact templates.
- The `{{template "path"}}` syntax currently in mode templates needs to be converted to Jinja2 `{% include %}` or handled by a pre-processing step.

### Feature 2: Metadata Parser

`project-guide-metadata.yml` is the business logic configuration. It defines all modes, their templates, artifacts, prerequisites, and shared variables.

**What changes:**
- New module: `metadata.py` — loads and validates `project-guide-metadata.yml`
- Two-pass variable resolution: the `common` block defines variables (e.g., `mode_templates_path`, `spec_artifacts_path`), and all other fields containing `{{var}}` are resolved against those variables
- Mode lookup by name returns: mode template path, sequence/cycle type, next_mode, artifact paths, prerequisite file list
- The metadata file is bundled in the package and copied to the project on `init`

**Data model:**
- `ModeDefinition`: name, info, description, sequence_or_cycle, generation_type, mode_template, next_mode (optional), artifacts (list), files_exist (list)
- `Metadata`: common (dict), modes (list of ModeDefinition)

### Feature 3: `mode` Command

The primary new CLI command. Sets the active development mode, renders `go-project-guide.md`, and prints status.

**What changes:**
- New CLI command: `project-guide mode [MODE_NAME]`
- With argument: validates mode name against metadata, updates `current_mode` in `.project-guide.yml`, renders `go-project-guide.md`, prints confirmation
- Without argument: prints current mode and available modes list
- Prerequisite checking: before activating a mode, verify `files_exist` entries exist on disk. If prerequisites are missing, warn the user (not a hard error — the user may be intentionally skipping ahead)
- Mode names are the `name` field from metadata.yml (e.g., `plan_concept`, `code_velocity`)

### Feature 4: Config Schema Update

`.project-guide.yml` needs new fields to support modes.

**What changes:**
- New field: `current_mode: str` — the active mode name (default: `default`)
- New field: `target_dir` changes from `docs/guides` to `docs/project-guide` 
- Config schema version bumps from `"1.0"` to `"2.0"`
- Migration: existing v1.0 configs get `current_mode: "default"` added on load, `target_dir` is preserved as-is (user decides when to restructure)

### Feature 5: Template Directory Restructuring

The template layout in the package and in target projects changes to support the mode system.

**What changes:**
- **Package templates** (`project_guide/templates/project-guide/`): already partially restructured. Contains `go-project-guide.md` (entry point template), `project-guide-metadata.yml`, `templates/modes/` (mode templates + header partials), `templates/artifacts/` (artifact templates).
- **Project target directory** changes from `docs/guides/` to `docs/project-guide/`. On `init`, the following structure is created:

```
docs/project-guide/
  go-project-guide.md          # rendered (gitignored)
  project-guide-metadata.yml   # copied, user-editable
  templates/
    modes/                     # mode instruction templates
      _header-common.md
      _header-sequence.md
      _header-cycle.md
      plan-concept-mode.md
      plan-features-mode.md
      ... (all mode templates)
    artifacts/                 # artifact format templates
      concept.md
      ... (future artifact templates)
  developer/                   # supplementary guides (static)
    codecov-setup-guide.md
    production-mode.md
```

- The old `docs/guides/` content (static guides like `best-practices-guide.md`, `debug-guide.md`) is absorbed into mode templates and the `go-project-guide.md` entry point. These files are no longer distributed as standalone files.
- `go-project-guide.md` should be added to `.gitignore` (it is a rendered artifact)

### Feature 6: Updated `init` Command

`init` needs to set up the new directory structure and render the initial `go-project-guide.md`.

**What changes:**
- Creates `docs/project-guide/` structure (templates/modes/, templates/artifacts/, developer/)
- Copies all mode templates, artifact templates, header partials, metadata.yml, and developer guides
- Renders `go-project-guide.md` in `default` mode
- Creates `.project-guide.yml` with `current_mode: "default"` and `target_dir: "docs/project-guide"`
- Adds `go-project-guide.md` to `.gitignore` if not already present

### Feature 7: Updated `update` and `sync` Commands

The sync/override model continues to work but operates on the new template files.

**What changes:**
- Guide discovery (`get_all_guide_names()` in `sync.py`) scans the new directory structure: `templates/modes/*.md`, `templates/artifacts/*.md`, `developer/*.md`, `project-guide-metadata.yml`
- Override/unoverride work on any of these files (e.g., `override templates/modes/code-velocity-mode.md "Custom velocity workflow"`)
- After any `update` that touches mode templates, re-render `go-project-guide.md` for the current mode
- `status` shows the current mode alongside the existing guide sync status

### Feature 8: Updated `status` Command

Status reflects the mode system.

**What changes:**
- Displays current mode name and description (from metadata)
- Shows `go-project-guide.md` render status (stale if templates changed since last render)
- Continues to show guide sync status (version, overrides) for all template files
- Shows prerequisite status for the current mode (which `files_exist` entries are present/missing)

### Feature 9: Foundation Mode Templates

All 11 foundation mode templates need to be complete and functional. Each must include the appropriate header partial and produce useful LLM instructions.

**Modes:**
| Mode | Type | Template | Next Mode |
|------|------|----------|-----------|
| `default` | — | `default-mode.md` | — |
| `plan_concept` | sequence | `plan-concept-mode.md` | `plan_features` |
| `plan_features` | sequence | `plan-features-mode.md` | `plan_tech_spec` |
| `plan_tech_spec` | sequence | `plan-tech-spec-mode.md` | `plan_stories` |
| `plan_stories` | sequence | `plan-stories-mode.md` | `code_velocity` (default) |
| `plan_phase` | sequence | `plan-phase-mode.md` | `code_velocity` (default) |
| `code_velocity` | cycle | `code-velocity-mode.md` | — |
| `code_test_first` | cycle | `code-test-first-mode.md` | — |
| `debug` | cycle | `debug-mode.md` | — |
| `document_brand` | sequence | `brand-mode.md` | — |
| `document_landing` | sequence | `document-mode.md` | — |

**Template requirements:**
- Each mode template must include one of `_header-sequence.md` or `_header-cycle.md`
- Each mode template must be self-contained: an LLM reading the rendered `go-project-guide.md` has everything needed for that mode
- Mode templates reference artifact templates by path so the LLM knows what format to produce
- `_header-common.md` is included in all rendered output via `go-project-guide.md` (not per-mode template)

### Feature 10: Existing Content Migration

The large monolithic `go-project-guide.md` entry point template currently contains Steps 0-4 (License, Features, Tech Spec, Stories, Implementation) plus debugging instructions. This content needs to be distributed into the appropriate mode templates.

**Migration mapping:**
| Current content | Target mode template |
|----------------|---------------------|
| Step 0: Project Setup (License, Headers, Badges, CHANGELOG) | `_header-common.md` or `default-mode.md` |
| Step 1: Features Document | `plan-features-mode.md` |
| Step 2: Technical Specification | `plan-tech-spec-mode.md` |
| Step 3: Stories Document | `plan-stories-mode.md` |
| Step 4: Implementation | `code-velocity-mode.md` / `code-test-first-mode.md` |
| Debugging and Maintenance | `debug-mode.md` |
| `best-practices-guide.md` | Distributed across relevant mode templates |

---

## Technical Constraints

1. **Jinja2 vs artifact placeholders**: Artifact templates use `{{variable}}` as LLM instructions, not Jinja2 variables. The renderer must only process mode templates and `go-project-guide.md`, never artifact templates.

2. **Metadata variable resolution**: `project-guide-metadata.yml` uses `{{var}}` for internal variable substitution (e.g., `{{mode_templates_path}}`). This is a separate pre-processing step from Jinja2 rendering — resolve metadata variables first, then pass resolved paths to Jinja2.

3. **Backward compatibility**: `init` on a project with existing `docs/guides/` should not break. The old directory is left alone. Users migrate manually or via a future `refactor` mode.

4. **Template customization**: Users can modify any template in `docs/project-guide/templates/` and protect it via `override`. The `update` command respects overrides on the new template files just as it did on the old static guides.

5. **Cross-platform symlinks**: The old Phase J plan used symlinks for `project-guide.md`. The new approach renders a real file, avoiding Windows symlink permission issues.

6. **`.gitignore` management**: `go-project-guide.md` is generated and should not be committed. `init` should add it to `.gitignore`.

---

## Implementation Strategy: Spike First

Following the project's own best-practices guide ("Spike Early, Spike Often"), Phase J is structured as a spike-first implementation:

**Spike scope:** Wire the full stack end-to-end with only two modes: `default` and `plan_concept`. The `plan_concept` templates are already hand-drafted and closest to ready. This validates:
- Metadata parsing and variable resolution
- Jinja2 rendering pipeline (entry point + mode template + header partial)
- `mode` command setting the active mode and rendering output
- Config schema v2.0 with `current_mode`
- New directory structure (`docs/project-guide/`)
- Updated `init` creating the new structure

**After the spike passes:** Add remaining foundation mode templates and update `sync`/`update`/`status` to work with the new structure. Each subsequent story adds modes incrementally, not all at once.

**What the spike defers:**
- All mode templates except `default` and `plan_concept`
- Updated `sync`/`update` for new directory structure
- Updated `status` with mode-aware output
- Content migration from the monolithic `go-project-guide.md`

---

## Out of Scope for Phase J

These were added to the end of the `stories.md` file as future feature ideas. 

- Mode auto-detection from `files_exist` prerequisites (future advanced feature)
- Interactive mode menu (deferred — direct `mode <name>` argument is sufficient for v2.0.0)
- LLM API calls for artifact generation (future — currently the LLM fills in variables conversationally)
- Per-project metadata overrides in `.project-guide.yml` (future — metadata.yml is the single source for now)
- Migration tooling for `docs/guides/` → `docs/project-guide/` (future `refactor` mode)
- Story detection in `status` command (nice-to-have, can be added in a follow-up phase)
- Future modes: `code_production`, `audit_*`, `refactor_*`

---

## Dependency Changes

| Dependency | Current | v2.0.0 |
|-----------|---------|--------|
| `jinja2` | dev only (via mkdocs) | **runtime** `>=3.1` |
| `click` | `>=8.1` | unchanged |
| `pyyaml` | `>=6.0` | unchanged |
| `packaging` | `>=24.0` | unchanged |

---

## Summary of New/Changed Modules

| Module | Status | Purpose |
|--------|--------|---------|
| `render.py` | **new** | Jinja2 template rendering, go-project-guide.md generation |
| `metadata.py` | **new** | Parse and validate project-guide-metadata.yml, resolve variables |
| `cli.py` | modified | Add `mode` command, update `init`/`status`/`update` |
| `config.py` | modified | Add `current_mode` field, schema v2.0 migration |
| `sync.py` | modified | Update guide discovery for new directory structure |
| `exceptions.py` | modified | Add `MetadataError`, `RenderError` |
| `version.py` | modified | Bump to `2.0.0` |
