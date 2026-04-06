# stories.md — project-guide (Python)

This document breaks the `project-guide` project into an ordered sequence of small, independently completable stories grouped into phases. Each story has a checklist of concrete tasks. Stories are organized by phase and reference modules defined in `tech-spec.md`.

Stories with code changes include a version number (e.g., v0.1.0). Stories with only documentation or polish changes omit the version number. The version follows semantic versioning and is bumped per story. Stories are marked with `[Planned]` initially and changed to `[Done]` when completed.

---

## Phase I: Rename and Publish Package

Rename the package from `project-guides` to `project-guide` (singular). The goals are: reserve the PyPI name immediately with a minimal publish, then progressively clean up the codebase over subsequent stories. The old `project-guides` CLI entry point is kept alive through Story I.c to avoid breaking existing users mid-rename.

### Story I.a: v1.4.0 Reserve PyPI Name [Done]

Publish the package under the new name `project-guide` on PyPI. This is the minimal change needed to secure the name. The old `project-guides` CLI command continues to work — no regressions for existing users.

- [x] Update `pyproject.toml`
  - [x] Change `name` from `"project-guides"` to `"project-guide"`
  - [x] Add `project-guide = "project_guides.cli:main"` entry point alongside existing `project-guides`
  - [x] Bump version to `1.4.0`
  - [ ] Update description if needed
- [x] Update `project_guides/version.py` to `"1.4.0"`
- [x] Update `CHANGELOG.md` with v1.4.0 entry
- [x] Publish to PyPI via GitHub Actions
  - [x] Commit and push changes
  - [x] Create and publish a GitHub Release tagged `v1.4.0`
  - [x] Confirm the `Publish to PyPI` Actions workflow passes
- [x] Verify: `pip install project-guide` installs successfully
- [x] Verify: both `project-guide --help` and `project-guides --help` work

### Story I.b: v1.4.1 Rename Config File [Done]

Rename `.project-guides.yml` to `.project-guide.yml` everywhere: the template, all code references, and all documentation. Add a one-time migration so existing users' config files are renamed automatically with a printed notice.

- [x] Rename template file
  - [x] `project_guides/templates/.project-guides.yml.template` → `.project-guide.yml.template`
- [x] Update `config.py`
  - [x] Change the config filename constant from `.project-guides.yml` to `.project-guide.yml`
- [x] Update `cli.py`
  - [x] Add migration logic in the `main` group or a shared helper: if `.project-guides.yml` exists and `.project-guide.yml` does not, rename it and print: `"Renamed .project-guides.yml → .project-guide.yml"`
  - [x] Update all string references to the old config filename
- [x] Update `sync.py` references if any
- [x] Update `tests/` — all fixtures and assertions using the old filename
- [x] Update `README.md` and all guide docs referencing `.project-guides.yml`
- [x] Bump `version.py` and `pyproject.toml` to `1.4.1`
- [x] Update `CHANGELOG.md`
- [x] Verify: existing project with `.project-guides.yml` runs any command and gets renamed automatically
- [x] Verify: new `project-guide init` creates `.project-guide.yml`

### Story I.c: v1.5.0 Complete CLI Rename [In Progress]

Remove the old `project-guides` CLI entry point. Update all user-facing strings, documentation, and guide content to use `project-guide`. This is the breaking change — old users must reinstall.

- [x] Update `pyproject.toml`
  - [x] Remove `project-guides = "project_guides.cli:main"` entry point
  - [x] Bump version to `1.5.0`
- [x] Update `project_guides/version.py` to `"1.5.0"`
- [x] Update all CLI help strings in `cli.py` (e.g., `"Run project-guides init"` → `"Run project-guide init"`)
- [x] Update `README.md` — all command examples
- [x] Update all files under `project_guards/templates/guides/` that reference `project-guides`
  - [x] `project-guide.md` (How to Use section)
  - [x] Any other guide referencing the CLI command
- [x] Update `CHANGELOG.md`
- [x] Build and publish to PyPI
- [x] Verify: `project-guides --help` is no longer available after reinstall
- [x] Verify: `project-guide --help` works and shows correct command name

### Story I.d: v1.5.1 Rename Python Module Directory [In Progress]

Rename the Python package directory from `project_guides/` to `project_guide/` so the module name matches the package and CLI command. This is a purely internal refactor with no user-visible behavior change.

- [x] Rename directory: `project_guides/` → `project_guide/`
- [x] Update `pyproject.toml`
  - [x] `packages = ["project_guides"]` → `["project_guide"]`
  - [x] `project-guide = "project_guides.cli:main"` → `"project_guide.cli:main"`
- [x] Update all internal imports across `project_guide/*.py`
  - [x] `cli.py` — `from project_guides.xxx import`
  - [x] `sync.py` — `from project_guides.xxx import` and `importlib.resources.files("project_guides.templates...")` strings
  - [x] `config.py`, `exceptions.py`, `__init__.py`, `__main__.py`
- [x] Update all test imports: `from project_guides.xxx import` → `from project_guide.xxx import`
- [x] Update `.github/workflows/`
  - [x] `--cov=project_guides` → `--cov=project_guide` in `ci.yml`, `test.yml`, `publish.yml`
  - [x] `mypy project_guides/` → `mypy project_guide/` in `publish.yml`
- [x] Bump `version.py` and `pyproject.toml` to `1.5.1`
- [x] Update `CHANGELOG.md`
- [x] Run full test suite — all 59 tests must pass
- [x] Verify: `pyve run project-guide status` works correctly after reinstall

### Story I.e: GitHub Repo Rename and PyPI Archive [Planned]

Admin tasks with no code changes. No version bump.

- [x] Rename GitHub repo from `project-guides` to `project-guide`
  - [x] Settings → Repository name → `project-guide`
  - [x] GitHub automatically redirects old URLs
- [x] Update all hardcoded GitHub URLs in the codebase and docs
  - [x] `README.md` badges and links
  - [x] `pyproject.toml` `[project.urls]` section
  - [x] Any guide files referencing the repo URL
- [x] Archive old `project-guides` PyPI package
  - [x] Publish a final `project-guides` release with updated README/description: "This package has moved to `project-guide`. Please update your dependencies."
  - [x] Go to PyPI → `project-guides` → Settings → Archive project
- [x] Update `mkdocs.yml` site URL if applicable
- [x] Verify: all links resolve correctly

### Story I.f: Update README, landing page, and descriptions [Planned]
- [x] Update `docs/specs/descriptions.md` to reflect new package name and concepts (guides -> guide/prompts)
- [x] Update `README.md` based on `docs/specs/description.md`
- [x] Update landing page based on `docs/specs/description.md`
- [x] Add Codecov badge to `README.md` and set minimum coverage to 75%

---

## Phase J: Support Modes

Add a `development_mode` system: a `mode` CLI command sets the active mode in `.project-guide.yml`, and creates a `project-guide.md` symlink in `docs/guides/` pointing to the relevant focused guide for that mode. The LLM always reads the same path (`docs/guides/project-guide.md`) regardless of mode.

Foundation modes (implemented this phase): `plan_concept`, `plan_features`, `plan_tech_spec`, `plan_stories`, `code_velocity`, `code_test_first`, `debug`.

Future modes (deferred): `code_production`, `audit_security`, `audit_architecture`, `audit_performance`, `audit_best_practices`, `audit_modularity`, `audit_patterns`, `refactor`.

### Story J.a: v1.6.0 Add Mode Config Fields [Planned]

Extend `.project-guide.yml` with `development_mode` and `cli_menu` fields. Update the `Config` dataclass and the `status` command to display the current mode.

- [ ] Update `project_guides/templates/.project-guide.yml.template`
  - [ ] Add `development_mode: "plan_concept"`
  - [ ] Add `cli_menu: "compact"`
- [ ] Update `Config` dataclass in `config.py`
  - [ ] Add `development_mode: str = "plan_concept"`
  - [ ] Add `cli_menu: str = "compact"` (valid values: `"compact"`, `"expanded"`, `"none"`)
  - [ ] Ensure new fields serialize/deserialize correctly with existing YAML logic
- [ ] Update `status` command in `cli.py` to print current mode (e.g., `Mode: plan_concept`)
- [ ] Update config migration logic (Story I.b) to write defaults for new fields when absent
- [ ] Update `test_config.py` for new fields
- [ ] Update `test_cli.py` for updated `status` output
- [ ] Bump `version.py` and `pyproject.toml` to `1.6.0`
- [ ] Update `CHANGELOG.md`
- [ ] Verify: `project-guide status` shows `Mode: plan_concept`
- [ ] Verify: old configs missing the new fields load without error (defaults apply)

### Story J.b: v1.6.1 Create Foundation Mode Guide Files [Planned]

Write the focused, context-efficient guide files for each foundation mode. These live at `project_guides/templates/guides/modes/` and are installed into `docs/guides/modes/` in the target project.

- [ ] Create `project_guides/templates/guides/modes/` directory
- [ ] Write guide file for each foundation mode (see content notes below)
  - [ ] `plan-concept.md` — guide for initial concept/ideation: what to ask, how to document `docs/specs/concept.md`, when done
  - [ ] `plan-features.md` — guide for writing `docs/specs/features.md`: required sections, approval gate
  - [ ] `plan-tech-spec.md` — guide for writing `docs/specs/tech-spec.md`: required sections, filename conventions, approval gate
  - [ ] `plan-stories.md` — guide for writing `docs/specs/stories.md`: phase structure, story format, CI/CD question, approval gate
  - [ ] `code-velocity.md` — guide for velocity coding: commit to main, version-per-story, HITLoop, checklist workflow
  - [ ] `code-test-first.md` — guide for TDD workflow: failing test first, red-green-refactor, test naming conventions
  - [ ] `debug.md` — guide for debugging: reproduce → isolate → failing test → fix → verify
- [ ] Each guide file must be self-contained: a fresh LLM reading it has everything needed for that mode
- [ ] Each guide file must be concise: ruthlessly exclude anything not relevant to that mode
- [ ] Update `sync.py` guide discovery to include `modes/` subdirectory files
- [ ] Bump `version.py` and `pyproject.toml` to `1.6.1`
- [ ] Update `CHANGELOG.md`
- [ ] Verify: `project-guide update` installs mode guides into `docs/guides/modes/`

### Story J.c: v1.6.2 Add `mode` Command (Direct Arg) [Planned]

Add `project-guide mode <arg>` to set the active mode. Accepts full mode names (`code_velocity`) and abbreviated key sequences (`cv`). Updates the config and recreates the `docs/guides/project-guide.md` symlink.

- [ ] Add `mode` command to `cli.py`
  - [ ] `@main.command()` with optional `arg` parameter
  - [ ] Define the mode registry: dict mapping full names and abbreviations to guide filenames
    ```python
    MODES = {
        "plan_concept":    ("pc", "modes/plan-concept.md"),
        "plan_features":   ("pf", "modes/plan-features.md"),
        "plan_tech_spec":  ("pt", "modes/plan-tech-spec.md"),
        "plan_stories":    ("ps", "modes/plan-stories.md"),
        "code_velocity":   ("cv", "modes/code-velocity.md"),
        "code_test_first": ("ct", "modes/code-test-first.md"),
        "debug":           ("b",  "modes/debug.md"),
    }
    ```
  - [ ] Resolve arg: try full name first, then abbreviation; error with list of valid values if unrecognized
  - [ ] Update `development_mode` in `.project-guide.yml`
  - [ ] Create or update symlink: `<target_dir>/project-guide.md` → `modes/<guide-file>.md` (relative symlink)
  - [ ] Print confirmation: `"Mode set: code_velocity\nGuide: docs/guides/project-guide.md → modes/code-velocity.md"`
  - [ ] If `cli_menu: "none"` and no arg provided, print error: `"No mode specified. Run with a mode name or abbreviation."`
- [ ] Add `project-guide.md` to `.gitignore` template (it is a generated symlink, not source)
- [ ] Update `test_cli.py` for all `mode` command cases
- [ ] Bump `version.py` and `pyproject.toml` to `1.6.2`
- [ ] Update `CHANGELOG.md`
- [ ] Verify: `project-guide mode cv` sets mode and creates symlink
- [ ] Verify: `project-guide mode code_velocity` has identical effect
- [ ] Verify: `project-guide mode xyz` prints error with valid options
- [ ] Verify: symlink target is relative (not absolute path)

### Story J.d: v1.6.3 Add Interactive Mode Menu [Planned]

When `project-guide mode` is called with no argument and `cli_menu` is not `"none"`, display an interactive two-level menu. Supports `compact` and `expanded` styles.

- [ ] Implement interactive menu in `cli.py` (or extract to `menu.py`)
  - [ ] Menu tree structure (leaf modes bold, parent nodes marked `→`)
    ```
    Top level:  [p]lan →  [c]ode →  [b]debug
    Plan:       [c]oncept  [f]eatures  [t]ech spec  [s]tories
    Code:       [v]elocity  [t]est first
    ```
  - [ ] `compact` style — single line per level:
    ```
    Select a mode: [[p]lan → [c]ode → [b]debug]
    ```
  - [ ] `expanded` style — one option per line with description:
    ```
    Select a mode:
      [p] Plan       →
      [c] Code       →
      [b] Debug
    ```
  - [ ] Read single keypress (no Enter required) using `sys.stdin` raw mode or `click.getchar()`
  - [ ] Single-char input for leaf modes (`b` → sets `debug` immediately)
  - [ ] Two-char input for two-level modes (`p` → show Plan submenu → `f` → sets `plan_features`)
  - [ ] Invalid key at any level reprints the menu
  - [ ] `Ctrl-C` / `Escape` exits without changing mode
- [ ] Update `test_cli.py` — mock `click.getchar()` for menu navigation tests
- [ ] Bump `version.py` and `pyproject.toml` to `1.6.3`
- [ ] Update `CHANGELOG.md`
- [ ] Verify: `project-guide mode` (no arg, compact) shows single-line menu
- [ ] Verify: `project-guide mode` (no arg, expanded) shows multi-line menu
- [ ] Verify: navigating `p` → `f` sets `plan_features` and creates correct symlink
- [ ] Verify: `cli_menu: none` with no arg prints error, no menu shown

### Story J.e: v1.6.4 Enhance `status` with Current Story [Planned]

Extend `project-guide status` to search `stories.md` for in-progress and next planned stories, giving the LLM (and developer) immediate orientation.

- [ ] Add story detection logic to `cli.py` or extract to `stories.py`
  - [ ] Look for `stories.md` at `docs/specs/stories.md` (relative to project root)
  - [ ] Scan for stories marked `[In Progress]` — print each one found
  - [ ] Scan for first story marked `[Planned]` — print as "Next"
  - [ ] If `stories.md` not found, silently skip (no error)
  - [ ] Story line format to match: `### Story <ID>: <optional-version> <Title> [In Progress]`
- [ ] Update `status` output format:
  ```
  Mode:        code_velocity
  Guide:       docs/guides/project-guide.md → modes/code-velocity.md
  In Progress: Story J.d: v1.6.3 Add Interactive Mode Menu
  Next:        Story J.e: v1.6.4 Enhance status with Current Story
  ```
- [ ] Update `test_cli.py` with fixture `stories.md` files covering: no file, no in-progress, one in-progress, multiple in-progress
- [ ] Bump `version.py` and `pyproject.toml` to `1.6.4`
- [ ] Update `CHANGELOG.md`
- [ ] Verify: `project-guide status` in a project with `stories.md` shows correct stories
- [ ] Verify: `project-guide status` in a project without `stories.md` shows no error
