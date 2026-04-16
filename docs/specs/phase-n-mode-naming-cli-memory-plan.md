# phase-n-mode-naming-cli-memory-plan.md — project-guide (Python)

Phase N plan: Mode Naming, CLI Polish & Memory Integration (v2.4.0).

This phase clears the accumulated deferred backlog from Phases J–M, organized into four clusters: (1) mode naming coherence, (2) CLI polish and maturity, (3) advanced mode system features, and (4) memory and knowledge management integration. No single cluster requires a spike — all integration boundaries are well-understood extensions of existing patterns.

**Implementation strategy:** Do renames first (N.a–N.b) since subsequent stories reference the new names. Then CLI improvements (N.c–N.g, mutually independent). Then advanced mode system (N.h–N.i). Then memory integration (N.j–N.l). Documentation pass last (N.m).

---

## Gap Analysis

### Mode Naming Inconsistency

`code_velocity` does not pair naturally with `code_test_first` — "velocity" implies speed rather than workflow style. `code_direct` more clearly describes the mode (direct coding, no mandatory TDD). Similarly, `project_scaffold` is the only mode name that does not start with a verb; every other mode follows a `<verb>_<noun>` convention. Both names have been deferred from Phase J pending more urgent work.

### Missing Code Mode Preference

There is no way to express a project-level preference for test-driven coding. Modes that suggest a next coding step (`default`, `plan_stories`, etc.) always suggest `code_direct`. A `--test-first` flag on `init` would persist this preference so the planning workflow adapts automatically.

### CLI Gaps Deferred from Phase L

Phase L landed `--no-input` for `init` only. `purge` and `update` still block on stdin in unattended contexts. There is no `--quiet` flag to suppress `_copy_template_tree` chatter. There is no config-file fallback for prompt values (the resolution chain: CLI flag → env var → `.project-guide.yml` key → default was documented in Phase L but not implemented). `status` reports file sync state but nothing about the stories backlog.

### Mode Discovery Is Opaque

`project-guide mode` without an argument currently lists available modes as plain text. There is no way to see which modes' prerequisites are already satisfied, and there is no interactive selection interface. Developers must read the docs to know which mode fits their current project state.

### Per-Project Mode Customization Not Possible

All projects use the bundled `.metadata.yml` with no way to override `next_mode`, `files_exist` prerequisites, or other fields for project-specific workflows. This blocks certain advanced use cases (e.g., a project that always wants `code_test_first` as the next step after `plan_stories`).

### Pyve Workflow Rules Must Be Written From Scratch

Every project using `pyve` for environment management must manually write the same two-environment workflow rules into `project-essentials.md`. A bundled `project-essentials-pyve.md` template would let the LLM populate these rules automatically when Pyve is detected, and the template can improve across releases independently of per-project content.

### LLM Memory and project-essentials.md Are Disconnected

The LLM's own memory system (e.g., `.claude/` per-project memories) and `project-essentials.md` serve overlapping purposes but are never reconciled. The LLM may record project-relevant facts to memory that should be in `project-essentials.md`, or vice versa. `scaffold_project` is the natural entry point for a one-time memory review. No mode currently instructs the LLM to reflect on whether a fact belongs in memory vs. `project-essentials.md` before recording it.

---

## Feature Requirements

### N1: Rename `code_velocity` → `code_direct`

Rename everywhere: mode template file (`code-direct-mode.md`), `.metadata.yml` key, all cross-references in other templates (`default-mode.md`, `plan-stories-mode.md`, `plan-phase-mode.md`, `_header-sequence.md` next-mode suggestions, etc.), README, `docs/site/user-guide/modes.md`, `docs/site/user-guide/commands.md`, `features.md`, CHANGELOG. The `go.md` re-render via `project-guide update` propagates automatically.

### N2: Rename `project_scaffold` → `scaffold_project`

Same scope as N1. `scaffold_project` follows the `<verb>_<noun>` convention established by all other modes. All cross-references updated; `scaffold-project-mode.md` is the new template filename.

### N3: `--test-first` Flag on `init`

Add `--test-first` boolean flag to `init`. When set (or `PROJECT_GUIDE_TEST_FIRST=1`), persist `test_first: true` to `.project-guide.yml`. The render pipeline passes `test_first` as a Jinja2 context variable. Mode templates that suggest the next coding step use `{% if test_first %}code_test_first{% else %}code_direct{% endif %}`. `--no-input` interaction: if `PROJECT_GUIDE_TEST_FIRST` is not set, default to `false` (no prompt needed; the flag is opt-in).

### N4: `--no-input` for `purge` and `update`

Wire `should_skip_input()` to `purge`'s `click.confirm()` and `update`'s modified-file prompts. When active (flag, env var, or non-TTY), `purge` proceeds without confirmation and `update` skips modified-file prompts and applies safe defaults (skip modified files; do not force-overwrite). Follows the Phase L `--no-input` contract: uses `should_skip_input()`, documented with `_require_setting()` behavior for any future required prompt.

### N5: `--quiet` / Output Suppression

Add `--quiet` / `-q` boolean flag to `init`, `update`, and `purge`. When set, suppress per-file progress lines from `_copy_template_tree` and `sync_files`. Errors, summaries, and explicit warnings are still printed. `--quiet` only affects stdout chatter; it does not affect stdin behavior (that is `--no-input`'s job). The two flags compose cleanly: `init --no-input --quiet` is a fully silent unattended install.

### N6: Config-File Fallback for Prompt Values

Add `_resolve_setting(name, cli_value, env_var, config_key, config, default)` helper to `project_guide/runtime.py`. Implements the documented resolution chain: CLI flag → env var → `.project-guide.yml` key → default. Used by `--test-first` (N3) and any future prompt that has a settable default. Pinned by a contract test in `test_runtime.py` (analogous to `test_require_setting_contract_exit_code_and_message` from Phase L).

### N7: Story Detection in `status`

`project-guide status` reads `docs/specs/stories.md` (resolved via `spec_artifacts_path` from `.metadata.yml`) when present and appends a **Stories** section to the output:

```
Stories: 12 total — 10 done, 1 in progress, 1 planned
  Next: Story N.b: v2.4.1 Rename scaffold_project
```

The "Next" line shows the first story whose status is not `[Done]`. If `stories.md` is absent or empty, the section is omitted. All parsing is regex-based (consistent with Phase K's `extract_stories_header_context` pattern). `--verbose` shows per-phase counts.

### N8: Mode Auto-Detection and Interactive Menu

`project-guide mode` without a mode name argument gains two new behaviors:

**Auto-detection:** Before listing modes, check each mode's `files_exist` prerequisites against the current working directory. Modes with all prerequisites satisfied are marked with a `✓`; modes with unmet prerequisites are shown but dimmed. This gives the developer an immediate signal about which modes are actionable.

**Interactive menu (TTY only):** When stdin is a TTY (i.e., `not should_skip_input()`), display modes grouped by category (Planning, Coding, Debugging, Documentation, Refactoring, Post-Release) with a numbered selection prompt. The developer selects by number; the mode is switched and `go.md` re-rendered. Under `--no-input` or non-TTY, falls back to the current plain-text listing.

### N9: Per-Project Metadata Overrides

`.project-guide.yml` gains an optional `metadata_overrides:` section that patches specific mode fields after the bundled `.metadata.yml` is loaded. Supported override fields: `next_mode`, `files_exist`, `info`, `description`. Deep-merge semantics: override entries are merged into the loaded `ModeDefinition`; unmentioned fields are unchanged. `metadata.py` applies overrides after `load_metadata()`. Validation: unknown mode names in overrides produce a `MetadataError`. This is the clean path for projects that want `--test-first` behavior without a CLI flag (they can set `next_mode` on `plan_stories` directly).

### N10: Pyve Detection and Bundled `project-essentials-pyve.md`

`project-guide init` runs `subprocess.run(['pyve', '--version'], capture_output=True)` during setup. Result is stored in `.project-guide.yml` as `pyve_version: "<version>"` (or `null` if not found). The render pipeline passes `pyve_installed: bool` and `pyve_version: str | None` as Jinja2 context variables.

A new bundled artifact template `project_guide/templates/project-guide/templates/artifacts/project-essentials-pyve.md` provides pre-written Pyve workflow rules. Planned content sections:

- **Two-environment pattern** — runtime env (`.venv/`) vs. dev testenv (`.pyve/testenv/venv/`); canonical invocation forms (`pyve run python ...`, `pyve test`, `pyve testenv run ruff/mypy ...`); the "pytest not found → use `pyve test`" signal; the "do not `pip install -e '.[dev]'` into the main venv" anti-pattern.
- **`requirements-dev.txt` story-writing rule** — any story that introduces dev tooling (ruff, mypy, pytest, types-* stubs) must include a task to create or update `requirements-dev.txt` with those dependencies. This ensures `pyve testenv --install -r requirements-dev.txt` works for the developer and that future contributors can reproduce the dev environment in one step. *Example gap:* a linting/type-checking story that configures `ruff.toml` and runs `pyve testenv run ruff check .` but never creates `requirements-dev.txt` leaves the testenv un-reproducible for anyone who clones the repo fresh.

`scaffold_project` and `plan_tech_spec` modes gain a conditional branch: if `pyve_installed` is true, the LLM is instructed to read `project-essentials-pyve.md` and copy/merge its content into `docs/specs/project-essentials.md`. The template is versioned with the package and improves across releases independently of per-project content.

### N11: Memory Review in `scaffold_project`

`scaffold_project` gains a new penultimate step (before "Present for Approval"): **Memory Review**. The LLM:

1. Reads all recorded memories from the project memory store (e.g., `.claude/projects/` memory files for Claude Code users).
2. For each memory, considers: is this project-specific? Should it also live in `project-essentials.md`?
3. Presents a summary to the developer: "I found N memories. Here are the ones that may belong in `project-essentials.md`: …"
4. Asks the developer to confirm which (if any) to migrate or copy.
5. Appends confirmed items to `project-essentials.md` following the heading convention.

The step includes a "skip if none" escape hatch: if the memory store is empty or inaccessible, note this and continue. The step explicitly targets `scaffold_project` because it runs once per project setup — it is the natural moment to reconcile prior-session memory with the project's permanent knowledge base.

### N12: Memory Reflection Instruction in `_header-common.md`

Add an instruction to `_header-common.md` (in the **Rules** block, as rule #7) that applies to every mode: **Before recording a new memory, reflect: is this fact project-specific (belongs in `docs/specs/project-essentials.md`) or cross-project (belongs in LLM memory)? Could it belong in both?** If the fact is project-specific, add it to `project-essentials.md` instead of or in addition to memory.

This instruction applies at the point of memory recording, not at the point of reading. It does not prevent the LLM from recording memories — it prompts reflection before doing so. The distinction between project-specific and cross-project facts is: project-specific facts (pyve setup for this project, this project's dogfooding rule) belong in `project-essentials.md`; cross-project facts (user preferences, general feedback on tone) belong in LLM memory.

---

## Technical Changes

### New and Modified Files

**Python (`project_guide/`)**
- `cli.py` — N1/N2 mode name constants; N3 `--test-first`; N4 `--no-input` on purge/update; N5 `--quiet`; N7 story detection; N8 interactive menu + auto-detect; N10 pyve detection
- `config.py` — N3 `test_first` field; N6 `_resolve_setting` (in `runtime.py`); N9 `metadata_overrides` field; N10 `pyve_version` field
- `runtime.py` — N6 `_resolve_setting` helper
- `metadata.py` — N9 override merging in `load_metadata`
- `render.py` — N3 `test_first` context var; N10 `pyve_installed`/`pyve_version` context vars

**Templates (source of truth: `project_guide/templates/project-guide/`)**
- `templates/modes/code-direct-mode.md` (rename from `code-velocity-mode.md`) — N1
- `templates/modes/scaffold-project-mode.md` (rename from `project-scaffold-mode.md`) — N2; + N11 memory review step
- `templates/modes/_header-common.md` — N12 memory reflection rule
- `templates/modes/default-mode.md` — N1/N2 references; N3 `{% if test_first %}` next-mode branches; N8 mode listing (updated for auto-detection markers)
- `templates/modes/plan-stories-mode.md` — N1/N2 references; N3 `{% if test_first %}` next-mode branch
- `templates/modes/plan-phase-mode.md` — N1/N2 references; N3 `{% if test_first %}` next-mode branch
- `templates/modes/plan-tech-spec-mode.md` — N10 pyve branch
- `templates/artifacts/project-essentials-pyve.md` (new) — N10

**Metadata and Config**
- `templates/project-guide/.metadata.yml` — N1/N2 mode key renames; N3/N10 new context vars in `common` block

**Docs**
- `docs/specs/features.md` — N1/N2 mode table; N3/N4/N5/N7/N8/N9 new FR entries; `.project-guide.yml` schema updated
- `docs/specs/tech-spec.md` — N1/N2 filename table; `Config` dataclass fields; module docs
- `README.md` — mode table; command reference; config schema
- `docs/site/user-guide/modes.md` — N1/N2 entries
- `docs/site/user-guide/commands.md` — N3–N9 flag/behavior docs
- `CHANGELOG.md` — per-story entries

### Config Schema Changes

```yaml
# .project-guide.yml additions
test_first: false          # N3: prefer code_test_first when suggesting next coding mode
pyve_version: null         # N10: detected pyve version, or null
metadata_overrides:        # N9: per-project mode field patches (optional)
  <mode_name>:
    next_mode: <string>
    files_exist: [<path>, ...]
```

### No New Runtime Dependencies

`subprocess.run(['pyve', '--version'])` uses stdlib. Interactive menu uses Click's existing `click.prompt()`. No new packages required.

---

## Out of Scope for Phase N

- `code_production` mode and `code_*` abstraction — deferred until the code mode hierarchy settles post-rename.
- Audit modes (`audit_security`, `audit_architecture`, etc.) — deferred.
- Release helper / version-bump / tag automation — deferred; developer prefers tool-agnostic.
- Migration tooling for `docs/guides/` → `docs/project-guide/` — deferred.
- Support for literal `{{ var }}` strings in templates — deferred (bridge with `{% raw %}` on a case-by-case basis).
- Validation/linting of `project-essentials.md` content — freeform by design; not in this phase.
- Auto-detection of stale `project-essentials.md` — deferred.
- `create_or_modify` action type — deferred until multiple artifacts develop the need.
- `refactor_essentials` mode — not needed; existing planning modes cover the lifecycle.
- Legacy broken-state detection for `init` — deferred.
- `--interactive` flag (force interactive mode over non-TTY) — deferred.
