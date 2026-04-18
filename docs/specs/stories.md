# stories.md --  (python)

This document breaks the `` project into an ordered sequence of small, independently completable stories grouped into phases. Each story has a checklist of concrete tasks. Stories are organized by phase and reference modules defined in `tech-spec.md`.

Stories with code changes include a version number (e.g., v0.1.0). Stories with only documentation or polish changes omit the version number. The version follows semantic versioning and is bumped per story. Stories are marked with `[Planned]` initially and changed to `[Done]` when completed.

For a high-level concept (why), see `concept.md`. For requirements and behavior (what), see `features.md`. For implementation details (how), see `tech-spec.md`. For project-specific must-know facts, see `project-essentials.md` (`plan_phase` appends new facts per phase).

---

## Phase O: (Theme TBD)

### Story O.a: v2.5.0 Rename project-essentials-pyve.md → pyve-essentials.md and Auto-Render in go.md [Done]

Today `project-essentials-pyve.md` is *merged once* into `docs/specs/project-essentials.md` at scaffold/plan-tech-spec time. Upstream improvements to the bundled pyve rules never reach existing projects — a real drift source. Rename to `pyve-essentials.md` (to signal it is a package-versioned bundled artifact, not a project-owned file) and render it directly in `go.md` behind the `pyve_installed` gate so every `project-guide mode <name>` invocation picks up the latest content automatically.

- [x] Rename `project_guide/templates/project-guide/templates/artifacts/project-essentials-pyve.md` → `pyve-essentials.md`
- [x] In `project_guide/render.py`:
  - [x] Add `_read_pyve_essentials(templates_subdir, pyve_installed)` helper — reads `templates/artifacts/pyve-essentials.md` from the *template tree* (not `spec_artifacts_path`); returns `""` when `pyve_installed=False` or file missing or whitespace-only
  - [x] Pass `pyve_essentials` into the Jinja context in `render_go_project_guide`
- [x] In `project_guide/templates/project-guide/templates/modes/_header-common.md`: add a `{% if pyve_essentials %}` block rendering the pyve content as a `### Pyve Essentials` subsection nested inside the existing `## Project Essentials` wrapper so `###` headings nest correctly
  - [x] Handle the case where `project_essentials` is empty but `pyve_essentials` is non-empty — the `## Project Essentials` wrapper must still render so the `###` subsection has a parent
- [x] Remove the "Merge Pyve Project Essentials" step from `scaffold-project-mode.md` (currently gated on `{% if pyve_installed %}`) — content is now auto-injected
  - [x] Renumber subsequent steps: collapse the `{% if pyve_installed %}9{% else %}8{% endif %}` conditionals back to unconditional numbering
- [x] Remove the "Pyve users" paragraph (the `{% if pyve_installed %}` block) from `plan-tech-spec-mode.md` step 6
- [x] Update `refactor-plan-mode.md` Step F.2 examples: clarify that pyve-specific rules live in the bundled `pyve-essentials.md` and should NOT be duplicated into `project-essentials.md`
- [x] Update `project_guide/templates/project-guide/templates/artifacts/project-essentials.md` comment block: mention `pyve-essentials.md` as a sibling bundled artifact that is auto-rendered (so users understand why pyve rules don't appear in their own file)
- [x] Update `docs/specs/features.md` FR-13: describe auto-render behavior, not one-shot merge
- [x] Update `docs/specs/tech-spec.md`: `render.py` behavior section, context variables table
- [x] Update `docs/specs/project-essentials.md` in this project (dogfooding): remove or shorten the "Workflow rules — pyve environment conventions" and "LLM-internal vs. developer-facing invocation" sections that will now auto-render from `pyve-essentials.md`; leave only project-specific notes that are not duplicated
- [x] Migration note in CHANGELOG: existing downstream projects may have pyve sections merged into their `project-essentials.md` from pre-v2.5.0 scaffold. Duplication is inert (content renders once from each source); users may optionally delete the merged-in pyve sections to defer to the bundled source of truth
- [x] Tests in `tests/test_render.py`:
  - [x] `render_go_project_guide` with `pyve_installed=True` → rendered `go.md` contains pyve-essentials content under a `### Pyve Essentials` subsection
  - [x] `render_go_project_guide` with `pyve_installed=False` → rendered `go.md` contains no pyve-essentials content (even if `pyve-essentials.md` exists in the template tree)
  - [x] Rendered `go.md` with both `project_essentials` and pyve content present has the `## Project Essentials` wrapper containing the `### Pyve Essentials` subsection
  - [x] Rendered `go.md` with empty `project_essentials` but `pyve_installed=True` still renders the `## Project Essentials` wrapper containing `### Pyve Essentials`
  - [x] No test or code references the old `project-essentials-pyve.md` filename
  - [x] Rename/update the existing pyve-artifact tests (currently `tests/test_render.py:1001-1152`) — adjust inclusion-gate test to assert auto-render rather than merge-instruction presence
  - [x] `test_every_mode_renders_successfully` still passes (parametrized)
  - [x] `scaffold_project` rendered output no longer contains "Merge Pyve Project Essentials"
  - [x] `plan_tech_spec` rendered output no longer contains "Pyve users:"
  - [x] `pyve-essentials.md` artifact contains no unrendered `{{ var }}` placeholders (update the existing guard test for the new name)
- [x] Bump `project_guide/version.py`, `pyproject.toml`, and `CHANGELOG.md` to v2.5.0 (Changed + Removed categories)

---

## Future

### Code Mode Hierarchy [Deferred]

- `code_production` mode — blocked on further `code_*` abstraction work; revisit after N.d (`--test-first`) settles the mode-preference pattern.

### Audit Modes [Deferred]

Future modes: `audit_security`, `audit_architecture`, `audit_performance`, `audit_best_practices`, `audit_modularity`, `audit_patterns`.

### Project Lifecycle Automation [Deferred]

- Release helper / version-bump / tag automation — developer works across multiple git flows and prefers tool-agnostic; no timeline.
- Migration tooling for `docs/guides/` → `docs/project-guide/` — future `refactor` mode; low demand.

### Advanced Project Essentials [Deferred]

- `create_or_modify` action type — revisit if multiple artifacts develop the need; not yet justified.
- Validation/linting of `project-essentials.md` content — freeform by design; template convention is sufficient.
- Auto-detection of stale `project-essentials.md` — git-log based; deferred until there is demand.

### CLI Edge Cases [Deferred]

- `--interactive` flag to force interactive mode over non-TTY stdin — not needed; `stdin` can always be re-attached.
- Legacy broken-state detection for `init` (`.project-guide.yml` absent but target dir populated) — unusual edge case; falls through to existing skip-with-warnings path.

### Integrity & Validation [Deferred]

- `project-guide check` command — dedicated integrity/audit surface with nonzero exit on failure, suitable for CI and pre-commit hooks. Candidate rules: `project_name` in config vs. `cwd.name` vs. `pyproject.toml` `[project] name`; artifact headers (`# stories.md -- <name> (<lang>)`) vs. `config.project_name`/`config.programming_language`; `SCHEMA_VERSION` surfacing; `installed_version` vs. `__version__`; `.archive/stories-vX.Y.Z.md` filenames parse cleanly; metadata override keys reference existing modes; unrendered `{{ var }}` placeholders across written artifacts (broadens the N.s `render_fresh_stories_artifact` guard to every written artifact). `project-guide status` runs a cheap subset and prints a one-line footer (`⚠ N integrity issues — run 'project-guide check' for details`) without changing its exit code. Precedent: `django check`, `brew doctor`, `cargo check`. Defer until there is a concrete second integrity rule worth shipping (N.s covers the first drift source inline with a warning).

### Template & Rendering [Deferred]

- Support for literal `{{ var }}` strings in template output — use `{% raw %}...{% endraw %}` on a case-by-case basis; bridge with a general solution only if the pattern becomes common.
