# stories.md -- project-guide (python)

This document breaks the `project-guide` project into an ordered sequence of small, independently completable stories grouped into phases. Each story has a checklist of concrete tasks. Stories are organized by phase and reference modules defined in `tech-spec.md`.

Put **`vX.Y.Z` in the story title only when that story ships the package version bump** for that release. Doc-only or polish stories **omit the version from the title** (they share the release with the preceding code story, or use your project’s doc-release policy). **One semver bump per owning story** — extra tasks on the *same* story share that bump; see `project-essentials.md`. Semantic versioning applies to the package. Stories are marked with `[Planned]` initially and changed to `[Done]` when completed.

For a high-level concept (why), see [`concept.md`](concept.md). For requirements and behavior (what), see [`features.md`](features.md). For implementation details (how), see [`tech-spec.md`](tech-spec.md). For project-specific must-know facts, see [`project-essentials.md`](project-essentials.md) (`plan_phase` appends new facts per phase). For the workflow steps tailored to the current mode (cycle steps, approval gates, conventions), see [`docs/project-guide/go.md`](../project-guide/go.md) — re-read it whenever the mode changes or after context compaction.

---

## Version Cadence

Standard semantic versioning, with these conventions:

- **Every story belongs to a phase.** Bugfix stories included. No orphan stories.
- **Per-story bumping** (when a story owns its own release):
  - Bugfix or trivial change → **patch** (`vX.Y.Z+1`)
  - Feature or improvement → **minor** (`vX.Y+1.0`)
  - Breaking change → **major** (`vX+1.0.0`). Post-1.0 only, and only via the `plan_production_phase` mode, which negotiates with the developer about whether the breakage is substantively user-facing or technically-but-trivially breaking (example: a log-format change is technically breaking, but if logs aren't a core consumer capability, the developer may judge it minor or even patch).
- **Phase-bundling option:** a phase can run unversioned during work and ship a single release/tag at end-of-phase. Stories within the phase carry no version in their title; the phase's last story owns the bump (magnitude determined by the highest-impact change in the bundle).
- **No out-of-order implementation.** Story order in this file is the order of execution. If work order needs to change, **reorganize/renumber here first** — don't skip ahead and create version-number gaps.
- **Pre-1.0:** standard semver applies; version starts at `v0.1.0` (Story A.a).
- **Post-1.0:** every phase must go through `plan_production_phase` (the lighter `plan_phase` is pre-1.0 only). Major bumps only happen through that mode's negotiation step.

This is the authoritative cadence rule. **Do not extrapolate the bump magnitude from `pyproject.toml`'s current version** — re-read this section whenever you're about to assign a version to a story.

---

## Phase P: Auto-heal & Production Hardening

Collapse the `docs/project-guide/` install footprint in consumer repos to a single tracked file (`go.md`) plus the tracked config (`.project-guide.yml`); everything else gets gitignored and is repopulated on demand by a new self-contained `heal` command that runs invisibly on every `project-guide` invocation. Goal: zero-friction "clone and go" — any `project-guide` command (including `--help`) heals the install if needed and otherwise stays silent. Bundled with a subset of post-1.0 production-readiness items: `SECURITY.md`, `CONTRIBUTING.md`, `.github/dependabot.yml`, and CI workflow PR-readiness. Branch protection and PR-only workflow are explicitly deferred until contributors join.

**Phase plan:** [`phase-p-auto-heal-plan.md`](phase-p-auto-heal-plan.md).

**Implementation order:** `heal` core (P.a) → auto-hook (P.b) → `--no-input` semantics (P.c) → gitignore template flip (P.d). Production hardening items (P.e–P.h) are independent and can ship in any order. P.i is the doc-only story that bundles the v2.6.0 release.

**Version cadence:** phase-bundled — stories within Phase P run unversioned; **P.i owns the single `v2.6.0` bump** at end-of-phase (per the bundled-release option in the Version Cadence rule).

### Story P.a: Heal command with drift detection and create-missing semantics [Done]

Add a new top-level `project-guide heal` command that detects drift between the installed template tree and the bundled package templates, then offers to fix it interactively. Idempotent and self-contained — no behavior change to other commands yet (the auto-hook lands in P.b). Missing `.project-guide.yml` is a hard error: `heal` cannot bootstrap a project that has never been initialized.

- [x] In `project_guide/sync.py`: add `heal_files(config)` (or extend `sync_files()` with a `create_missing=True` flag — pick whichever yields the smaller diff) that, in addition to the existing hash-based update behavior, also creates files that are present in the bundled template tree but absent on disk *(existing `sync_files()` already provides create-missing semantics; reused as-is for the smallest diff)*
- [x] In `project_guide/cli.py`: add the `heal` Click command
  - [x] On missing `.project-guide.yml`: exit 1 with stderr message `Missing .project-guide.yml — run 'project-guide init' to bootstrap the project.`
  - [x] Discover drift (missing + stale files) using existing `sync.py` helpers
  - [x] When zero drift: exit 0 with **no stdout** (silent success — required for the auto-hook in P.b)
  - [x] When drift detected: print one-line summary to stderr (`<N> templates missing or stale.`), then prompt `Update? [Y/n] ` (default Y on bare Enter)
  - [x] On yes: apply updates via `heal_files()` and re-render `go.md` for the current mode
  - [x] On no: exit 1 with no further action
  - [x] `SchemaVersionError` propagates unchanged — same older/newer guidance as `update`
- [x] In `tests/test_cli.py`: add `heal` tests
  - [x] Clean state → exit 0, no stdout, no file writes
  - [x] Missing files → prompt fires, accepts `y` / `Y` / Enter (default), creates files
  - [x] Stale files → prompt fires, applies update with backup of pre-existing modified files (where applicable)
  - [x] Decline (`n`) → exit 1, no file writes
  - [x] Missing `.project-guide.yml` → exit 1, exact stderr message
  - [x] `SchemaVersionError` (older/newer) → unchanged guidance preserved
- [x] In `tests/test_sync.py`: add tests for create-missing semantics

### Story P.b: Auto-hook with recursion guard [Done]

Wire a Click group-level callback so every `project-guide` invocation (including `--help` and `--version`) runs `heal` first via the hook. The hook is silent in the steady state; only fires the prompt when there's actual drift. A `PROJECT_GUIDE_HEALING=1` env var prevents the hook from re-entering when `heal` runs as part of its own dispatch.

- [x] In `project_guide/cli.py`: add a Click group `result_callback` or pre-invoke hook on the `main` group *(implemented as a custom `HealGroup(click.Group)` overriding `main()` so the hook fires before eager-flag short-circuit, satisfying the `--help` / `--version` requirement)*
  - [x] Skip the hook when `PROJECT_GUIDE_HEALING=1` is set in the environment
  - [x] Skip the hook when `.project-guide.yml` is absent (let `init` bootstrap the project; `heal` would error otherwise)
  - [x] Otherwise call into the same drift-detection + prompt path as `heal`
  - [x] Set `PROJECT_GUIDE_HEALING=1` in `os.environ` when `heal` runs (whether via the hook or invoked directly) so any nested `project-guide` calls don't re-enter
  - [x] If user declines the prompt, continue with the original subcommand (do not block — refusing the heal is the user's choice)
- [x] In `tests/test_cli.py`: add hook integration tests
  - [x] Clean state → hook is invisible, original subcommand runs as before
  - [x] Drift detected → hook prompts, applies fix on yes, runs original subcommand
  - [x] Drift detected → hook prompts, on no continues to original subcommand without applying fix
  - [x] Missing `.project-guide.yml` → hook is skipped, original subcommand handles missing-config
  - [x] `PROJECT_GUIDE_HEALING=1` set → hook is skipped (recursion guard test)
  - [x] `--help` and `--version` → hook still fires (this is the "any command heals" goal)

### Story P.c: --no-input auto-yes for heal with stderr notice [Done]

Apply the existing `--no-input` contract (`should_skip_input()` from `runtime.py`) to `heal`: under `--no-input`, the `[Y/n]` prompt is replaced with auto-yes, and a one-line stderr notice signals that file writes occurred. The notice is non-suppressible so CI logs and embedding callers (pyve scaffolding, etc.) have a visible signal.

- [x] In `project_guide/cli.py:heal`:
  - [x] Use `should_skip_input(no_input)` from `runtime.py` to detect `--no-input` mode (flag, env, `CI=1`, non-TTY stdin)
  - [x] Under skip-input: emit stderr `Auto-healing <N> templates under --no-input.` then proceed with auto-yes (apply updates, re-render `go.md`)
  - [x] Under interactive mode: behavior unchanged from P.a (prompt fires)
- [x] The auto-hook from P.b inherits this — when the hook fires inside a parent invocation that has `--no-input` (or any equivalent trigger), the hook's heal call also auto-yes's
- [x] In `tests/test_cli.py`: add `--no-input` tests for `heal`
  - [x] `--no-input` flag with drift → no prompt, stderr notice present, files written, exit 0
  - [x] `CI=1` env with drift → same behavior
  - [x] Non-TTY stdin (piped) with drift → same behavior
  - [x] `--no-input` with no drift → still silent (no stderr notice; the notice is "auto-healing" specifically)
  - [x] Auto-hook under `--no-input` parent command → heals silently+stderr-notice, parent command proceeds

### Story P.d: Invert .gitignore template — track only go.md [Done]

Change `init`'s gitignore writer so that everything under `target_dir` is ignored except `go.md` (plus the existing `*.bak.*` rule). The rationale: only `go.md` needs to be visible to IDE-integrated LLMs (which typically hide gitignored files from the LLM's view) — every other file is static bundled data that `heal` repopulates on first invocation. This eliminates the ~35-file install footprint from consumer repo `git status` / PR reviews.

- [x] In `project_guide/cli.py:_ensure_gitignore_entry()`: rewrite the `# project-guide` block to:
  ```
  # project-guide
  docs/project-guide/**
  !docs/project-guide/go.md
  docs/project-guide/**/*.bak.*
  ```
  (substitute the actual `target_dir` value at write time)
- [x] Existing-block detection: if a previous `# project-guide` block exists with the old `docs/project-guide/go.md` line (which incorrectly gitignored `go.md` — confirm or correct based on the actual current code), replace it cleanly without leaving the old content; for any other unrecognized block, leave alone and emit a stderr warning so the developer can resolve manually *(also recognizes the current `.bak.*`-only legacy block this repo has been using)*
- [x] **Migration path** for existing consumer repos: documented as `project-guide init --force`. No automatic detection of "tracked-but-now-ignored" files; the developer uses `git rm --cached` if they want to clean history-going-forward
- [x] In `tests/test_cli.py`: update `init` gitignore tests
  - [x] Fresh `init` → new block written, exact text match
  - [x] `init --force` over existing project with old block → block rewritten cleanly
  - [x] `init` with foreign `# project-guide` block (non-recognized content) → warn, do not overwrite
- [x] In the bundled package: confirm there is no other place that hardcodes `go.md` as gitignored (check `templates/`, `tests/`, docs); update or test-verify *(grep verified — no other place hardcodes the gitignore policy)*

### Story P.e: SECURITY.md [Planned]

Add a top-level `SECURITY.md` documenting the vulnerability reporting channel and supported-versions policy.

- [ ] Create `SECURITY.md` at repo root with:
  - [ ] Apache-2.0 / Pointmatic file header comment block
  - [ ] **Supported versions** table — latest minor only (e.g., v2.6.x)
  - [ ] **Reporting a vulnerability** section: GitHub Security Advisories (preferred) link to `https://github.com/pointmatic/project-guide/security/advisories/new`; fallback contact email if appropriate
  - [ ] Response expectations — acknowledge within ~7 days; no hard SLA on fix time given solo-dev status
  - [ ] Statement that the package contains no secrets and operates entirely offline (low attack surface)

### Story P.f: CONTRIBUTING.md [Planned]

Add a top-level `CONTRIBUTING.md` documenting dev environment setup, code style, test requirements, PR process, and release process. Replaces (or supersedes) the brief Contributing/Development sections in README.md.

- [ ] Create `CONTRIBUTING.md` at repo root with:
  - [ ] Apache-2.0 / Pointmatic file header comment block
  - [ ] **Dev environment**: pyve two-environment pattern (cite `pyve-essentials.md`); editable install via `pyve run pip install -e .` and testenv via `pyve testenv init && pyve testenv install -r requirements-dev.txt`
  - [ ] **Code style**: `ruff check` + `ruff format`; mypy clean
  - [ ] **Tests**: `pyve test`; minimum 85% coverage; parametrized mode-render regression test
  - [ ] **PR process**: fork → branch → PR → CI must be green → maintainer review (note: branch protection not yet enabled, but PR workflow is the expected path for outside contributors)
  - [ ] **Release process**: `plan_production_phase` for new phases, `bump-version <X.Y.Z>` at end-of-phase, GitHub Release triggers `publish.yml`
  - [ ] **Substantive contributions** suggestion: use `code_direct` or `code_test_first` to scope changes via stories before sending a PR
- [ ] Update `README.md` Contributing/Development sections to point at `CONTRIBUTING.md` as canonical (do not delete the README sections — they remain as quick-reference summaries)

### Story P.g: .github/dependabot.yml [Planned]

Configure Dependabot to keep runtime, dev, and CI dependencies current with weekly updates. Group minor + patch updates per ecosystem to limit PR noise; majors land separately.

- [ ] Create `.github/dependabot.yml` with:
  - [ ] `pip` ecosystem (root) — weekly schedule, group minor + patch into one PR per week, label `dependencies`
  - [ ] `github-actions` ecosystem (`.github/workflows/`) — weekly schedule, group minor + patch into one PR per week, label `dependencies` + `ci`
  - [ ] Reasonable PR title prefixes (`chore(deps)`, `chore(ci)`)
- [ ] Verify the file passes GitHub's Dependabot config validation (no schema errors in the Insights → Dependency graph view after pushing)

### Story P.h: CI workflow PR-readiness [Planned]

Tighten `.github/workflows/ci.yml` and `.github/workflows/test.yml` to fully gate on lint + test results so they are PR-ready. Branch protection is not enabled (deferred per developer override), but workflows must be correct so the switch is one settings flip when contributors join.

- [ ] Audit `ci.yml`:
  - [ ] Triggers include `pull_request` (in addition to whatever push-based trigger exists today)
  - [ ] Exit codes propagate: no `continue-on-error: true` on lint or test steps
  - [ ] Both lint (`ruff check`) and tests (`pyve test` or equivalent) are mandatory
- [ ] Audit `test.yml` (multi-platform matrix):
  - [ ] Triggers include `pull_request`
  - [ ] All matrix legs are required (no `continue-on-error` shortcuts)
- [ ] Document the green-CI expectation in `CONTRIBUTING.md` (cross-reference from P.f) — informal until branch protection is enabled

### Story P.i: v2.6.0 Doc updates and release bundling [Planned]

Doc-only release bundling story for Phase P. Updates the spec artifacts, README, and `project-essentials.md` to reflect the new auto-heal flow, the inverted gitignore policy, the IDE-LLM-visibility constraint that forces `go.md` to remain tracked, and the new production-hardening files. Bumps the package to **v2.6.0** and seeds a `## [2.6.0]` CHANGELOG entry. **This story owns the single Phase P version bump per the phase-bundling rule in Version Cadence.**

- [ ] Update `docs/specs/features.md`:
  - [ ] Add a new functional requirement section for `heal` (FR-14 or next available)
  - [ ] Update `## Inputs / Command Line` to add `project-guide heal` with its options (`--no-input`)
  - [ ] Update `## Outputs / File Structure` to reflect that only `go.md` is tracked in consumer repos
  - [ ] Update FR-8 (`--no-input` / CI Mode) to add `heal` to the list of commands that respect the contract
  - [ ] Update Acceptance Criteria — add criteria for auto-heal silent-when-clean and auto-yes-with-stderr-notice
- [ ] Update `docs/specs/tech-spec.md`:
  - [ ] Add `heal` to the CLI Design / Commands table
  - [ ] Add the auto-hook + recursion-guard mechanism under Cross-Cutting Concerns
  - [ ] Update `## .gitignore Management` block to the new policy (single `!docs/project-guide/go.md` exception)
  - [ ] Update the "Nine intuitive commands" / "console script" verbiage if it appears
- [ ] Update `README.md`:
  - [ ] Line 39 — update CLI Interface count from "Nine" to "Ten" (or rephrase to drop the count)
  - [ ] Line 91 — replace `The rendered go.md and .bak.*  backup files are gitignored.` with the corrected statement: `Everything under docs/project-guide/ is gitignored except go.md (which the LLM reads) and .bak.* backup files.`
  - [ ] Add a `### heal` section to Command Reference (between `update` and `override`, or wherever fits the alphabetical/logical order)
  - [ ] Update Quick Start step 1 "This creates" footnote to reflect the new tracked-vs-ignored policy
  - [ ] Cross-reference `CONTRIBUTING.md` from the Contributing/Development sections
  - [ ] Cross-reference `SECURITY.md` from a new "Security" section (or under the existing badge area)
- [ ] Append to `docs/specs/project-essentials.md` (do not rewrite or reorder existing content):
  - [ ] **Auto-heal hook contract** — every `project-guide` invocation calls `heal` first via a Click group-level callback; recursion guarded by `PROJECT_GUIDE_HEALING=1` env var; silent in steady state; missing `.project-guide.yml` is a hard error (not a heal opportunity)
  - [ ] **Inverted gitignore policy** — only `go.md` is tracked under `target_dir`; everything else is bundled static data that `heal` repopulates on first post-clone invocation
  - [ ] **IDE-LLM visibility constraint** — `go.md` must remain non-gitignored because IDE-integrated LLMs (Cursor, Claude Code, etc.) typically hide gitignored files from the LLM's view; the LLM's instruction to `Read docs/project-guide/go.md` requires the file to be visible. Repo-history value of `go.md` is incidental and the file churns on every mode switch — that churn is acceptable cost for LLM visibility
  - [ ] **`heal` vs. `update` vs. `init`** — `init` is one-time bootstrap (writes `.project-guide.yml`), `update` refreshes files that exist on disk, `heal` is `update` plus create-missing and is the right command for fresh-clone-with-templates-gitignored
  - [ ] **`--no-input` auto-yes for `heal`** — file writes under `--no-input` emit a one-line stderr notice (`Auto-healing N templates under --no-input.`) so CI logs and embedding callers have a visible signal
- [ ] Bump `project_guide/version.py`: `__version__ = "2.6.0"`
- [ ] Bump `pyproject.toml`: `version = "2.6.0"`
- [ ] Add `## [2.6.0] - <date>` entry to `CHANGELOG.md` summarizing all of Phase P's user-visible changes (heal command, auto-hook, gitignore inversion, SECURITY.md, CONTRIBUTING.md, dependabot, CI tightening)

---

## Future

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
