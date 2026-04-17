# Project-Guide — Calm the chaos of LLM-assisted coding

This document provides step-by-step instructions for an LLM to assist a human developer in a project. 

## How to Use Project-Guide

### For Developers
After installing project-guide (`pip install project-guide`) and running `project-guide init`, instruct your LLM as follows in the chat interface: 

```
Read `docs/project-guide/go.md`
```

After reading, the LLM will respond:
1. (optional) "I need more information..." followed by a list of questions or details needed. 
  - LLM will continue asking until all needed information is clear.
2. "The next step is ___."
3. "Say 'go' when you're ready." 

For efficiency, when you change modes, start a new LLM conversation. 

### For LLMs

**Modes**
This Project-Guide offers a human-in-the-loop workflow for you to follow that can be dynamically reconfigured based on the project `mode`. Each `mode` defines a focused cycle of steps to guide you (the LLM) to help generate artifacts for some facet in the project lifecycle. This document is customized for code_direct.

**Approval Gate**
When you have completed the steps, pause for the developer to review, correct, redirect, or ask questions about your work.  

**Rules**
- Work through each step methodically, presenting your work for approval before continuing a cycle. 
- When the developer says "go" (or equivalent like "continue", "next", "proceed"), continue with the next action. 
- If the next action is unclear, tell the developer you don't have a clear direction on what to do next, then suggest something. 
- Never auto-advance past an approval gate—always wait for explicit confirmation. 
- At approval gates, present the completed work and wait. Do **not** propose follow-up actions outside the current mode step — in particular, do not prompt for git operations (commits, pushes, PRs, branch creation), CI runs, or deploys unless the current step explicitly calls for them. The developer initiates these on their own schedule.
- After compacting memory, re-read this guide to refresh your context.
- Before recording a new memory, reflect: is this fact project-specific (belongs in `docs/specs/project-essentials.md`) or cross-project (belongs in LLM memory)? Could it belong in both? If project-specific, add it to `project-essentials.md` instead of or in addition to memory.
- When creating any new source file, add a copyright notice and license header using the comment syntax for that file type (`#` for Python/YAML/shell, `//` for JS/TS, `<!-- -->` for HTML/Svelte). Check this project's `project-essentials.md` for the specific copyright holder, license, and SPDX identifier to use.

---

## Project Essentials

Must-know facts for future LLMs working on the project-guide project. These are things a smart newcomer could easily miss and waste time on. This content gets injected verbatim under a `## Project Essentials` section in every rendered mode, so entries below use `###` for subsections.

### Workflow rules — pyve environment conventions

This project uses `pyve` with **two separate environments**. Picking the wrong invocation form often "works" but leads to subtle drift. Use the canonical forms below:

- **Runtime code (the `project_guide` package itself):** `pyve run python ...` or `pyve run project-guide ...`.
- **Tests:** `pyve test [pytest args]` — **not** `pyve run pytest`. Pytest is not installed in the main `.venv/`; it lives in the dev testenv.
- **Dev tools (ruff, mypy, pytest):** `pyve testenv run ruff check ...`, `pyve testenv run mypy ...`. These use `.pyve/testenv/venv/`.
- **Install dev tools:** `pyve testenv --install -r requirements-dev.txt`. **Do not** run `pip install -e ".[dev]"` into the main venv — that pollutes the runtime environment with test-only dependencies and breaks the two-env isolation.

If `pytest` fails with "not found" that is the signal to use `pyve test`, not to `pip install pytest` into the wrong venv.

### LLM-internal vs. developer-facing invocation

`pyve run` is for the LLM's own Bash-tool invocations; developer-facing command suggestions use the bare form verbatim from the mode template.

- ✅ Developer-facing: `project-guide mode plan_phase`
- ❌ Developer-facing: `pyve run project-guide mode plan_phase`
- ✅ LLM Bash-tool: `pyve run project-guide mode plan_phase`

**Why:** the LLM's Bash-tool shell does not auto-activate `.venv/`, so the LLM must wrap its own commands with `pyve run`. The developer's shell is typically already pyve/direnv-activated, so the bare form resolves correctly and matches the commands quoted throughout mode templates and documentation.

**How to apply:** never prepend environment wrappers (`pyve run`, `poetry run`, `uv run`, etc.) to commands you quote back to the developer from a mode template. Use the wrapper only when you execute the command yourself through the Bash tool.

### Dogfooding rule — template source of truth

This project uses itself (dogfooding). Template files live in **two places** that must not be confused:

- **Source of truth:** `project_guide/templates/project-guide/` — the bundled templates that ship inside the Python package. **Edit these.**
- **Installed copy:** `docs/project-guide/` — the rendered output from running `project-guide init` on this project. **Never hand-edit these.** They are regenerated by `project-guide mode` and `project-guide update`, and any hand-edits will be lost on the next sync.

In particular, `docs/project-guide/go.md` is dynamically re-rendered by the `project-guide mode` command every time the mode changes. Never hand-edit `go.md`. After editing a source template, run `project-guide update` (while working in an editable install, e.g. `pyve run pip install -e .`) to propagate changes into the installed copy before re-rendering.

### Architecture quirks

- **v2 architecture is mode-driven Jinja2 templating,** not static file sync. The v1 "copy files to `docs/guides/`" pattern is deprecated; all new work targets `docs/project-guide/` via rendered templates.
- **Phase K release lifecycle:** `archive_stories` mode + the `archive-stories` CLI command form a two-part pattern — the mode template walks the developer through the decision conversationally; the CLI performs the deterministic file move + re-render. Keep this split when adding similar lifecycle commands.
- **Phase letters continue across archive boundaries.** When planning a new phase with `plan_phase` and `stories.md` is empty (post-archive), the `.archive/stories-vX.Y.Z.md` files must be read to determine the next letter. The rules are centralized in `project_guide/templates/project-guide/templates/modes/_phase-letters.md`.

### `--no-input` contract (added v2.2.1)

Any future interactive prompt added to a CLI command **must** use the `should_skip_input()` helper from `project_guide/runtime.py` to decide whether to read from stdin, and must use `_require_setting()` to fail loudly when a required setting has no default under `--no-input`. The contract and the exact error message format are pinned by `tests/test_cli.py::test_require_setting_contract_exit_code_and_message` — do not change that message lightly, as downstream tooling (e.g., pyve) may cite it.

`init` currently has no prompts, but the plumbing (`skip_input = should_skip_input(no_input)` in `cli.py:init`) is already in place. The unused local is intentional — see the `# noqa: F841` comment.

### Commit and version style

- **One version bump per story** (code stories only — doc-only stories share the version with the preceding code story or bump to a `.N` doc release).
- **Commit messages reference the story ID**: `"Story M.a: v2.3.0 project-essentials render hook"`.
- **Direct commits to main** in `code_direct` mode — no branches, no PRs.
- **Bump version in three places** per story: `project_guide/version.py`, `pyproject.toml`, and `CHANGELOG.md` (new `## [X.Y.Z]` entry dated).

### Config schema versioning

`.project-guide.yml` has a `version:` field that tracks the **config schema** (currently `"2.0"`, pinned by `SCHEMA_VERSION` in `project_guide/config.py`), not the package version. Policy:

- **Bump `SCHEMA_VERSION` only for breaking changes:** field rename, field removal, type change, or semantic-meaning change of an existing field.
- **Do NOT bump for additive-with-default changes.** Adding a new optional field with a sensible default (as in every Phase N field: `test_first`, `pyve_version`, `metadata_overrides`) is already backwards-compatible via `data.get(key, default)` in `Config.load()`.
- **On mismatch,** `Config.load()` raises `SchemaVersionError(direction="older"|"newer")`. `cli.py:update` handles this specially: on `"older"` it points the user at `project-guide init --force` (which performs the backup at the destructive-overwrite site); on `"newer"` it tells the user to upgrade project-guide. `cli.py:init` is the sole writer of `.project-guide.yml.bak.<timestamp>`: with `--force` on an existing config it copies the current file aside before overwriting it, so the backup is idempotent (one per refresh) regardless of the entry point.
- **When a real breaking change arrives,** revisit adding a migration registry (deferred by design — YAGNI until there's something to migrate).

### Approval gate discipline

At approval gates, present the completed work and wait. **Do not prompt for, offer, or initiate git operations** (commits, pushes, PRs, branch creation), CI runs, or deploys unless the current step explicitly calls for them. This applies to every mode, not just `code_direct`.

**Why:** in the `code_direct` cycle, the template lists "direct commits to main" and "commit messages reference story IDs" as conventions — those are *developer-lane* conventions describing what the developer does on their own schedule. They are not instructions for the LLM to offer or bundle commits. The `_header-common.md` **Rules** block makes this universal at read time. The `code_direct` and `code_test_first` "Present" steps reinforce it with explicit "Do not propose commits, pushes, or bundling options. Do not offer 'want me to also...?' follow-ups" language.

**How to apply:** when presenting a completed story, end with a concise status + suggested next story. Do not offer "commit first or continue?" options. Do not mention bundling commits. The developer decides; the LLM presents and waits.


---

# code_direct mode (cycle)

> Generate code directly, test after


Implement stories rapidly with direct commits to main. Focus on feature completion and iteration speed over process overhead.

**Next Action**
Restart the cycle of steps. 

---


## Cycle Steps

For each story:

1. **Read** the story's checklist from `docs/specs/stories.md`
2. **Implement** all tasks in the checklist
3. **Add copyright/license headers** to every new source file
4. **Run tests** -- `pyve run pytest` (fix failures before continuing)
5. **Run linting** -- fix any issues immediately
6. **Mark tasks** as `[x]` in `stories.md` and change story suffix to `[Done]`
7. **Bump version** in package manifest and source (if the story has a version)
8. **Update CHANGELOG.md** with the version entry
9. **Present** the completed story concisely: what changed (files + line refs), verification results (test counts, lint status), and the suggested next story. Do not propose commits, pushes, or bundling options. Do not offer "want me to also…?" follow-ups.
10. **Wait** for the developer to say "go" before starting the next story

## Velocity Practices

**LLM's role in each cycle:**

- **Version bump per story** -- v0.1.0, v0.2.0, v0.3.0, etc. — bump in package manifest and source
- **Minimal process overhead** -- focus on making it work, not making it perfect
- **Tests run after every story** -- not after every file, but before presenting to developer
- **Fix linting immediately** -- small incremental fixes, not batch cleanup
- **Update CHANGELOG.md** with the version entry before presenting

**Developer's role (do NOT prompt for, offer, or initiate):**

- **Direct commits to main** -- no branches, no PRs, no code review (velocity convention)
- **Commit messages** reference story IDs: `"Story A.a: v0.1.0 Hello World"`
- **Decides when to commit** -- the LLM presents, the developer commits. Multiple stories may be bundled into one commit at the developer's discretion — that is not the LLM's call to make or suggest.

## Story Ordering

- Start with Story A.a (Hello World) if not yet implemented
- If unclear which story is next, ask: "Which story should I work on next?"
- Never skip ahead -- complete stories in order within each phase

## File Header Reminder

Every new source file must include the copyright and license header as the very first content (before code, docstrings, or imports).

## When to Switch Modes

Switch to **code_test_first** when:
- Working on a story with complex logic that benefits from TDD
- The developer requests test-first approach

Switch to **debug** when:
- A bug is discovered during implementation
- Tests are failing unexpectedly

Switch to **production mode** when:
- CI/CD phase is complete and branch protection is enabled
- The project is ready for public users

