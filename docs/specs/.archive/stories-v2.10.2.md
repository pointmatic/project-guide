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

**Version cadence:** phase-bundled — stories P.a–P.i ran unversioned and shipped together as **v2.6.0** (P.i owned the single bundled bump). **Stories P.j, P.k, and P.l were added post-bundle** and follow standard per-story cadence: **P.j → v2.6.1** (patch — gitignore-block tightening, a fix-up to P.d), **P.k → v2.7.0** (minor — new `git-push` wrapper command), **P.l → v2.7.1** (patch — switch the gitignore block from negation to explicit-list form for IDE compatibility). Phases can be extended after their bundled release, but new stories then follow the standard per-story cadence rather than rejoining the (already-shipped) bundle.

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

### Story P.e: SECURITY.md [Done]

Add a top-level `SECURITY.md` documenting the vulnerability reporting channel and supported-versions policy.

- [x] Create `SECURITY.md` at repo root with:
  - [x] Apache-2.0 / Pointmatic file header comment block
  - [x] **Supported versions** table — latest minor only (e.g., v2.6.x)
  - [x] **Reporting a vulnerability** section: GitHub Security Advisories (preferred) link to `https://github.com/pointmatic/project-guide/security/advisories/new`; fallback contact email if appropriate *(no real maintainer email exists in `pyproject.toml` — placeholder only — so the section points solely at GitHub Security Advisories rather than a fake fallback)*
  - [x] Response expectations — acknowledge within ~7 days; no hard SLA on fix time given solo-dev status
  - [x] Statement that the package contains no secrets and operates entirely offline (low attack surface) *(folded into a "Threat model" section that also enumerates the narrow attack surface)*

### Story P.f: CONTRIBUTING.md [Done]

Add a top-level `CONTRIBUTING.md` documenting dev environment setup, code style, test requirements, PR process, and release process. Replaces (or supersedes) the brief Contributing/Development sections in README.md.

- [x] Create `CONTRIBUTING.md` at repo root with:
  - [x] Apache-2.0 / Pointmatic file header comment block
  - [x] **Dev environment**: pyve two-environment pattern (cite `pyve-essentials.md`); editable install via `pyve run pip install -e .` and testenv via `pyve testenv init && pyve testenv install -r requirements-dev.txt`
  - [x] **Code style**: `ruff check` + `ruff format`; mypy clean
  - [x] **Tests**: `pyve test`; minimum 85% coverage; parametrized mode-render regression test
  - [x] **PR process**: fork → branch → PR → CI must be green → maintainer review (note: branch protection not yet enabled, but PR workflow is the expected path for outside contributors)
  - [x] **Release process**: `plan_production_phase` for new phases, `bump-version <X.Y.Z>` at end-of-phase, GitHub Release triggers `publish.yml`
  - [x] **Substantive contributions** suggestion: use `code_direct` or `code_test_first` to scope changes via stories before sending a PR
- [x] Update `README.md` Contributing/Development sections to point at `CONTRIBUTING.md` as canonical (do not delete the README sections — they remain as quick-reference summaries) *(also corrected stale `pip install -e ".[dev]"` / `pytest` quick-reference to the pyve canonical commands; added cross-reference to `SECURITY.md`)*

### Story P.g: .github/dependabot.yml [Done]

Configure Dependabot to keep runtime, dev, and CI dependencies current with weekly updates. Group minor + patch updates per ecosystem to limit PR noise; majors land separately.

- [x] Create `.github/dependabot.yml` with: *(updated the existing file rather than creating it from scratch — the prior version had weekly schedules but no grouping, no PR-title prefixes, and used different labels)*
  - [x] `pip` ecosystem (root) — weekly schedule, group minor + patch into one PR per week, label `dependencies`
  - [x] `github-actions` ecosystem (`.github/workflows/`) — weekly schedule, group minor + patch into one PR per week, label `dependencies` + `ci`
  - [x] Reasonable PR title prefixes (`chore(deps)`, `chore(ci)`)
- [ ] Verify the file passes GitHub's Dependabot config validation (no schema errors in the Insights → Dependency graph view after pushing) *(deferred to post-push verification — cannot be checked locally; YAML parses cleanly and matches the documented Dependabot v2 schema)*

### Story P.h: CI workflow PR-readiness [Done]

Tighten `.github/workflows/ci.yml` and `.github/workflows/test.yml` to fully gate on lint + test results so they are PR-ready. Branch protection is not enabled (deferred per developer override), but workflows must be correct so the switch is one settings flip when contributors join.

- [x] Audit `ci.yml`: *(already PR-ready — no changes needed)*
  - [x] Triggers include `pull_request` (in addition to whatever push-based trigger exists today) *(already triggers on `push: [main, develop]` + `pull_request: [main]`)*
  - [x] Exit codes propagate: no `continue-on-error: true` on lint or test steps *(grep-verified: zero `continue-on-error` lines in any workflow file)*
  - [x] Both lint (`ruff check`) and tests (`pyve test` or equivalent) are mandatory *(both `ruff check`, `mypy`, and `pytest` run as separate hard-failing steps; the only soft step is `codecov-action` with `fail_ci_if_error: false`, which is intentional — codecov outages shouldn't fail PR CI)*
- [x] Audit `test.yml` (multi-platform matrix): *(already PR-ready — no changes needed)*
  - [x] Triggers include `pull_request` *(already triggers on `push: [main, develop]` + `pull_request: [main]` + weekly cron)*
  - [x] All matrix legs are required (no `continue-on-error` shortcuts) *(3 OSes × 3 Python versions = 9 mandatory legs; `fail-fast: false` is set so legs run independently but each is still required)*
- [x] Document the green-CI expectation in `CONTRIBUTING.md` (cross-reference from P.f) — informal until branch protection is enabled *(already in `CONTRIBUTING.md` line 107: "All checks must be green before review", added in P.f)*

### Story P.i: v2.6.0 Doc updates and release bundling [Done]

Doc-only release bundling story for Phase P. Updates the spec artifacts, README, and `project-essentials.md` to reflect the new auto-heal flow, the inverted gitignore policy, the IDE-LLM-visibility constraint that forces `go.md` to remain tracked, and the new production-hardening files. Bumps the package to **v2.6.0** and seeds a `## [2.6.0]` CHANGELOG entry. **This story owns the single Phase P version bump per the phase-bundling rule in Version Cadence.**

- [x] Update `docs/specs/features.md`:
  - [x] Add a new functional requirement section for `heal` (FR-14 or next available) *(added FR-14: Auto-Heal & Self-Repair Install — covers the heal command, auto-hook, recursion guard, inverted gitignore, IDE-LLM-visibility constraint)*
  - [x] Update `## Inputs / Command Line` to add `project-guide heal` with its options (`--no-input`)
  - [x] Update `## Outputs / File Structure` to reflect that only `go.md` is tracked in consumer repos
  - [x] Update FR-8 (`--no-input` / CI Mode) to add `heal` to the list of commands that respect the contract
  - [x] Update Acceptance Criteria — add criteria for auto-heal silent-when-clean and auto-yes-with-stderr-notice *(added items 15 and 16)*
- [x] Update `docs/specs/tech-spec.md`:
  - [x] Add `heal` to the CLI Design / Commands table *(also added `archive-stories` and `bump-version` which were missing)*
  - [x] Add the auto-hook + recursion-guard mechanism under Cross-Cutting Concerns
  - [x] Update `## .gitignore Management` block to the new policy (single `!docs/project-guide/go.md` exception) *(plus rationale for the IDE-LLM-visibility constraint and the existing-block detection contract)*
  - [x] Update the "Nine intuitive commands" / "console script" verbiage if it appears *(grep-verified: only README had this phrasing; tech-spec.md never did)*
- [x] Update `README.md`:
  - [x] Line 39 — update CLI Interface count from "Nine" to "Ten" (or rephrase to drop the count) *(rephrased to drop the count entirely — current count is 11, future-proofed)*
  - [x] Line 91 — replace `The rendered go.md and .bak.*  backup files are gitignored.` with the corrected statement: `Everything under docs/project-guide/ is gitignored except go.md (which the LLM reads) and .bak.* backup files.`
  - [x] Add a `### heal` section to Command Reference (between `update` and `override`, or wherever fits the alphabetical/logical order)
  - [x] Update Quick Start step 1 "This creates" footnote to reflect the new tracked-vs-ignored policy
  - [x] Cross-reference `CONTRIBUTING.md` from the Contributing/Development sections *(done in P.f; verified)*
  - [x] Cross-reference `SECURITY.md` from a new "Security" section (or under the existing badge area) *(promoted from a single line under "Contributing" to a dedicated `## Security` section)*
- [x] Append to `docs/specs/project-essentials.md` (do not rewrite or reorder existing content):
  - [x] **Auto-heal hook contract** — every `project-guide` invocation calls `heal` first via a Click group-level callback; recursion guarded by `PROJECT_GUIDE_HEALING=1` env var; silent in steady state; missing `.project-guide.yml` is a hard error (not a heal opportunity)
  - [x] **Inverted gitignore policy** — only `go.md` is tracked under `target_dir`; everything else is bundled static data that `heal` repopulates on first post-clone invocation
  - [x] **IDE-LLM visibility constraint** — `go.md` must remain non-gitignored because IDE-integrated LLMs (Cursor, Claude Code, etc.) typically hide gitignored files from the LLM's view; the LLM's instruction to `Read docs/project-guide/go.md` requires the file to be visible. Repo-history value of `go.md` is incidental and the file churns on every mode switch — that churn is acceptable cost for LLM visibility
  - [x] **`heal` vs. `update` vs. `init`** — `init` is one-time bootstrap (writes `.project-guide.yml`), `update` refreshes files that exist on disk, `heal` is `update` plus create-missing and is the right command for fresh-clone-with-templates-gitignored
  - [x] **`--no-input` auto-yes for `heal`** — file writes under `--no-input` emit a one-line stderr notice (`Auto-healing N templates under --no-input.`) so CI logs and embedding callers have a visible signal
- [x] Bump `project_guide/version.py`: `__version__ = "2.6.0"`
- [x] Bump `pyproject.toml`: `version = "2.6.0"`
- [x] Add `## [2.6.0] - <date>` entry to `CHANGELOG.md` summarizing all of Phase P's user-visible changes (heal command, auto-hook, gitignore inversion, SECURITY.md, CONTRIBUTING.md, dependabot, CI tightening)

### Story P.j: v2.6.1 Drop redundant `.bak.*` line from canonical gitignore block [Done]

Tighten the canonical `# project-guide` gitignore block from four lines to three by removing the `<target>/**/*.bak.*` line — it is already covered by the broader `<target>/**` rule introduced in P.d. The fourth line was carried over from the pre-P.d block during the policy inversion and is functionally redundant under the new shape. **Existing installs are not at risk:** `_recognized_block_lines()` continues to recognize the old line, so `init --force` cleanly rewrites a v2.6.0-style 4-line block to the v2.6.1 3-line form.

- [x] In `project_guide/cli.py:_build_project_guide_block()`: remove the trailing `f"{target_dir}/**/*.bak.*\n"` line. New canonical form:
  ```
  # project-guide
  <target>/**
  !<target>/go.md
  ```
- [x] In `project_guide/cli.py:_recognized_block_lines()`: **keep** the `f"{target_dir}/**/*.bak.*"` entry in the recognized set so a v2.6.0-shipped 4-line block is treated as "ours" and rewritten on `init --force` rather than warned about as foreign.
- [x] In `tests/test_cli.py`:
  - [x] Update `_EXPECTED_GITIGNORE_BLOCK` to the 3-line form
  - [x] Update `test_init_force_rewrites_old_recognized_block_cleanly` to verify the test case where the prior block is the v2.6.0 4-line form (recognized → rewritten to 3-line) in addition to the existing legacy-`.bak.*`-only case *(split into two tests: `test_init_force_rewrites_legacy_bak_only_block_cleanly` for the pre-P.d shape and `test_init_force_rewrites_v260_four_line_block_to_three_lines` for the v2.6.0→v2.6.1 cleanup)*
  - [x] Update `test_init_with_existing_canonical_block_is_idempotent` so the seed block is the new 3-line form *(picked up via the `_EXPECTED_GITIGNORE_BLOCK` rebind)*
  - [x] All assertions that the `.bak.*` line is present should be removed
- [x] Doc updates (bundled in this story):
  - [x] `docs/specs/features.md`: update the Outputs / File Structure prose that currently lists `.bak.*` as a separate exception — the only tracked file under `target_dir` is `go.md`; `.bak.*` is just one of the many things subsumed by the broad `**` rule
  - [x] `docs/specs/tech-spec.md`: update the `## .gitignore Management` code block from 4 lines to 3, and refresh the surrounding prose
  - [x] `docs/specs/project-essentials.md`: amend the "Inverted gitignore policy" sub-section added in P.i to note the v2.6.1 simplification (the `.bak.*` line was redundant and was removed; existing v2.6.0 blocks heal on `init --force`)
  - [x] `README.md`: update the Quick Start step-1 footnote to drop the "and `.bak.*` backup files" callout — `.bak.*` is no longer a separate exception, just one of the things ignored by `<target>/**`
- [x] Bump `project_guide/version.py`: `__version__ = "2.6.1"`
- [x] Bump `pyproject.toml`: `version = "2.6.1"`
- [x] Add `## [2.6.1] - <date>` entry to `CHANGELOG.md` (this is a follow-up tightening of P.d; the v2.6.0 entry stays as historical record of what actually shipped, including the redundant line)

**Migration:** none required. Consumer repos running v2.6.0 see identical *behavior* under v2.6.1 (the gitignore semantics don't change — the redundant line was a no-op). Running `init --force` on a v2.6.0 install simply produces a tidier 3-line block. Consumers who never run `init --force` keep the 4-line block forever without issue.

### Story P.k: v2.7.0 `project-guide git-push` wrapper for gitbetter [Done]

Add a new `project-guide git-push [BRANCH_NAME]` command that auto-derives the commit message from the most-recently-completed-and-not-yet-committed story heading in `docs/specs/stories.md` and shells out to [gitbetter](https://github.com/pointmatic/gitbetter)'s `git-push` to perform the actual push. Collapses the developer's per-story commit step from "find the story ID, format the message correctly, type the command" to a single command, while delegating every actual git operation (preview, confirm, branch cleanup, reject/recovery menu) to gitbetter.

This is a developer-lane convenience command. **The LLM still does not initiate it** — the approval-gate discipline rule in `project-essentials.md` remains in force, and this story's doc updates reinforce that explicitly so future LLMs don't start offering `project-guide git-push` as a follow-up.

- [x] Story detection (`project_guide/stories.py` or a small new helper):
  - [x] Parse `docs/specs/stories.md` for the **last** `### Story <ID>: ... [Done]` heading in file order *(implemented as `_read_done_stories()` returning **all** `[Done]` headings; the "last" rule emerges naturally from the "0 / 1 / 2+ uncommitted" branch logic)*
  - [x] When no `[Done]` story exists, exit 1 with stderr `No completed story found in <stories.md>.`
  - [x] When `stories.md` is absent, exit 1 with stderr matching the existing `_read_stories_summary` no-stories behavior *(emits `Error: docs/specs/stories.md not found.`)*
- [x] Commit-message derivation:
  - [x] Input form: `### Story G.a: v1.2.3 New command \`foo\` with "Hello" [Done]`
  - [x] Output form: `G.a: v1.2.3 New command 'foo' with 'Hello'`
  - [x] Transformations: strip `### Story ` prefix, strip ` [Done]` suffix, replace each backtick with a single quote, replace each double quote with a single quote. Single quotes in the original heading pass through unchanged (no shell quoting concerns because the wrapper invokes gitbetter via `subprocess.run([...], shell=False)`)
  - [x] Preserve the colon after the story ID (matches the project's commit-message convention and is the anchor the already-committed check searches for)
- [x] Already-committed detection (Q5 → hard error):
  - [x] Run `git log --pretty=%s` and scan for a subject line whose prefix matches `<story_id>: ` (e.g., `G.a: `)
  - [x] If found, exit 1 with stderr `Story <ID> is already committed. Use 'git-push' directly for any follow-up commit.` — the developer resolves manually rather than the wrapper second-guessing
- [x] Multi-uncommitted-story detection (Q3 → hard error):
  - [x] If more than one `[Done]` story in the file has no matching `git log` subject, exit 1 with stderr listing the IDs and pointing the developer at raw `git-push` to commit them one at a time with explicit messages
- [x] gitbetter invocation:
  - [x] Detect `git-push` on PATH via `shutil.which("git-push")`; on miss, exit 1 with stderr `git-push not found on PATH. Install gitbetter: brew install pointmatic/tap/gitbetter`
  - [x] Build argv: `["git-push", message]` plus `[branch_name]` when provided
  - [x] `subprocess.run(argv, check=False)`; propagate the child's exit code unchanged so gitbetter's reject/recovery menu surfaces to the developer with its real exit semantics
- [x] CLI surface (`project_guide/cli.py`):
  - [x] New `@main.command(name="git-push")` with optional `BRANCH_NAME` positional
  - [x] No `--quiet` / `--no-input` plumbing — the wrapped command is fully interactive, so the flags would be no-ops
  - [x] Help text cites gitbetter, the brew install command, and the auto-message-derivation rules
- [x] Tests in `tests/test_cli.py`: 11 new tests under `--- Story P.k ---`. Covers happy path, branch-name passthrough, all heading transforms (plain, backticks-only, double-quotes-only, both, single-quote passthrough, no-version doc-only form), already-committed error, multi-uncommitted error, no-Done error, stories.md missing, `git-push` missing on PATH, and child-exit-code propagation.
- [x] Doc updates (bundled in this story per the version-bumping rule — code story owns its own doc churn):
  - [x] `docs/specs/features.md`: new functional requirement (FR-15 or next) for the wrapper; add to Inputs / Command Line; add an Acceptance Criteria item
  - [x] `docs/specs/tech-spec.md`: add `git-push` to the CLI Design / Commands table; document the `shutil.which` discovery + `subprocess.run` exit-code-propagation pattern under Cross-Cutting Concerns *(added as new "External CLI Dependencies (Story P.k pattern)" section so future wrappers follow the same shape)*
  - [x] `README.md`: new `### git-push` section in Command Reference between `update` (or `heal`) and `override`; make the gitbetter dependency clearly optional and link the install command
  - [x] `docs/specs/project-essentials.md`: append a sub-section covering (a) the message-derivation rules, (b) the **LLM-vs-developer-lane reminder** — `project-guide git-push` is invoked by the developer after the LLM presents a completed story; the LLM still does not initiate commits per the approval-gate discipline
- [x] Bump `project_guide/version.py`: `__version__ = "2.7.0"`
- [x] Bump `pyproject.toml`: `version = "2.7.0"`
- [x] Add `## [2.7.0] - <date>` CHANGELOG entry summarizing the new command and gitbetter integration

**Out of scope (revisit if demand):**
- Passthrough of gitbetter's other flags (`--amend`, `--keep`, `--force-with-lease`). The wrapper accepts only `BRANCH_NAME`; everything else routes through raw `git-push`.
- A parallel `project-guide git-tag` wrapper. gitbetter has one but the project's release process already uses `bump-version` + raw `git tag`, so the value is lower.
- Pre-flight `pyve test` / `ruff check` gates before invoking gitbetter. The developer runs those during the story's normal cycle before marking `[Done]`, so re-running them at push time is redundant.

### Story P.l: v2.7.1 Negation-free gitignore for IDE LLM compatibility [Done]

Switch the canonical `# project-guide` gitignore block from the v2.6.1/v2.7.0 negation form (`<target>/**` + `!<target>/go.md`) to a **negation-free explicit-list** form. Motivation: several IDE-integrated tools (Cursor, parts of the VS Code fork ecosystem, certain LSP-based search backends) implement a subset of `.gitignore` semantics that does not honor re-include negation — they apply the broad `**` rule, hide `go.md` from @-mention and fuzzy-search, and defeat the IDE-LLM-visibility constraint that's the entire reason `go.md` is tracked.

The new canonical form lists every gitignored top-level entry explicitly so no negation is required. The list is **dynamically generated** from the bundled template root, so new top-level files or subdirectories added in future stories are picked up automatically — no manual maintenance.

- [x] In `project_guide/cli.py:_build_project_guide_block()`: rewrite to enumerate `_get_package_template_dir()` and emit one `/<target>/<child>[/]` line per top-level entry except `go.md`, plus the existing `/<target>/**/*.bak.*` backup-catch-all. New canonical form for the default install layout:
  ```
  # project-guide
  /docs/project-guide/.metadata.yml
  /docs/project-guide/README.md
  /docs/project-guide/developer/
  /docs/project-guide/templates/
  /docs/project-guide/**/*.bak.*
  ```
  Use a leading slash to anchor each rule at repo root; trailing slash on directories. Children sorted for deterministic output.
- [x] In `project_guide/cli.py`: update the recognized-block check to accept every form we've ever written: *(replaced `_recognized_block_lines()` with a `_is_recognized_block_line(line, target_dir)` predicate — cleaner because the v2.7.1+ "anything anchored at `/<target>/`" rule isn't expressible as a fixed set)*
  - [x] New v2.7.1+ form: any line starting with `/<target>/`
  - [x] v2.6.1 form: `<target>/**`, `!<target>/go.md`
  - [x] v2.6.0 form: `<target>/**`, `!<target>/go.md`, `<target>/**/*.bak.*`
  - [x] pre-P.d form: `<target>/**/*.bak.*` only
  - [x] Legacy `<target>/go.md` line
- [x] In `tests/test_cli.py`:
  - [x] Compute the expected block from the bundled tree via `_expected_gitignore_block()` helper instead of a hardcoded constant
  - [x] Add `test_init_force_rewrites_v261_three_line_block_to_explicit_list` for the v2.6.1/v2.7.0 → v2.7.1 migration
  - [x] Renamed the v2.6.0 → v2.7.1 migration test to `test_init_force_rewrites_v260_four_line_block_to_explicit_list` (was the v2.6.1-form rewrite test)
  - [x] Foreign-block warning test updated to use a line not anchored at `/<target>/` so the new predicate flags it correctly
  - [x] Idempotency test passes against the new canonical form (the seed builds from `_expected_gitignore_block()`)
  - [x] All prior P.j/P.d migration tests continue to pass
- [x] Doc updates (bundled in this story):
  - [x] `docs/specs/features.md` FR-14: amended the "Inverted gitignore policy" paragraph with the three-version evolution (v2.6.0 → v2.6.1 → v2.7.1) and the IDE-compat rationale
  - [x] `docs/specs/tech-spec.md` § `.gitignore Management`: replaced the negation code block with the explicit-list form, added a "Why explicit list instead of `**` + `!go.md`?" paragraph plus an explicit "do not simplify back" warning, and a "Why the trailing `<target>/**/*.bak.*` line?" paragraph
  - [x] `docs/specs/project-essentials.md`: amended the "Inverted gitignore policy" sub-section to cover the v2.7.1 form change and the "future maintainers: do not simplify back to `**` + `!`" warning
  - [x] `README.md`: no user-facing prose changes needed (Quick Start footnote still reads correctly — "ignored except go.md")
- [x] Bump `project_guide/version.py`: `__version__ = "2.7.1"`
- [x] Bump `pyproject.toml`: `version = "2.7.1"`
- [x] Add `## [2.7.1] - <date>` CHANGELOG entry framed as a compatibility fix

**Migration:** none required by consumers. The new and old blocks produce identical git-tracking outcomes (only `go.md` is tracked). The behavior change is purely in what `_ensure_gitignore_entry()` writes. Existing v2.6.x/v2.7.0 installs heal to the v2.7.1 form on `init --force` because all prior shapes remain recognized. Consumers whose IDE handles negation correctly can keep their existing block indefinitely — only consumers hitting the IDE bug actually need to migrate.

**Why dynamic enumeration:** hardcoding the install footprint in `_build_project_guide_block()` means every new top-level template file or subdirectory requires a writer-code update. Enumerating `_get_package_template_dir()` at write time keeps the canonical block in sync with the bundled tree automatically. The trade-off is that the writer now reads from the package — not a real concern since `init` already does the same to copy the template tree.

**Out of scope:**
- An opt-back-in flag (`--gitignore-style=negation`). YAGNI until someone asks; the new form is strictly better for the documented IDE-LLM-visibility constraint.
- A `project-guide check` integrity rule that detects "consumer has tracked-but-should-be-ignored files under `target_dir`". Defer until there's a second integrity rule worth shipping (see Future > Integrity & Validation).

### Story P.m: v2.7.2 Recognize sub-numbered story IDs (`J.m.1`) in regex sites [Done]

Reported bug: in a consumer project with the heading sequence `… J.l [Done], J.m.1 [Done]`, `project-guide git-push` printed `"Story J.l is already committed. Use 'git-push' directly for any follow-up commit."` and refused to push, even though `J.m.1` was the actual just-completed story.

**Root cause:** three regexes encoded the story-ID shape as `[A-Z]\.[a-z]+`, which silently fails to match the sub-numbered form. `stories.py:_STORY_RE` was the proximate cause — `_read_done_stories()` filtered the `J.m.1` heading out entirely, leaving `J.l` as the "last `[Done]`," and the commit-subject check then correctly observed that `J.l` had been committed. The other two sites (`cli.py:_COMMIT_SUBJECT_STORY_ID_RE`, `actions.py:_VERSION_RE`) had the same hole and were fixed in the same story to avoid a half-fix where a future code path re-introduced the bug from a different angle.

**Sub-numbered form** — `<phase>.<letter>.<digit>+`, flat single-level only (no cascading like `J.m.1.1`). Two use cases per the developer's intent:

- **Pre-implementation split:** `J.m` is planned but its scope is judged too large before any work begins; the heading is split into `J.m.1`, `J.m.2` and the bare `J.m` heading is dropped. Sequence: `… J.l, J.m.1, J.m.2, J.n, …`.
- **Post-implementation follow-up:** `J.m` ships, then a bug or follow-on feature must land before proceeding to `J.n`; the follow-up is added as `J.m.1` (and may cascade to `J.m.2`, `J.m.3`, …). Sequence: `… J.l, J.m, J.m.1, J.m.2, …, J.n, …`.

Both scenarios are exercised by the new test suite.

- [x] `project_guide/stories.py:_STORY_RE` — extend capture group to `[A-Z]\.[a-z]+(?:\.\d+)?` with comment cross-referencing `_phase-letters.md`
- [x] `project_guide/cli.py:_COMMIT_SUBJECT_STORY_ID_RE` — matching extension; updated comment to reflect the new shape so future readers see why the two regexes must move together
- [x] `project_guide/actions.py:_VERSION_RE` — matching extension; `detect_latest_version()` now picks up versions on sub-numbered headings
- [x] `project_guide/templates/project-guide/templates/modes/_phase-letters.md` — new "Sub-numbered stories" subsection documenting both scenarios and the flat-only constraint
- [x] Ran `project-guide update` to propagate the template change into `docs/project-guide/templates/modes/_phase-letters.md` (installed copy)
- [x] New `tests/test_stories.py` — first direct unit-test coverage for `stories.py` (the gap that let the bug ship in P.k). Covers `_STORY_RE` matches (plain, sub-numbered, multi-digit sub-number), `_read_done_stories()` for both scenarios, `derive_commit_message()` with sub-numbered ID, and the round-trip through `cli._COMMIT_SUBJECT_STORY_ID_RE`
- [x] `tests/test_cli.py` — new cases for both `git-push` scenarios (post-impl follow-up; pre-impl split with no bare `J.m`) and the "sub-numbered story is already committed" path that surfaces the second-layer regex hole
- [x] `tests/test_actions.py` — new case asserting `detect_latest_version()` picks up the version on a sub-numbered heading
- [x] Bump `project_guide/version.py`: `__version__ = "2.7.2"`
- [x] Bump `pyproject.toml`: `version = "2.7.2"`
- [x] Add `## [2.7.2] - 2026-05-19` entry to `CHANGELOG.md` framed as a bug fix with test-coverage backfill

**Migration:** none. The change is purely permissive — existing plain-letter IDs (`J.l`, `J.m`) continue to match. Consumers who never used sub-numbered IDs see no behavior change; consumers who did will see `git-push` and `detect_latest_version()` start handling those headings correctly.

**Why the docs change rides this story:** the sub-numbered form was already in use by consumers but undocumented in `_phase-letters.md`. Extending the regex without documenting the form would leave the next maintainer staring at an unexplained `(?:\.\d+)?` tail. Doc + code travel together.

**Out of scope:**
- Multi-level cascading (`J.m.1.1`). The developer's intent is flat; YAGNI until a consumer asks. Adding it later is a strict superset (`(?:\.\d+)+` instead of `(?:\.\d+)?`) and would be backwards compatible.
- A `project-guide check` rule that warns when a sub-numbered ID appears without a preceding plain-letter heading in non-pre-split contexts. The two valid scenarios cover everything seen in the wild; defer until there's evidence of misuse.
- Sub-numbered phase letters (`AA.1`). Phases don't carry the same pre-impl-split / post-impl-followup workflow that motivates the story-level sub-numbering, and no consumer has asked.

---

### Story P.n: Scope-of-authority guardrail for cycle-mode templates [Done]

While drafting a Step-5 story in the `debug` cycle, the LLM created a new `## Phase Q: Generated artifact lifecycle` heading and theme paragraph in `docs/specs/stories.md` without authorization, then defended the choice as "a meaningful policy shift." The developer corrected: phase creation — the heading, the theme, the bundle of stories it owns — is the exclusive job of `plan_phase` (or `plan_production_phase` post-1.0). Cycle modes (`debug`, `code_direct`, `code_test_first`, `refactor_document`, `refactor_plan`) append stories under an **existing** phase only. This story bakes the boundary into the cycle-mode template instructions so the same drift cannot recur silently.

**Root cause:** the universal Rules block in `_header-common.md` covered approval-gate discipline, hand-edit safety, and copyright headers, but did not bound *structural* edits to `stories.md`. An LLM following the existing rules verbatim could still rationalize a new phase heading as "appropriate context for the work I'm documenting." The fix is to name the boundary explicitly and pair it with an escape valve (recommend `plan_phase`) so the LLM has a legitimate action to take when broader scope surfaces.

**Implementation:**

- [x] `project_guide/templates/project-guide/templates/modes/_header-common.md` — added a new bullet to the universal **Rules** block: explicit scope-of-authority statement covering structural changes to `stories.md`. May append stories under existing `## Phase <Letter>:` headings and edit existing story bodies; may **not** create new `## Phase` headings, re-theme existing phases, or move stories between phases. Phase creation is the exclusive job of `plan_phase` / `plan_production_phase`. When broader scope surfaces, recommend `plan_phase` at the approval gate; do not unilaterally start a new phase.
- [x] `project_guide/templates/project-guide/templates/modes/debug-mode.md` — added a "Scope reminder before you write" paragraph at Step 5, inline at the specific point where the LLM is most tempted to overstep (composing a new story for a discovered bug).
- [x] Ran `project-guide update` to propagate both template edits into the installed copy under `docs/project-guide/templates/modes/`.
- [x] Verified the rendered `docs/project-guide/go.md` includes the new Rules-block bullet and the Step-5 reminder.

**Why no per-mode reinforcement in the other cycle templates:** the other cycle modes (`code_direct`, `code_test_first`, `refactor_document`, `refactor_plan`) consume `[Planned]` stories rather than authoring new ones, so the universal `_header-common.md` rule covers them without needing inline reinforcement. The `debug` mode is unique in that Step 5 explicitly directs the LLM to write a new story — that's the temptation point where unilateral phase creation can occur, and where inline reinforcement adds real value. If field experience shows the other modes drift the same way, inline reinforcement can be added then.

**Version assignment:** doc-only template change. Per the Version Cadence rule (top of this file), doc-only stories do not bump for themselves — this story rides the next code-story release. No `project_guide/version.py`, `pyproject.toml`, or `CHANGELOG.md` change in this story.

**Migration:** none. The Rules-block addition affects only LLM behavior on subsequent mode invocations; consumers see the new wording on their next `project-guide mode <X>` render (or on the next auto-heal sync of the installed templates).

**Out of scope:**
- Inline scope-of-authority reinforcement in `code_direct`, `code_test_first`, `refactor_document`, `refactor_plan` templates. The universal `_header-common.md` rule covers them; defer per-mode reinforcement until evidence shows it's needed.
- Strengthening Step 5's authorship language ("you, the LLM, write this story yourself") and adding an Anti-Pattern entry for "Deferring the Gate Artifact to the Developer," plus a trigger for "prevention-scan discovery spawned a new cycle." These gaps were identified during this conversation but are a separate fix — they govern *who authors* the Step-5 artifact, not *what structural changes* are in-bounds. Scope as a follow-up story (likely P.q) if the developer agrees they are worth landing.
- Cross-cutting `features.md` / `tech-spec.md` scope rules (parallel to the `stories.md` rule). No drift observed; defer until one is.

---

### Story P.o: Untracked-by-default `go.md` policy [Done]

Reframe `go.md` from "the one tracked file under `target_dir`" to "unignored-but-untracked, regenerated on demand." The IDE-LLM-visibility constraint that drove the entire P.d → P.l line of work is about **gitignore status**, not **tracking status**: an unignored-but-untracked file is fully visible to IDE-integrated LLMs (Cursor, Claude Code, VS Code forks), while removing it from version control eliminates an entire class of dirty-working-tree failures during branch switches and post-merge cleanup.

**Found in the field** (consumer report from pyve): a `update/project-guide-v2.7.1` feature branch was pushed, the PR was merged on GitHub, and gitbetter's post-merge `git switch main` aborted with `error: The following untracked working tree files would be overwritten by checkout: docs/project-guide/go.md`. Diagnostics confirmed pyve's main tracked `go.md` (last touched in pyve's `322423d project-guide upgrade to v2.6.0`), the feature branch's tip did not (`git ls-files` empty for the path), and no gitignore rule matched (`git check-ignore` empty). The structural cause was the hybrid status — git's branch-switch safety check sees an untracked-unignored file in the working tree and refuses to overwrite it with main's tracked version. Re-rendering `go.md` from `.project-guide.yml:mode` in `heal` (a related architectural improvement) doesn't help here because git aborts *before* any `project-guide` command runs. Collapsing to untracked-by-default removes the conflict entirely: git doesn't gate `switch` on untracked-unignored files.

**Visibility vs. tracking — the key distinction:**
- **Gitignore status** governs IDE-LLM visibility. The constraint from P.d / the IDE-LLM-visibility section of `project-essentials.md` is: `go.md` must remain **non-gitignored** so Cursor / Claude Code / VS Code-fork LLM tooling can read it via `@-mention` and fuzzy-search. This story preserves that constraint unchanged — the v2.7.1 explicit-list gitignore block already leaves `go.md` un-listed (and therefore unignored).
- **Tracking status** governs version-control churn. The current "tracked by historical accident" state means `go.md` appears in every mode-switch diff, every cross-branch comparison, every merge resolution, and (as in the pyve case) every post-merge `git switch`. Untracking removes the churn without affecting visibility.

**Implementation:**

- [x] `project_guide/cli.py:heal` — added `_warn_if_go_md_tracked(config)` helper (called from both the heal command and the auto-hook). When `docs/project-guide/go.md` is in the consumer's git index, emits a single-line stderr warning with the copyable migration command:
  ```
  Warning: docs/project-guide/go.md is tracked. The current policy is untracked-by-default — run `git rm --cached docs/project-guide/go.md && git commit` once to migrate.
  ```
  - [x] Silent when go.md is untracked (steady state).
  - [x] Silent when the cwd is not a git repository (`git rev-parse --is-inside-work-tree` non-zero exit).
  - [x] Suppressed under `PROJECT_GUIDE_HEALING=1` (recursion guard).
  - [x] Suppressed under `--no-input` (via `should_skip_input()`).
  - [x] **Does NOT auto-run `git rm --cached`** — same wrapper-initiates-git-ops constraint that bounded the P.k `git-push` wrapper.
- [x] `project_guide/cli.py:init` — emits a single-line stderr note (`Note: docs/project-guide/go.md is intentionally untracked. Do not 'git add' it.`) after the initial render. Suppressed under `--quiet` / `--no-input`. *(also cleaned the `# noqa: F841` annotation from `skip_input` now that it's consumed)*
- [ ] Project-guide's own dogfooded repo: developer runs `git rm --cached docs/project-guide/go.md && git commit` on their own schedule per approval-gate discipline (the LLM does not initiate git operations).
- [x] Docs reshape:
  - [x] `docs/specs/project-essentials.md` — extended "IDE-LLM visibility constraint" and "Inverted gitignore policy" subsections with the v2.8.0 visibility-vs-tracking distinction.
  - [x] `docs/specs/features.md` — extended the FR-14 evolution narrative with the v2.8.0 tracking flip and migration command.
  - [x] `docs/specs/tech-spec.md` — added "Visibility vs. tracking" and "Why untracked-by-default?" paragraphs to `## .gitignore Management`, citing the pyve `git switch` incident.
  - [x] `README.md` — Quick Start now describes `go.md` as unignored-but-untracked and includes the consumer migration one-liner; `heal` command reference documents the tracked-`go.md` warning.
  - [x] `CHANGELOG.md` — `## [Unreleased]` entry with P.o-tagged Changed/Documented/Migration subsections (the unified `## [2.8.0]` entry is assembled by P.t at release time).
- [x] Tests:
  - [x] `tests/test_cli.py::test_init_emits_untracked_note_on_stderr`
  - [x] `tests/test_cli.py::test_init_quiet_suppresses_untracked_note`
  - [x] `tests/test_cli.py::test_init_no_input_suppresses_untracked_note`
  - [x] `tests/test_cli.py::test_heal_warns_when_go_md_is_tracked` — asserts copy-pasteable migration command verbatim
  - [x] `tests/test_cli.py::test_heal_silent_when_go_md_is_untracked`
  - [x] `tests/test_cli.py::test_heal_silent_when_not_in_git_repo`
  - [x] `tests/test_cli.py::test_heal_suppresses_warning_under_no_input`

**Version assignment:** P.o is the code-bearing story in the Phase P v2.8.0 release bundle. The version bump itself (`project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` entry) is owned by **P.t** — the bundled-release story for v2.8.0 — following the same single-story-owns-the-bump pattern used by P.i for v2.6.0. P.o's CHANGELOG bullet (consumer migration command, heal-warning text, etc.) lands inside the unified `## [2.8.0]` entry that P.t assembles.

**Migration:** consumers run `git rm --cached docs/project-guide/go.md && git commit` once on their default branch. The next `project-guide` invocation (auto-heal hook) regenerates `go.md` as an untracked-unignored working-tree file; IDE LLMs continue to see it; the cross-branch dirty-tree class of failures disappears. Consumers who don't migrate continue to function — `heal` warns on every invocation but doesn't error or refuse work; the cost is `go.md` keeps appearing in their working-tree diff on every mode switch.

**Why "warn-don't-auto-fix":** auto-running `git rm --cached` from inside `project-guide` would mutate the consumer's git index — the same wrapper-initiates-git-ops concern that constrained P.k's `git-push` to a thin gitbetter passthrough. Project-guide writes its own files (templates, `.project-guide.yml`, the gitignore block) but does not edit the consumer's index or HEAD. The warning surfaces the issue with a copyable command; the consumer decides when to apply it.

**Out of scope:**
- A dedicated `project-guide untrack-go-md` subcommand. YAGNI — the heal warning gives the consumer the exact command verbatim, and a dedicated subcommand would expand the wrapper-initiates-git-ops surface that the project has been deliberate about keeping narrow.
- A `project-guide check` integrity rule that flags tracked `go.md` as a defect with non-zero exit. Defer until the broader integrity-check surface is built (see Future > Integrity & Validation); the heal warning covers the same ground with a softer touch.
- Pre-flight on the `project-guide git-push` wrapper to detect dirty/untracked `go.md` before invoking gitbetter. The post-P.o steady state is "go.md is untracked-unignored on every branch" — branch switches no longer fail on it. If a pre-flight is still wanted after P.o ships and field-tests, scope it as a separate follow-up story.
- Backporting the new policy to v2.6.x or v2.7.x. Consumers on older project-guide versions stay on the historical tracked-`go.md` model; upgrading to v2.8.0 surfaces the heal warning and the README migration note.
- Changing the v2.7.1 explicit-list gitignore block. The block is unchanged — `go.md` is still un-listed and therefore unignored. Only tracking status flips.
- Applying the same untracked-by-default policy to other generated artifacts under `target_dir` (e.g., rendered mode files in `templates/`). Those are already gitignored under the v2.7.1 block, so the question doesn't arise; if a future artifact lands in the same "tracked + generated" hybrid as `go.md` is leaving, that would warrant its own story (and possibly a new phase via `plan_phase`).
- Heal-time re-render of `go.md` from `.project-guide.yml:mode`. Considered earlier in the same design conversation as a parallel resilience improvement (yml as single source of truth, `go.md` as derived cache, `heal` as the convergence operation), then deferred: the untracked-by-default policy obviates the proximate need because git no longer gates branch switches on the file, and the re-render approach doesn't address the cross-branch tracking-status mismatch that motivated this story. Revisit if field evidence after P.o ships shows that intra-branch drift (modes changed without committing the resulting `go.md` rendering) still creates UX friction; in that case, scope as a follow-up story to make `heal` re-render unconditionally when `.project-guide.yml:mode` exists and the on-disk render doesn't match.

---

### Story P.p: XP methodology grounding, three-flavor spike taxonomy, foundation-story reconciliation, and ID-insertion rules [Done]

Bundle four related doc-and-template reconciliations surfaced during the P.m → P.q design conversation. Each by itself is small; together they make project-guide's methodology explicit, name its terminology in line with industry conventions, and close three latent drifts that would have caused future confusion if left as-is.

**Four threads in scope:**

1. **XP methodology grounding.** Project-guide's core practices — cycle modes with approval gates, mandatory test-first in `debug`, single-story-per-commit discipline, the spike concept — are all rooted in Extreme Programming (Beck, 1999). Today this lineage is implicit. P.p makes it explicit with a citation block and a brief "Why XP for LLM-assisted development" framing, so future maintainers and consumers understand *why* these choices were made (not just *what* the rules are) and don't drift back to non-XP defaults when the rules feel inconvenient.

2. **Three-flavor spike taxonomy.** `best-practices-guide.md`'s "Hello World First — Spike Early, Spike Often" section currently documents only one flavor — what amounts to an *integration spike* under a generic name. Agile literature recognizes three structurally distinct flavors, each addressing a different kind of uncertainty: **integration spike** (will external systems connect end-to-end?), **architectural spike** (Beck's original — will this design or pattern work? what is the probability of implementation success?), **investigation spike** (is there a viable path at all? often produces no code). P.p expands the section to name all three, with each cited to its XP/Agile origin, and updates `_header-common.md` Rule 3 (drafted in P.q) to reference the unified definition.

3. **Foundation-story reconciliation.** Three docs currently disagree on the foundation-story structure:
   - `plan-stories-mode.md` (the active template): **3-story foundation** — A.a scaffolding, A.b "Hello World," A.c end-to-end stack spike.
   - `developer/best-practices-guide.md`: **2-story foundation, hello-world implicit** — A.a scaffolding, A.b first spike (section title says "Hello World First" but the placement collapses hello-world into the spike).
   - `developer/project-guide.md`: **2-story foundation, A.a renamed** — A.a "Hello World," A.b end-to-end stack spike (no separate scaffolding story).
   P.p makes the 3-story `plan-stories-mode.md` convention canonical (it's the actively-walked template, and the three concerns — package wiring, runtime self-proof, integration self-proof — are genuinely distinct), and reconciles the other two docs to match.

4. **ID-insertion rules in `_phase-letters.md`.** Today the file covers sub-numbered stories (`J.m.1`, added in P.m) and base-26 phase letters but does not document the general algorithm for inserting a new story when prior stories already exist. P.p adds an "Inserting a new story" subsection covering three insertion options: **append** (default: next sequential ID at top level), **sub-number extension** (next `<parent>.N` when the new work is conceptually a follow-up), **renumber (last resort)** (insert at an existing position, shift later IDs +1, update all references). Reaffirms the 3-level depth limit explicitly.

**Why bundle these four:** they share two common properties — (a) every change is doc-or-template-only, no Python source code touched; (b) they all close ambiguity that affects how future LLMs read the docs and behave. Bundling them lets a single doc-only PR or commit batch reshape the methodology vocabulary coherently, rather than four trickling PRs that each leave parts of the doc tree inconsistent with the others. Anything that doesn't share both properties is out of scope (see below).

**Implementation:**

- [x] `project_guide/templates/project-guide/developer/best-practices-guide.md` — added new top-level section **"Methodology — Extreme Programming (XP)"** with three subsections (Lineage, Why XP fits LLM-assisted development, References — Beck 1999/2004 and Jeffries/Anderson/Hendrickson 2000).
- [x] `project_guide/templates/project-guide/developer/best-practices-guide.md` — reworked the "Hello World First — Spike Early, Spike Often" section to anchor in XP and document three flavors (Integration / Architectural / Investigation), each with question-answered framing, triggers, and output. Replaced the implicit "first spike (A.b)" placement language with explicit A.c placement, and added a closing "Foundation-story structure" subsection that names the 3-story foundation (A.a scaffolding / A.b hello world / A.c integration spike) as canonical.
- [x] `project_guide/templates/project-guide/developer/project-guide.md` — rewrote the planning-rules foundation-stories bullets to match the 3-story foundation (A.a scaffolding, A.b hello world, A.c integration spike). Updated the cross-reference to point at the v2-path `docs/project-guide/developer/best-practices-guide.md` (was pointing at the legacy v1 `docs/guides/...` path). Also updated Step 4's "Start with Story A.a" line — A.a is now Scaffolding (executed in `scaffold_project`), not Hello World.
- [x] `project_guide/templates/project-guide/templates/modes/plan-stories-mode.md` — renamed "end-to-end stack spike" → "integration spike" on the A.c line and in the Recommended Phase Progression table. Added a cross-reference to `best-practices-guide.md` for the three-flavor taxonomy.
- [x] `project_guide/templates/project-guide/templates/modes/plan-phase-mode.md` — clarified that the phase-spike means an *integration spike* with cross-reference to `best-practices-guide.md`; architectural and investigation spikes enter the sequence ad-hoc.
- [x] `project_guide/templates/project-guide/templates/modes/plan-production-phase-mode.md` — same fix as `plan-phase-mode.md`.
- [x] `project_guide/templates/project-guide/templates/modes/_phase-letters.md` — added a new **"Inserting a new story"** subsection between "Sub-numbered stories" and "Continuing across archive boundaries." Documents the three insertion options (Append default / Sub-number extension / Renumber last-resort), restates the 3-level depth limit (flat single-level only), and includes both precision rules from the P.s bug-triage conversation: Sub-number is valid only when the parent is the latest top-level ID committed under its phase, and Renumber is valid only on working-tree-only IDs (committed IDs are locked, verified via `git log -- docs/specs/stories.md`).
- [x] Ran `pyve run project-guide update` to propagate all six template edits into `docs/project-guide/`.
- [x] Verified the rendered `docs/project-guide/go.md` under `plan_phase` mode contains the new "Inserting a new story" subsection and the integration-spike terminology with cross-reference. (Mode restored to `code_direct` for ongoing work.)
- [x] Flipped this story's status to `[Done]` and all checklist items to `[x]`.

**Version assignment:** doc-only template change. Per Version Cadence, doc-only stories do not bump for themselves; P.p rides the next code-story release. No `project_guide/version.py`, `pyproject.toml`, or `CHANGELOG.md` change in this story.

**Migration:** none required by consumers. The terminology rename ("end-to-end stack spike" → "integration spike") is purely textual; no code path depends on the old phrase. Foundation-story structure has been *already* canonical in `plan-stories-mode.md` for some time; P.p only reconciles the prose docs (`best-practices-guide.md`, `developer/project-guide.md`) to match what the active template already produces. Consumers on existing project-guide versions see the new terminology and reconciled prose on next `project-guide update`.

**Dependency note:** P.p's expanded spike section satisfies the forward reference in P.q's Rule 3 (Rules block in `_header-common.md`). If P.q ships before P.p, the reference is still valid (section exists) but the readers of P.q see only one spike flavor documented at the destination. **Cleanest implementation order: P.p before P.q** — story IDs are aligned to this order, so a sequential walk of Phase P from `P.o` onward implements correctly without reordering.

**Out of scope:**
- **A `project-guide renumber-story <old-id> <new-id>` CLI helper** for the rare last-resort renumber-insertion case. YAGNI — manual renumber is straightforward when needed, and a CLI helper that has to track every cross-doc reference (CHANGELOG, commit messages, in-body story refs) is a non-trivial build. Defer until renumbering happens routinely enough to justify the surface area.
- **Per-mode inline spike-vocabulary reinforcement** in cycle templates (`code_direct`, `code_test_first`, `refactor_*`). The universal definition in `best-practices-guide.md` plus the `_header-common.md` Rule 3 reference are sufficient; defer per-mode reinforcement until evidence shows it's needed.
- **Backporting spike-flavor terminology to archived stories** under `docs/specs/.archive/stories-vX.Y.Z.md`. Archives are a historical record; leave the old "end-to-end stack spike" / generic-spike language as-is. New work uses the new vocabulary.
- **A separate `_spike.md` template include** with hypothesis / steps / outcome structure. Light-touch definition in `best-practices-guide.md` is sufficient for now; if spikes become routine enough to need structural template support, scope as a follow-up.
- **Deeper-than-3-level story IDs** (`A.b.1.1`). Already out of scope in P.m; restated here for the insertion-rules subsection.
- **Renaming "Hello World" or "scaffolding"**. Both terms are industry-standard and canonical to project-guide's foundation-story structure; no renaming proposed.
- **Adding "architectural spike" or "investigation spike" as new default foundation stories** in the recommended phase progression. They are ad-hoc spike flavors used when warranted (per-cycle, per-decision), not required slots in every phase. The default foundation stays 3-story (scaffolding / hello world / integration spike); other spike flavors enter the story sequence on an as-needed basis.

---

### Story P.q: LLM workflow discipline — documentation timing, spike-awareness, gate handoff [Done]

Bake four cross-cutting workflow rules into the universal Rules block of `_header-common.md` so every rendered `go.md` carries them, and reinforce the rules that hit hardest at `debug`-mode's Step 5 with inline guidance plus a new anti-pattern entry. The rules address structural LLM failure modes observed in this conversation and in prior cycles: undocumented work, off-by-one story numbering when work is paused/resumed, conflation of documentation with implementation, deferral of the gate artifact to the developer.

**Failure mode this story closes:** in a prior turn, the LLM (this assistant) made template changes after misreading "go" as approval for a recommendation rather than as a directive to implement the planned story. The work was completed without a story; at the approval gate, the LLM asked the developer how to wrap it instead of writing the story itself. The developer correctly named both the immediate fix (renumber + insert) and the structural gap (the templates don't tell the LLM *who* writes the Step-5 artifact). P.q installs the missing rules at the template level so the next LLM in this situation just knows what to do.

**The four rules** (full text lands in `_header-common.md` Rules block; summary here for the story record):

1. **Sequential, story-by-story documentation.** Every chunk of LLM-produced work that lands in the repo (code, tests, docs, templates) is captured as a story in `stories.md` under the existing phase, in the order performed. One coherent unit of work → one story → one developer commit.
2. **Documentation timing.** Default: write the story with its `[ ]` checklist → execute → flip to `[x]` → present at the gate. Exception for `debug` mode: when the root cause is unknown until exploration, the legitimate sequence is explore → reproduce → small-scope fix → write the story (Step 5). Either way, **the story exists on disk by the time the cycle reaches its approval gate.**
3. **Spikes for uncertainty reduction.** When the path forward is uncertain, document the work as a spike — a time-boxed throwaway effort whose deliverable is a documented outcome. Three flavors recognized (integration / architectural / investigation); full definitions in `developer/best-practices-guide.md`'s "Hello World First — Spike Early, Spike Often" section. *(P.p lands the three-flavor expansion at that destination; P.q's Rule 3 forward-references the section, which already exists.)*
4. **Approval-gate documentation handoff.** Every gate presents (a) a story reflecting current completion state (`[x]` done, `[ ]` outstanding, one-line note on in-progress items) alongside (b) the files changed. If you enter a gate with undocumented work, write or update the story *before* pausing. The developer returns distracted; the handoff names what's done, what's next, what decision is being asked for.

**Implementation:**

- [x] `project_guide/templates/project-guide/templates/modes/_header-common.md` — added four new bullets to the Rules block, immediately after the P.n "Scope of authority" bullet, in bold-leading-title style: (1) **Sequential, story-by-story documentation**, (2) **Documentation timing** (default + `debug` exception, on-disk-before-gate invariant), (3) **Spikes for uncertainty reduction** (forward-references the three-flavor taxonomy that P.p expanded in `developer/best-practices-guide.md`), (4) **Approval-gate documentation handoff** (story + files-changed presented together; story authored before pausing, not after the developer asks).
- [x] `project_guide/templates/project-guide/templates/modes/debug-mode.md` Step 5 — added the "Documentation timing in `debug`" paragraph after the P.n "Scope reminder before you write" paragraph and before "(a) The story write-up." Names the explore→reproduce→fix→write sequence as the one legitimate exception to the universal timing rule, reinforces the on-disk invariant, and states explicitly that the LLM authors the story (no asking the developer how to wrap it).
- [x] `project_guide/templates/project-guide/templates/modes/debug-mode.md` Anti-Patterns section — added the new **"Deferring the Gate Artifact to the Developer"** entry as a sibling to "Declaring the Fix Complete After Step 4." Names both shapes of the failure (asking the developer how to story-ize the work; asking permission to author the story) and points the solution at Rule 4 plus the `_phase-letters.md` "Inserting a new story" rules from P.p.
- [x] Ran `pyve run project-guide update` to propagate both template edits into `docs/project-guide/templates/modes/`.
- [x] Verified rendered `docs/project-guide/go.md` (under `debug` mode) contains all four new universal Rules-block bullets (lines 37–40), the new Step-5 "Documentation timing in `debug`" paragraph (line 434), and the new "Deferring the Gate Artifact to the Developer" anti-pattern (lines 716–720). Mode restored to `code_direct` for ongoing work.
- [x] Flipped this story's status to `[Done]` and all checklist items to `[x]`.

**Version assignment:** doc-only template change. Per Version Cadence, doc-only stories do not bump for themselves; P.q rides the next code-story release. No `project_guide/version.py`, `pyproject.toml`, or `CHANGELOG.md` change in this story.

**Migration:** none. The new Rules-block bullets affect LLM behavior on the next `project-guide mode <X>` render or the next auto-heal sync of installed templates. Existing consumers see the new wording without any consumer-side action.

**Out of scope:**
- **The XP methodology grounding and the three-spike-flavor expansion in `developer/best-practices-guide.md`.** Scoped as P.p so the cycle-mode discipline rules (P.q) and the foundation-terminology reconciliation (P.p) can be reviewed and committed independently.
- **Inline reinforcement of Rules 1–4 in `code_direct`, `code_test_first`, `refactor_document`, `refactor_plan` mode templates.** The universal `_header-common.md` rule covers them; defer per-mode reinforcement until evidence shows it's needed.
- **Tooling helper to detect "approval gate reached without story update"** (e.g., a `project-guide check` rule). Defer until the broader integrity-check surface is built.

---

### Story P.r: LLM response framing — mode echo and step contextualization [Done]

Two complementary rules for how the LLM frames its responses in any project-guide-powered repo, addressing two friction points observed during dogfooding:

1. **Mode is sometimes unclear at the top of the LLM's response.** Some modes' rendered `go.md` doesn't prompt the LLM to announce the active mode on its first response after the developer says "read `docs/project-guide/go.md`". When the mode is wrong (developer intended a different one), the absence of a clear mode echo turns a one-line correction into multiple lost turns. Some modes already do echo; convention is currently inconsistent across the mode template set.

2. **Naked step references confuse the developer.** "Step 2" alone means nothing unless the developer happens to remember the cycle's step list (which is the LLM's responsibility, not the developer's). Coupling the step number with its name on first mention in a response — "Step 2 (announce the next story)" — makes the workflow self-explanatory for the developer skim-reading at a glance.

**Implementation:**

- [x] `project_guide/templates/project-guide/templates/modes/_header-common.md` — extended the "After reading, the LLM will respond:" protocol to four numbered lines, with `**First line, always:** "Mode: {% raw %}{{ mode_name }}{% endraw %}."` as the new always-first item. No "if the mode looks wrong, say so" qualifier — the LLM just emits the signal, per the deliberate out-of-scope rejection.
- [x] `project_guide/templates/project-guide/templates/modes/_header-common.md` Rules block — added the **"Step references include the step's name on first mention in a response"** bullet near the other response-framing rules (right after "If the next action is unclear", before "Never auto-advance past an approval gate"). Bullet text matches the story spec verbatim.
- [x] Audited the cycle-mode template set (`_header-cycle.md`, `_header-sequence.md`, `code-direct-mode.md`, `code-test-first-mode.md`, `debug-mode.md`, `refactor-document-mode.md`, `refactor-plan-mode.md`, `default-mode.md`) — no per-mode mode-announce / "first response" / "say the mode" language exists in any of them. `_header-common.md` is already the sole source for the response protocol. No reconciliation edits required.
- [x] Ran `pyve run project-guide update` to propagate the `_header-common.md` edits.
- [x] Verified the rendered `docs/project-guide/go.md` for both `code_direct` and `debug` modes — each shows the four-line "After reading" protocol with the correct mode-name interpolation (`Mode: code_direct.` / `Mode: debug.`) at line 15, and the step-name Rules-block bullet at line 35. Mode restored to `code_direct`.
- [x] Flipped this story's status to `[Done]` and all checklist items to `[x]`.

**Version assignment:** template change (code abstracted into text — see P.t's principle note). Rides P.t's bundled v2.8.0 release; no per-story version bump.

**Migration:** none required by consumers. Behavior change is purely in LLM response framing on next mode invocation. Existing consumers see the new conventions on next `project-guide update` or auto-heal sync.

**Out of scope:**
- **"If the mode looks wrong, say so"** qualifier in the mode-echo rule. Considered and rejected: corrections are the developer's job, the LLM just provides the signal; LLM-as-supervisor adds friction without adding signal.
- **A `project-guide check` rule** verifying that LLM responses in project-guide-powered repos actually follow these conventions. Out of scope here; defer until the broader integrity-check surface is built. This story addresses the prescriptive side only.
- **Step-reference contextualization in *generated artifacts*** (CHANGELOG entries, commit messages, story bodies). The rule applies to LLM-to-developer responses; if generated artifacts also benefit, scope as a follow-up story.
- **Echoing additional context** (e.g., current phase, version, last `[Done]` story) on the first response. Out of scope here; the mode echo is sufficient signal for the immediate friction observed.

---

### Story P.s: Recognize "Story " prefix in commit-subject regex [Done]

**Bug report from the field** (consumer repo running project-guide v2.7.2):

```
% project-guide git-push
Multiple uncommitted [Done] stories: J.m.2, J.m.3. Use 'git-push' directly to commit them one at a time with explicit messages.

% git log
commit 1323a8b... Story J.m.2: v0.71.0 — 'QuizProvider' Protocol → 'AssessmentProvider' + Parameter Rename
commit 5abf42a... J.m.1: v0.70.0 — Integrate Published '@pointmatic/quizazz' SvelteKit Component, Retire Local Placeholder
```

J.m.2 *is* committed (visible in `git log`), but the wrapper claims it isn't and refuses to push.

**Root cause.** The wrapper's commit-subject regex at `project_guide/cli.py:_COMMIT_SUBJECT_STORY_ID_RE` is `^([A-Z]\.[a-z]+(?:\.\d+)?):\s` — it requires the commit subject to start with the bare story ID. The two field commits use different conventions:

- `J.m.1: v0.70.0 — Integrate Published ...` — bare prefix → regex matches → recognized as committed ✓
- `Story J.m.2: v0.71.0 — 'QuizProvider' ...` — `"Story "` prefix → regex does **not** match → NOT recognized ✗

`_get_committed_story_ids()` returns `{J.m.1}` instead of `{J.m.1, J.m.2}`, so the wrapper concludes both J.m.2 and the next `[Done]` (J.m.3) are uncommitted and bails with the "Multiple uncommitted" error.

**Wider inconsistency (resolved as part of this fix).** `derive_commit_message` emits output *without* the `"Story "` prefix (`<id>: <title>`), but project-guide's own `project-essentials.md` Commit-workflow section shows examples *with* the prefix (`"Story M.a: v2.3.0 ..."`). Developers following the docs convention with raw `git commit` produce subjects the wrapper can't recognize. Resolution per the bug-triage conversation: **Option 3 — permissive regex + concise/bare-form docs examples**. Wrapper output unchanged (still bare); regex accepts both forms for historical-mix compatibility; docs examples updated to bare form so the canonical convention is unambiguous going forward.

**Why bare form is the canonical convention.** Concise. Matches what the wrapper produces. The `"Story "` prefix doesn't add information that the `<id>:` anchor doesn't already convey, and "Story" is implicit context — every commit referencing a story ID is by definition a story commit.

**Fix design:**

```python
_COMMIT_SUBJECT_STORY_ID_RE = re.compile(r"^(?:Story\s+)?([A-Z]\.[a-z]+(?:\.\d+)?):\s")
```

The non-capturing `(?:Story\s+)?` consumes an optional `"Story "` prefix without altering the captured story-ID group. Existing tests on the bare form continue to pass; new tests cover the `"Story "`-prefixed form.

**Implementation:**

- [x] Added 4 new tests in `tests/test_cli.py` under `--- Story P.s ---`: `Story <id>:` form matches (`test_commit_subject_regex_matches_story_prefix_form`), bare `<id>:` form continues to match (`test_commit_subject_regex_matches_bare_form`), both forms work for plain-letter IDs (`..._matches_plain_letter_id_both_forms`), and `Fix `/`Feat ` prefixes are *not* absorbed (`..._rejects_other_prefixes` — pins the regex's permissive scope to `Story ` specifically). Confirmed the two `Story `-prefix tests fail before the fix and pass after.
- [x] Updated `project_guide/cli.py:_COMMIT_SUBJECT_STORY_ID_RE` to `re.compile(r"^(?:Story\s+)?([A-Z]\.[a-z]+(?:\.\d+)?):\s")`. Replaced the comment block with the dual-form rationale (bare canonical, `Story ` legacy) and a back-reference to the P.s field bug.
- [x] Confirmed full test suite green (`pyve test` → 532 passed; up from 528 by the 4 new tests) and `ruff check project_guide/ tests/` clean.
- [x] Reconciled commit-message examples to bare `<id>: <title>` form across the source templates and the project's own `project-essentials.md`:
  - `docs/specs/project-essentials.md` (this repo's own project-essentials, not the artifact template) — Commit-workflow subsection: M.a / M.c examples flipped to bare; added a sentence naming bare as canonical and citing P.s for the regex's dual-form tolerance.
  - `project_guide/templates/project-guide/templates/modes/code-direct-mode.md` — Velocity-mode commit-message example flipped to bare with cross-reference to `project-essentials.md`.
  - `project_guide/templates/project-guide/developer/best-practices-guide.md` — three Commit-messages examples flipped to bare (A.a velocity, J.c production, H.d version-control).
  - `project_guide/templates/project-guide/developer/production-github-guide.md` — `git commit -m` example and `gh pr create --title` example flipped to bare; rewrote the "Commit message format" guidance bullet to name bare as canonical and acknowledge the regex's backward-compatible `Story ` tolerance.
  - **Bundled artifact template** `templates/artifacts/project-essentials.md` confirmed *not* to contain commit-message examples (the field-bug examples lived in this project's own `project-essentials.md`, not in the artifact scaffolding shipped to consumers).
- [x] Ran `pyve run project-guide update` to propagate the template-source edits into `docs/project-guide/`.
- [x] Flipped this story's status to `[Done]` and all checklist items to `[x]`.

**Version assignment:** patch-level regex bug fix; rides P.t's v2.8.0 bundled release. No standalone version bump in this story.

**Migration:** none. The permissive regex retains backward compatibility with the bare form (historical wrapper output and direct developer use) and adds forward compatibility with the `"Story "` prefix form (legacy hand-typed style). Consumers with mixed history get coherent recognition automatically on upgrade to v2.8.0.

**Out of scope:**
- **Updating `derive_commit_message` to emit the `"Story "` prefix.** Considered (Option 2 in triage) and rejected: docs examples are being aligned *to* the bare form, not away from it; changing the wrapper's emitted format would also require updating the P.k test pinning and would propagate a longer prefix into every wrapper-generated commit.
- **A `project-guide check` integrity rule** verifying that every `[Done]` story in `stories.md` has a matching commit-subject parse under the regex. Defer until the broader integrity-check surface exists; the wrapper's own error message already surfaces this kind of mismatch interactively.
- **Backporting the regex fix to v2.7.x as a patch release.** Consumers stay on v2.7.2 until v2.8.0 ships; bundling under P.t avoids a stand-alone v2.7.3 release that would only contain this one regex tweak.
- **Auto-detecting and warning when an existing repo's commit history contains a mix of `"Story <id>:"` and bare `"<id>:"` subjects.** The mix is benign under the permissive regex; no warning needed.

---

### Story P.t: v2.8.0 Refactor mode story authoring and bundled release [Done]

**Placeholder ID convention.** `P.t` is a placeholder, deliberately drafted at the end of Phase P's alphabet so it stays out of the way of in-flight work. At release time the developer renumbers this story to whatever the next sequential letter is in Phase P (likely `P.s` or `P.t` after P.o/P.p/P.q/P.r ship) so the final on-disk record matches Rule 1's "in the order performed" invariant.

**Principle: template changes are not doc-only.** A template under `project_guide/templates/` is **code abstracted into text** — it ships inside the Python package, gets rendered into the consumer's `go.md` on `project-guide init`/`update`/`mode`, and changes the LLM's runtime behavior on the next mode invocation. To reach consumers it must be published to PyPI, which requires a release tag. Therefore template-touching stories cannot follow the "doc-only stories don't bump for themselves" rule literally; they must ride a versioned release. The cleanest pattern (mirroring P.i's role for v2.6.0) is to bundle every template/code story since the previous release under a single bundled-release story (this one) that owns the version bump and assembles a unified CHANGELOG entry.

**What this story does.** Phase P bundled release at **v2.8.0**, owning the single version bump and the unified CHANGELOG entry for every Phase P story shipping since v2.7.2 (P.m). Includes one minor-behavior code story (P.o) plus four template/doc stories (P.n, P.p, P.q, P.r). Per Version Cadence: bump magnitude is determined by the highest-impact change in the bundle — P.o adds new consumer-visible behavior (heal warning + init note + the consumer-side `git rm --cached` migration), so the bundle is a **minor** bump (v2.7.2 → v2.8.0).

**Stories bundled** (verified at release time; adjust the list to whatever has actually shipped to `[Done]` status by then):
- P.n `[Done]` — Scope-of-authority guardrail for cycle-mode templates (template change)
- P.o — Untracked-by-default `go.md` policy (code: heal warning, init note, tests; consumer migration)
- P.p — XP methodology grounding, three-flavor spike taxonomy, foundation-story reconciliation, ID-insertion rules (template/doc change)
- P.q — LLM workflow discipline (documentation timing, spike-awareness, gate handoff) (template change)
- P.r — LLM response framing rules (mode echo + step contextualization) (template change)
- P.s — Recognize "Story " prefix in commit-subject regex (code: regex + tests; template: bare-form docs examples)

**Implementation:**

Pre-release content tasks (folded in at the developer's request during the announce of this story):

- [x] **Foundation-reconciliation cleanup** — rewrote the "Story Ordering" bullet at `code-direct-mode.md:39` from the stale `"Start with Story A.a (Hello World)"` to a 3-story foundation summary (A.a Scaffolding / A.b Hello World / A.c integration spike) with cross-reference to `best-practices-guide.md` § "Hello World First — Spike Early, Spike Often." Confirmed no parallel issues exist in `code-test-first-mode.md` (no foundation language), `debug-mode.md`, `default-mode.md`, or the `developer/` guides (already reconciled by P.p).
- [x] **Mode-template audit vs. new universal rules** — reviewed every cycle-mode and planning-mode template against P.n/P.q/P.r's universal rules. Findings:
  - **Per-mode "Do not propose commits…" reinforcements** at `code-direct-mode.md` Step 10 and `code-test-first-mode.md` Step 9 duplicate `_header-common.md` Rule 5 in spirit, but are deliberate per-step emphasis at the highest-temptation moment (parallels P.q's debug-mode inline reinforcement pattern). Not redundancy in the bad sense; **left as-is**.
  - **No conflicts found** between any per-mode template and the new universal rules. The P.p terminology rename ("end-to-end stack spike" → "integration spike") had already reconciled the planning-mode cross-references; the P.n scope-of-authority guardrail had already been reinforced inline at debug-mode Step 5.
  - **Ambiguity flagged at the approval gate (not fixed unilaterally):** `refactor-plan-mode.md` and `refactor-document-mode.md` do not currently author `stories.md` entries per-cycle, which is in tension with P.q Rule 1 ("every chunk of LLM-produced work is captured as a story"). The historical refactor convention has been that the rewrite session documents itself in the rewritten artifacts. Resolving this is a methodology decision beyond P.t's bundled-release scope; **flagging for the developer**.

Release bundling tasks:

- [x] Verified all six bundled stories are `[Done]` on disk: P.n, P.o, P.p, P.q, P.r, P.s (P.t self-completes).
- [x] Bumped `project_guide/version.py`: `__version__ = "2.8.0"`
- [x] Bumped `pyproject.toml`: `version = "2.8.0"`
- [x] Added unified `## [2.8.0] - 2026-05-19` entry to `CHANGELOG.md` with the recommended structure: opening paragraph naming the Phase P closing-bundle theme, `### Changed` / `### Added` / `### Fixed` subsections crediting each bundled story by ID (P.n–P.t), and a `### Migration` subsection with the one-line P.o consumer command. Consolidated the previously P.o-tagged content from `## [Unreleased]`; `[Unreleased]` is now empty.
- [x] Ran `pyve run project-guide update` to propagate the foundation-cleanup edit (one source template) into `docs/project-guide/`.
- [x] Ran full test suite + lint sweep: `pyve test` → **532 passed**; `ruff check project_guide/ tests/` → **All checks passed**.

Folded-in audit follow-up (developer-directed Path 2, after the initial gate presentation):

- [x] **Refactor modes now author session-level stories** — resolved the ambiguity flagged at the initial gate by updating both refactor cycle templates to bring them inside P.q Rule 1's "every chunk of LLM-produced work is captured as a story" invariant:
  - `project_guide/templates/project-guide/templates/modes/refactor-plan-mode.md` — new **Session Story** section between "Targets" and "Cycle Steps (for each document)" specifying: write one story per session (after Step 1 of the first document), checklist holds one `[ ]` per doc touched + one `[ ]` for the Final-Step project-essentials revisit, version-bump decision deferred to the developer at the session gate. New **Step F.5** (after F.4 Approval) flips the checklist `[x]`, marks the story `[Done]`, executes any version-bump-and-CHANGELOG tasks the developer authorized at session start, and presents the session story at a session-level gate distinct from the per-document gates at Step 7. Cross-references `_header-common.md` Rules 1 (story-by-story) / 4 (gate handoff) / 5 (no LLM-proposed commits) and `_phase-letters.md`'s "Inserting a new story" Append rule (no new phase headings — Scope of authority).
  - `project_guide/templates/project-guide/templates/modes/refactor-document-mode.md` — parallel **Session Story** + **Session Close** additions covering README / brand-descriptions / landing page / MkDocs config. Note that `refactor_document` has no project-essentials revisit, so the session-story checklist captures only document-rewrite tasks.
- [x] Ran `pyve run project-guide update` and verified rendered `go.md` for both modes: 4 occurrences each of "Session Story" / "Session Close" / "session-level gate" reaching the rendered output. Mode restored to `code_direct`.
- [x] Re-ran the test/lint sweep after the additional template edits: still **532 passed**, ruff clean.
- [x] Extended `CHANGELOG.md`'s `## [2.8.0]` `### Fixed` section with a P.t-credited bullet describing the refactor-mode change.
- [x] Flipped this story's status to `[Done]` and all checklist items to `[x]`. (P.t remains the v2.8.0 bundled-release story; the audit follow-up rides the same release.)

**Version assignment:** **v2.8.0** — minor bump driven by P.o's new behavior (heal warning + consumer migration path). The four template stories (P.n, P.p, P.q, P.r) ride this release per the principle above. P.t owns the single bump; individual bundled stories do **not** carry their own `Bump version.py` / `Bump pyproject.toml` / `CHANGELOG.md` tasks.

**Migration:** see P.o's Migration section for the consumer-side `git rm --cached docs/project-guide/go.md && git commit` one-liner. No migration needed for the template-only stories beyond running `project-guide update`.

**Out of scope:**
- **Splitting the release into a v2.7.3 patch (templates only) followed by v2.8.0 (P.o code).** Previously considered; rejected because the template changes are themselves "code abstracted into text" — they require a release tag to reach consumers, so there's no real "doc-only patch" available, and bundling everything as v2.8.0 keeps the consumer-visible changelog coherent rather than fragmenting across two close-spaced releases.
- **Bundling stories from outside Phase P.** Phase P's bundle is the bundle; if work in a future phase lands before this release ships, it gets its own release story.
- **Pre-release rebasing or squashing** of individual story commits. Each bundled story keeps its own commit per `code_direct` convention; the bundled release is the version-bump commit on top, with the CHANGELOG entry referencing every bundled story by ID.
- **Updating the Version Cadence rule** (top of this file) to call out the "templates are code abstracted into text" principle explicitly. The current wording ("Doc-only stories do not bump for themselves") is misleading because it conflates true prose-doc-only stories (very rare in this project) with template-touching stories (common, and effectively code). Worth a follow-up doc fix at the Version-Cadence-section level; out of scope for this bundled-release story.

---

### Story P.u: v2.9.0 `git-push` bundled-commit recognition and bundle offer [Done]

**Problem.** Two related friction points in the `project-guide git-push` wrapper (P.k), observed in dogfooded use in a downstream project (`ml-datarefinery`):

1. **Bundled commits aren't recognized.** When a developer commits multiple `[Done]` stories under one subject (e.g., `H.a, H.b, H.c InputSource sidecar labels...`), the wrapper's `_COMMIT_SUBJECT_STORY_ID_RE` only matches single-ID prefixes. The bundled subject is invisible to `_get_committed_story_ids()`, so on the next invocation those three stories appear "uncommitted" — the wrapper either incorrectly offers the oldest one for re-commit (if it would now be the lone `[Done]` candidate) or falls through to the multi-uncommitted error path.
2. **No bundle offer.** When 2+ `[Done]` stories are uncommitted, the wrapper exits 1 with `"Multiple uncommitted [Done] stories: ... Use 'git-push' directly to commit them one at a time"`. The developer must hand-type a bundled message. The wrapper already knows the IDs, versions, and titles — it should offer to assemble the bundled message and ask `[Y/n]`.

**Behavior (post-story).**

- **Bundled-commit parsing.** `_COMMIT_SUBJECT_STORY_ID_RE` is retired in favor of a structured parser that extracts the full sequence of ID tokens from a commit subject. The parser greedily consumes `<id>(: vX.Y.Z)?` tokens separated by `,\s*`, followed by an optional `:` before the title. Every colon is **optional on parse** to tolerate legacy bundled subjects (`H.a, H.b, H.c InputSource ...`).
  - **Emit rule (canonical):** a colon precedes a *version* or a *title*; it does **not** separate two bare IDs. Concrete shapes:
    - `H.a, H.b, H.c: Foo bar bing baz` (no versions; colon only before the title)
    - `H.a, H.b: v1.2.3, H.c: Foo bar bing baz` (one interior version; colon before that version and before the title)
    - `H.a, H.b, H.c: v1.2.3 Foo bar bing baz` (single trailing version covering the bundle's release; colon before the version)
    - `H.a: v1.2.3, H.b: v1.2.4, H.c: v1.3.0 Foo bar bing baz` (each ID versioned; colon before every version, and the last ID's `: <ver>` segment doubles as the boundary before the title)
  - Single-ID subjects continue to parse correctly under both legacy forms (bare `A.a: ...` and storied `Story A.a: ...`).
  - The "already-committed" set is keyed on bare `<id>` only (version is incidental — see duplicate-key warning below).
- **Duplicate-`<id>` warning.** When `_get_committed_story_ids()` finds the same `<id>` in 2+ commit subjects (regardless of version), emit a stderr warning listing the affected `<id>` plus the offending commit subjects, and ask `Continue? [Y/n]`. Under `--no-input`, auto-**no** (abort with exit 1) so CI surfaces the anomaly. Default at the interactive prompt is `Y` (continue).
- **Bundle offer.** When 2+ uncommitted `[Done]` stories exist, the wrapper proposes a bundled commit subject and asks `Use this message? [Y/n]`:
  - **Emit format (formatter side, derived from `stories.md` headings):** join the per-story tokens with `, `, then append `: ` and the joined titles. Per-story token = `<id>` if the story has no version, `<id>: <version>` if it does. The colon-before-title boundary is supplied by the formatter (after the last ID, or after its `: <version>` if present) — collapsed to a single `:` when the last ID is already versioned (i.e., `H.a: v0.1.0` followed by ` Foo` reads as "version then title", with the colon doing double duty). Titles joined with ` + `, no escaping of `+` inside individual titles. Concretely, the four shapes above are reachable:
    - All versionless → `H.a, H.b, H.c: title1 + title2 + title3`
    - Mixed → `H.a, H.b: v1.2.3, H.c: title1 + title2 + title3`
    - All versioned → `H.a: v0.10.0, H.b: v0.11.0 title1 + title2` (last ID's `: <ver>` is the boundary; no second colon)
    - The single-trailing-version shape (`H.a, H.b, H.c: v1.2.3 Foo`) is **valid on parse** (legacy / hand-typed bundles) but not what the formatter emits from stories.md headings — each story carries its own version or none.
  - **Whitespace:** the final message is trimmed and internal whitespace collapsed to single spaces.
  - **Title sanitization:** same rules as single-story (backticks → single quotes; double quotes → single quotes; single quotes pass through).
  - **`[Y]`:** the wrapper invokes `git-push` with the bundled message (same shell-less `subprocess.run` path as the single-story branch).
  - **`[n]`:** today's exit-1 `"Multiple uncommitted [Done] stories: ... Use 'git-push' directly"` error. Developer untangles the situation manually.
  - **`--no-input`:** auto-**no**. CI gets the existing exit-1 error path; nothing new is committed silently. The developer re-runs interactively and types `y` to accept the bundle.
- **Single uncommitted `[Done]` story:** unchanged. No bundle prompt; today's behavior preserved exactly.

**Why these defaults.**

- Duplicate-`<id>` is project-wide anomalous (one story = one commit, modulo bundles where the ID still only appears once across subjects). Worth a warning + interactive confirm. Auto-no under `--no-input` because CI shouldn't paper over a real history irregularity.
- Bundle offer auto-**no** under `--no-input` because accepting changes the *shape* of the commit (bundled vs. single) silently — that is a developer decision, not a CI default. Falling through to today's error keeps CI behavior bit-identical and the developer can re-run interactively (or up-arrow + `y`) to take the offer.
- Title parsing is intentionally absent on the read side. As the developer observed, story prose may contain `+` and other separators; anchoring on the ID-token shape is the only robust strategy.

**Implementation:**

- [x] **Replace `_COMMIT_SUBJECT_STORY_ID_RE` with a multi-ID parser.** Extracted to `project_guide/stories.py` as `parse_committed_ids_from_subject(line: str) -> list[str]`. Tokenizer-style parser: greedy `<id>(: <ver>)?` consumption, comma-separated for bundles, with the colon optional on parse (legacy bundles tolerated). Disambiguation rule preserved: a single ID without `:` is rejected (`Story J.m.2 some other text` → `[]`).
- [x] **Rewrote `_get_committed_story_ids()`** to use the new parser. Return type changed from `set[str]` to `tuple[set[str], dict[str, list[str]]]` so callers receive both the committed-IDs set and the duplicates map (keyed on bare `<id>`, regardless of version differences).
- [x] **Added `derive_bundle_commit_message(headings: list[StoryHeading]) -> str`** in `project_guide/stories.py`. Splits the leading `vX.Y.Z ` off each `StoryHeading.title` (the existing dataclass shape — no schema expansion needed), joins per-story tokens with `", "`, applies the colon-precedes-version-or-title rule, joins titles with `" + "`, sanitizes backticks / double quotes, and trims + collapses whitespace.
- [x] **Added `_prompt_continue_on_duplicate_ids(duplicates, skip_input) -> bool`** helper in `project_guide/cli.py`. Always emits the duplicate warning to stderr (visible even in non-interactive flows). Returns `False` (abort) under `skip_input`. Interactive default `Y`.
- [x] **Rewrote the `len(uncommitted) > 1` branch in `git_push`.** Builds the bundled message, calls `_prompt_use_bundle_message(message, skip_input)`. Under `skip_input` returns `False` (auto-decline → today's exit-1 error). Interactive prints the proposed subject then prompts `Use this message? [Y/n]`. Accept → invoke gitbetter with the bundled message. Decline → exit 1 with the existing `"use git-push directly"` text.
- [x] **Plumbed `--no-input` into `git-push`.** Added `@click.option('--no-input/--input', 'no_input', ...)` with `should_skip_input(no_input)` resolution. Help text describes the auto-decline behavior on both gates.
- [x] **Tests in `tests/test_cli.py`** (extend the existing P.k test section):
  - Migrated four P.s regex tests to call the new parser (preserves coverage; tests now live in stories.py for the comprehensive matrix).
  - New `test_git_push_recognizes_bundled_commit_in_already_committed_check` regression for the field bug (bundled subject now marks all IDs committed).
  - New bundle-offer tests: happy path (versioned, versionless, mixed), branch-name pass-through, quote sanitization, `--no-input` auto-decline, interactive decline, distinct-IDs-in-bundle-is-not-duplicate.
  - New duplicate-`<id>` warning tests: interactive `[Y]` continues, interactive `[n]` aborts, `--no-input` auto-aborts.
  - Updated `test_git_push_errors_on_multiple_uncommitted_done_stories` → `*_with_no_input` (preserves the exit-1 behavior under the new `--no-input` path) + companion test for interactive decline.
- [x] **Tests in `tests/test_stories.py`**: 12 new parser tests (single bare/storied/sub-numbered, bundle legacy/canonical/mixed/single-trailing-version/storied/sub-numbered, garbage rejection) and 7 new bundle-formatter tests (all-versionless, all-versioned, mixed, quote sanitization, `+`-in-title pass-through, whitespace trim/collapse, round-trip with parser).
- [x] **Ran full test suite** — `pyve test` → **566 passed** (up from 532 baseline; +34 net tests).
- [x] **Ran lint** — `pyve testenv run ruff check project_guide/ tests/` → **All checks passed!**
- [x] **Updated `docs/specs/project-essentials.md`** — expanded the `git-push` developer-lane section with the bundle-offer flow, the colon-precedes-version-or-title rule, the four reachable emit shapes, the duplicate-`<id>` warning, the `--no-input` auto-decline defaults, and the parse-permissive / emit-strict invariant. Also updated the Commit-workflow section's parser reference (regex → `parse_committed_ids_from_subject`). Ran `pyve run project-guide update` → "All files are up to date" (no rendered-template drift since the bundled `project-essentials.md` template has no git-push section).
- [x] **Bumped `project_guide/version.py`** to `2.9.0`.
- [x] **Bumped `pyproject.toml`** to `2.9.0`.
- [x] **CHANGELOG.md** new `## [2.9.0] - 2026-05-20` entry: opening paragraph + `### Added` (bundle recognition, bundle offer, duplicate warning, `--no-input` flag) + `### Changed` (internal API return-type, parser location, docs expansion) + `### Fixed` (field bug regression).
- [x] **Flipped story status** `[Planned]` → `[Done]` and checked off all `[ ]` items.

**Version assignment:** **v2.9.0** — feature/improvement (new bundle-offer behavior, new `--no-input` flag, fix for bundled-commit recognition in the already-committed check). Minor bump per Version Cadence.

**Out of scope:**
- **Auto-bundling without prompt.** The `[Y/n]` gate is non-negotiable — accepting a bundle silently changes the shape of the commit; the developer always gets the last word.
- **Picking a subset of the uncommitted `[Done]` stories to bundle.** Bundle offer is all-or-nothing for the uncommitted set. Cherry-picking is the developer's job via raw `git-push` after declining.
- **Reading versions from sources other than `stories.md` headings.** Version source is unchanged from the single-story flow.
- **Title-based heuristics on the read side.** Parser anchors on ID-token shape only; titles are never inspected when scanning git log.
- **Renaming `_COMMIT_SUBJECT_STORY_ID_RE`-era public symbols.** The regex is internal; replacing it does not affect any documented API.
- **Header-story awareness and out-of-sequence detection** in the bundle-offer flow. Deferred to Story P.v.

---

### Story P.v: v2.10.0 `git-push` header-story awareness and out-of-sequence detection [Done]

**Problem.** Two additional friction points in the `project-guide git-push` wrapper, surfaced by dogfooding P.u's bundle-offer flow in `ml-datarefinery`:

1. **Header stories are misclassified as commit units.** A common authoring pattern is a "group overview" story `### Story H.m: imagecorruptions Generation ops [Done]` followed by sub-numbered children `H.m.1`, `H.m.2`, `H.m.3` that do the actual work. The header is prose-only (no `- [ ]` / `- [x]` checklist items); the children carry the tasks and version bumps. Today's wrapper treats the header heading as a normal `[Done]` story and proposes to commit it, which is wrong — the header has no work to commit.
2. **Out-of-sequence `[Done]` stories silently bundle.** A real field bug: when `H.m` (a header, but pre-this-story the wrapper didn't know that) appeared uncommitted alongside `H.n.1` (uncommitted) with `H.m.1`/`H.m.2`/`H.m.3` committed between them in stories.md document order, the wrapper happily proposed `H.m, H.n.1: ... + ...` as a bundle subject. The two IDs *look* in-sequence in isolation, but the document order proves they are not — older committed work sits between them.

**Behavior (post-story).**

- **Header detection.** A `[Done]` story is treated as a header (skipped by the uncommitted-detection flow) iff its body — the text between this `### Story` heading and the next `### Story` / `## Phase` / `## Future` / EOF — contains **zero** Markdown checklist items, i.e., no `- [ ]` and no `- [x]` lines (top-level or indented). A story with at least one checklist item, even if all items are `- [ ]`, is a real story; unchecked items are a developer-discipline concern, not a header signal. The other header variant — `### Story <id>: <title>` with no `[Done]`/`[Planned]`/`[In Progress]` status suffix at all — is already invisible to `_STORY_RE` and needs no new code path.
  - **Scope of the filter:** git-push only. `_read_done_stories` populates a new `StoryHeading.is_header` boolean so callers can opt-in; the `status` command and other consumers continue to count `[Done]` headers in their totals (the developer chose to mark them `[Done]`; that is their semantic).
  - **Header IDs in git log:** if a developer commits a subject like `H.m: Group overview`, the parser picks it up and `H.m` lands in the `committed` set normally. No header-aware policing on the git-log side — the wrapper does not dictate what counts as a "real" commit.
- **Out-of-sequence detection.** After filtering headers, the post-filter `[Done]` list in stories.md document order must have all committed stories *before* all uncommitted ones (committed prefix → uncommitted suffix). Any uncommitted story whose index is **less than** the index of the last committed story is **out-of-sequence**. When out-of-sequence stories exist, exit 1 with a message that lists every offender plus the later-committed IDs that proved the gap, and (for full context) the uncommitted stories that would have been eligible for normal flow. Phase boundaries are not respected — the check operates on the flat document-order list. Example message:

  ```
  Out-of-sequence [Done] stories detected:
    H.b is uncommitted, but later stories are already committed:
      - H.c
      - H.d

  Uncommitted [Done] stories in proper sequence (eligible for normal flow once
  the above are resolved):
    - H.i
    - H.j

  Commit out-of-sequence stories manually with raw git-push, or investigate
  the history gap.
  ```

  Under `--no-input` the out-of-sequence error still fires (no auto-yes/no — it is an unambiguous error path, not a prompt).
- **Empty-uncommitted-after-filter graceful message.** When the only `[Done]` stories not in git are headers, the post-filter uncommitted list is empty. Today's `"Story <last id> is already committed"` message names the header heading, which is misleading. Replace with **exit 0** + message: `Nothing to commit — every real [Done] story is already in git log. (<H.m> appears as a [Done] header; headers do not produce commits.)` Exit 0 because the repo is in the state the developer wanted: nothing pending. (The `not done_stories` branch — no `[Done]` headings at all — continues to exit 1 with the existing message, since that is a stories.md authoring problem.)

**Why these defaults.**

- **Forgiving header signal.** Q3-clarified rule: a `[Done]` story with all `- [ ]` items and zero `- [x]` items is *not* a header — it is a real story whose developer forgot to flip checkboxes. The header signal is specifically zero items *of any kind*, which matches the prose-only authoring pattern. Failure direction: false-negative on commit prompts (real story with no checklist gets ignored) beats false-positive (header gets committed by mistake).
- **Out-of-sequence as a hard error, not a prompt.** The bundle-offer `[Y/n]` gate is appropriate when the wrapper is confident the proposal makes sense and just wants developer consent. Out-of-sequence is the opposite: the wrapper has *evidence* that the proposal would be wrong. No prompt can salvage that — surfacing the gap and aborting is the only safe move.
- **Exit 0 on "nothing real to commit".** A bare `git-push` invocation in a clean repo is success: the repo is in the desired state. Pre-P.v exit-1 was an artifact of treating the absence of uncommitted work as a failure to do the requested action; post-filter the more accurate framing is "the action is unnecessary."

**Implementation:**

- [x] **Added `is_header: bool = False` field to `StoryHeading`** in `project_guide/stories.py`. Default `False` preserves backward compat for tests and callers constructing `StoryHeading(story_id=..., title=...)` directly.
- [x] **Rewrote `_read_done_stories`** to slice each story's body (between its heading and the next `### Story` / `## Phase` / `## Future` / EOF via `_find_story_body_end` helper + `_PHASE_BOUNDARY_RE`) and scan for checklist items via `_CHECKLIST_ITEM_RE` (`^\s*- \[[ x]\]\s`, multiline). Populates `is_header=True` when zero items are found.
- [x] **Added `_check_out_of_sequence(commit_units, committed) -> list[tuple[str, list[str]]]`** helper in `project_guide/cli.py`. Walks the post-header-filter `[Done]` list once to find the last committed index; any uncommitted story at an earlier index is an offender, paired with the list of later-committed IDs that proved the gap. Returns `[]` when the partition is clean.
- [x] **Added `_emit_out_of_sequence_error(offenders, commit_units, committed)`** helper to print the structured error block: per-offender header + indented later-committed IDs, then the eligible-tail context (uncommitted stories not in the offender set), then the manual-resolution hint.
- [x] **Rewired `git_push`** between the duplicate-`<id>` warning and the single-vs-bundle branches:
  1. Filter `done_stories` to exclude `is_header=True` → `commit_units`; capture `headers` separately for the nothing-to-commit message.
  2. Run `_check_out_of_sequence(commit_units, committed)`; non-empty → emit error, exit 1 (always, ignores `--no-input`).
  3. Compute `uncommitted = [s for s in commit_units if s.story_id not in committed]`.
  4. If empty: print `"Nothing to commit — every real [Done] story is already in git log."` + parenthetical naming any headers present, exit **0**.
  5. Else proceed to the existing single-story / bundle-offer logic.
- [x] **Updated `git_push` docstring** to describe the header filter, out-of-sequence detection, and the new exit-0 nothing-to-commit success branch.
- [x] **Tests in `tests/test_stories.py`** — 6 new tests covering `is_header` detection:
  - `is_header=True` for a header (prose-only body, no checklist).
  - `is_header=False` for all-unchecked `[Done]` (forgiving rule).
  - `is_header=False` for at-least-one `[x]` and for mixed `[ ]`/`[x]` cases.
  - `is_header=True` when the body ends at the next `### Story` heading (no child-checklist borrowing).
  - `is_header=False` when only indented checklist items exist (regex `^\s*- \[[ x]\]\s` matches indented).
  - `is_header=True` when the body ends at a `## Phase` boundary (no next-phase-story borrowing).
- [x] **Tests in `tests/test_cli.py`** — 8 new tests covering git-push integration (extend the P.u section):
  - Header-only `[Done]` story → exit-0 nothing-to-commit, git-push not invoked.
  - Header alongside single real uncommitted → header filtered, real story flows through single-story path.
  - Header alongside 2+ real uncommitted → header filtered, bundle offer proposes only the real stories.
  - **Field-bug regression:** header + uncommitted sibling + committed children between them → header filtered, single-story flow on the sibling.
  - Out-of-sequence with single offender → exit 1, message names offender + later-committed IDs, git-push not invoked.
  - Out-of-sequence with multiple offenders → message lists every offender + per-offender later-committed context + the eligible-tail context.
  - Out-of-sequence fires under `--no-input` (regression: no auto-yes/no for unambiguous errors).
  - Nothing-to-commit message names any `[Done]` headers present in the parenthetical.
  - No-`[Done]`-stories-at-all path still exits 1 (only the all-committed case became exit 0).
  - Updated 4 existing tests that asserted the old exit-1 "already committed" behavior to assert the new exit-0 nothing-to-commit path.
  - Updated test helper `_write_stories_md` to append `- [x] done` after each heading so existing tests don't inadvertently produce header stories; added `_write_stories_md_raw` for tests that need to author header / mixed-body content.
- [x] **Ran full test suite** — `pyve test` → **581 passed** (up from 566 baseline; +15 net tests).
- [x] **Ran lint** — `pyve testenv run ruff check project_guide/ tests/` → **All checks passed!** (Fixed two F541 f-string-without-placeholder warnings in the new exit-0 echo calls before re-running.)
- [x] **Updated `docs/specs/project-essentials.md`** `git-push` section heading line to credit v2.10.0; expanded with the header-filter rule, the out-of-sequence partition rule, the exit-0 nothing-to-commit semantics, and rewrote the "Branch logic" bullet list to reflect the post-P.v decision tree. Ran `pyve run project-guide update` → "All files are up to date".
- [x] **Bumped `project_guide/version.py`** to `2.10.0`.
- [x] **Bumped `pyproject.toml`** to `2.10.0`.
- [x] **CHANGELOG.md** new `## [2.10.0] - 2026-05-20` entry: opening paragraph + `### Added` (header filter, out-of-sequence detection) + `### Changed` (body-scan in `_read_done_stories`, `StoryHeading.is_header` field, exit semantics for all-committed, docs expansion) + `### Fixed` (two field-bug regressions: header-plus-sibling false bundle; out-of-sequence silent bundling).
- [x] **Flipped story status** `[Planned]` → `[Done]` and checked off all `[ ]` items.

**Version assignment:** **v2.10.0** — minor bump. Header-aware filtering and out-of-sequence detection are meaningfully new safety checks that prevent wrong commits, not just bug fixes to P.u's behavior. The exit-0 nothing-to-commit path is a small but consumer-visible semantic change (previously exit 1).

**Out of scope:**
- **Promoting header detection to other CLI commands** (`status`, `mode`, etc.). Scope is git-push only; the `is_header` flag is opt-in for other callers, but no consumer is rewired in this story.
- **Header-aware reporting in the duplicate-`<id>` warning.** If a header ID like `H.m` appears in git log, it is treated as a normal commit. Future refinement could special-case headers in the duplicate warning ("H.m appears 3x — but it is a header heading; expected"), but YAGNI until the case actually arises in field use.
- **Auto-fix suggestions for out-of-sequence stories.** The error names the offenders and tells the developer to use raw `git-push` or investigate; the wrapper does not propose splitting commits, re-ordering, or any kind of rebase. Wrapper-initiates-git-ops constraint (same one that bounded P.k, P.o, P.u) is in force.
- **Configurable header-detection signal.** The zero-checklist-items rule is hard-coded. No `--header-marker` flag, no `is_header: true` YAML frontmatter, no alternate signals. If a project ever needs a different signal, it can override `is_header` post-hoc, but that is out of scope here.
- **Sequence-check special-casing for phase boundaries.** The flat document-order check is intentional. A future "phase-aware partition" mode could be added if the field demands it.

---

### Story P.w: v2.10.1 Loosen renumber pre-condition in `_phase-letters.md` partial template [Done]

**Problem.** The renumber-as-last-resort rule in `project_guide/templates/project-guide/templates/modes/_phase-letters.md` (the partial rendered into `go.md`'s Phase/Story ID Scheme section) read: an ID is **locked** once its heading appears in **committed git history**, regardless of `[Planned]` / `[In Progress]` / `[Done]` status. Field experience in a downstream project surfaced the failure mode: when `plan_phase` needed to insert a new phase ahead of one or more `[Planned]` phases that had already been committed to `stories.md` as untouched roadmap placeholders (no work begun, no commits naming them, no cross-references), the LLM correctly read the rule as forbidding the renumber and refused to proceed — even though no references had actually accreted to the IDs being shifted. The rule overweighted "committed to disk in stories.md" and underweighted the actual harm a renumber causes (broken cross-references in commit messages, CHANGELOG entries, in-body story citations, external tooling).

**Behavior (post-story).** The pre-condition is restated as "no references have accreted around the ID." An ID is **locked** iff **(a)** its current status is anything other than `[Planned]` (`[In Progress]` or `[Done]`), **(b)** any commit message names it, or **(c)** it is cited outside `stories.md` itself — `CHANGELOG.md`, other spec docs, PR descriptions, external tooling. A `[Planned]` heading sitting in committed `stories.md` as an untouched roadmap placeholder is **not** locked — being present in the file is not the same as having references accrete around it. The rule ships with two mechanical verification commands (`git log --all --grep='<ID>'` for commit-message references; `grep -RFn '<ID>' docs/ CHANGELOG.md --exclude=stories.md` for cross-references in tracked text) so the LLM has a deterministic safety check, not a judgment call. The `--exclude=stories.md` flag is essential — without it the grep always matches the heading being checked, making the "both come up empty" success condition impossible to reach.

**Why these defaults.**

- **Reference-accretion as the locking signal.** What actually breaks when an ID is renumbered is *external citation* of that ID. A `[Planned]` heading that nothing else references — including no commit message, since no work has begun — is safe to shift. The pre-P.w rule conflated "in the committed file" with "referenced," which led to false-positive lockouts.
- **Three independent conditions joined by OR, not a checklist.** Any one of (a), (b), (c) being true is sufficient to lock. This matches how citations actually accrete: status flips, commits, and cross-doc mentions are independent events. The LLM does not need to weigh them; it checks each and locks on the first hit.
- **Status check chosen over historical-status scan.** Condition (a) is "current status is anything other than `[Planned]`," not "status has ever flipped past `[Planned]`." A story that was once `[Done]` and got reverted to `[Planned]` is vanishingly rare; when it does happen, condition (b) (the commit that did the work, or the revert commit) catches it. Avoiding the history scan (`git log -p -- docs/specs/stories.md | grep ...`) keeps the verification fast and mechanical.
- **Keep "PR descriptions" in (c) even though `code_direct` has no PRs.** The partial template ships to all consumers of project-guide, not just dogfooded-as-`code_direct` projects. Downstream projects in `code_test_first` or production modes use PRs; the rule must cover them.

**Implementation:**
- [x] **Rewrote the Renumber bullet** in `project_guide/templates/project-guide/templates/modes/_phase-letters.md` (line 36–44) — replaced the working-tree-only pre-condition with the three-condition reference-accretion rule, added the verification command block (with `--exclude=stories.md` on the grep), and added the explicit "untouched `[Planned]` placeholder ≠ locked" clarification.
- [x] **Ran `pyve run project-guide update`** to propagate the template edit to `docs/project-guide/go.md` (the dogfooded installed copy). Heal hook auto-healed 1 template; update reported "All files are up to date".
- [x] **Ran `pyve test`** → **581 passed** (no test changes; baseline preserved).
- [x] **Ran `pyve testenv run ruff check project_guide/ tests/`** → **All checks passed!**
- [x] **Bumped `project_guide/version.py`** to `2.10.1`.
- [x] **Bumped `pyproject.toml`** to `2.10.1`.
- [x] **CHANGELOG.md** new `## [2.10.1] - 2026-05-23` entry under `### Changed`.
- [x] **Flipped story status** `[Planned]` → `[Done]` and checked off all `[ ]` items.

**Version assignment:** **v2.10.1** — patch. Doc-only template content change at the developer's direction (deliberate `.N` line, not bundled with a preceding code story). No code path affected, no test changes, no consumer-visible CLI behavior change; the only consumer-visible effect is that LLMs reading the rendered `go.md` now have a more permissive (and more correct) renumber rule.

**Out of scope:**
- **Tests for the template content.** The partial is rendered verbatim through Jinja; there is no logic to test. The existing render-pipeline tests already verify the file is included.
- **Programmatic enforcement of the renumber pre-condition.** The rule is LLM-readable guidance, not a CLI safety check. A future `project-guide check-renumber <ID>` command could mechanize the three-condition verification, but YAGNI until repeated field use proves the need.
- **Re-evaluating prior locked-ID decisions in the dogfooded `stories.md`.** No existing story IDs in this repo's `stories.md` are being renumbered as part of this fix — the change is rule-text only.
- **Tightening / loosening the `plan_phase` template's invocation of this rule.** The rule lives in the partial; `plan_phase` includes it unchanged. If `plan_phase` needs additional guidance on *when* renumber is the right tool vs. Append or Sub-number, that is a separate story.

---

### Story P.x: v2.10.2 Story-insertion priority signal and out-of-order completion guard [Done]

**Problem.** Field experience in a downstream project surfaced two related LLM workflow bugs around story creation and completion, both rooted in the same scenario: an ad-hoc developer request arriving while `[Planned]` stories sit ahead in the phase queue.

*The B.g incident.* A developer's project had `B.a` / `B.b` `[Done]`, `B.c` / `B.d` / `B.e` / `B.f` `[Planned]`. The developer asked the LLM to draft an ad-hoc bugs/gaps document for a dependency repo — an interrupt to the planned sequence. The LLM read the "create a story for my work" rule plus the Option 1 Append default, concluded the new story should be `B.g`, drafted the doc, and marked `B.g` `[Done]` while `B.c`–`B.f` remained untouched `[Planned]`. Two distinct bugs:

1. **Insertion-position bug.** Appending at the tail was the wrong position. The ad-hoc doc-drafting work belonged *before* the planned `B.c`–`B.f` queue (conceptually it was an interruption-then-resume, not a continuation past the queue). Option 1 Append's wording — *"new work goes after the latest committed story, regardless of which earlier story conceptually motivated it"* — gave the LLM no signal to insert mid-queue, even though the developer's ad-hoc request was itself implicit signal.
2. **Out-of-order completion bug.** Even granted the wrong position, the LLM happily marked `B.g` `[Done]` while `B.c`–`B.f` remained `[Planned]`. The cycle-mode templates implicitly assume "the next story to work on is the next-in-sequence `[Planned]` one" but never state it as a hard rule, so the LLM completed work out of document order — producing the same out-of-sequence state that P.v's `git-push` check now catches at commit time, but with no upstream prevention or recovery beat.

**Behavior (post-story).** Two template edits, addressing the two bugs at their respective layers:

- **Insertion-position layer (`_phase-letters.md`, Option 1 Append).** New exception paragraph appended to the Option 1 bullet: when the developer signals (explicitly *or* implicitly via an ad-hoc interrupt request) that a new story should land before existing `[Planned]` stories, insert immediately after the last `[Done]` story and renumber the `[Planned]` tail via Option 3. P.w's reference-accretion rule guarantees the renumber is safe on untouched `[Planned]` placeholders. The exception explicitly invites the LLM to ask the developer when the signal is ambiguous, rather than defaulting to the tail. Without any signal, the Append default still rules.
- **Cycle-discipline layer (`_header-cycle.md`).** Two new paragraphs:
  - **"Work stories in document order."** Hard rule: the next story to work on is the next-in-sequence `[Planned]` story; never a new story appended at the tail when `[Planned]` stories sit ahead of it, never a `[Planned]` story chosen out of position. Binds the LLM regardless of any developer signal — completing out of order is corrupting whether or not the developer asked for the work.
  - **"Recovery when already out of order."** When a story has been marked `[Done]` while earlier `[Planned]` stories remain, stop and ask the developer to choose between (a) moving the completed story to its proper position via Option 3 Renumber (allowed by P.w on untouched `[Planned]` placeholders), or (b) undoing the work and restoring `[Planned]` status. Do not pick either unilaterally.

**Why these defaults.**

- **Two layers, one root cause.** Both bugs trace back to the B.g failure mode but live at different rule-layers: numbering (`_phase-letters.md`) and execution discipline (`_header-cycle.md`). Fixing only one leaves the other half of the failure mode intact — an LLM with perfect numbering hygiene can still complete out of order, and an LLM that won't complete out of order can still pick the wrong insertion position when asked to author a new story.
- **Ad-hoc request as implicit signal.** The B.g incident showed that LLMs read "developer didn't say 'higher priority'" as "apply the default." Naming "ad-hoc interrupt request" as an implicit signal closes the loophole without requiring the developer to learn a magic phrase. The "ask when uncertain" beat is the safety rail — the rule prefers a clarifying question over a unilateral default-pick.
- **Recovery rule names two options, not one.** "Undo the work" must be on the menu alongside "move the story to its proper place." Sometimes the right answer is that the out-of-order work was itself a mistake — the developer should not be forced into renumber-as-only-option just because the LLM already produced output. The rule deliberately puts the choice in the developer's hands.
- **Cross-referencing P.v and P.w in the rule text.** The cycle-discipline rule explicitly names P.v's `git-push` check (the detection net) and P.w's reference-accretion rule (which makes the recovery renumber safe). This documents the safety-net topology — Bug 1 prevention (P.x insertion rule), Bug 2 prevention (P.x cycle rule), Bug 2 detection (P.v `git-push`), Bug 2 recovery (P.x recovery rule, P.w-enabled) — so future maintainers don't accidentally undo one layer thinking another covers the same ground.
- **Append-not-prepend on `_phase-letters.md` Option 1.** The exception lands as a paragraph appended to the existing Option 1 bullet rather than restructuring the three-option section, preserving the "Always try Option 1 first" framing for the silent default case and minimizing churn to a section that several other documents (CHANGELOG, project-essentials, prior stories) reference structurally.

**Implementation:**
- [x] **Appended exception paragraph to Option 1 Append** in `project_guide/templates/project-guide/templates/modes/_phase-letters.md` — covers higher-priority / prerequisite / blocker / ad-hoc-interrupt signals, names Option 3 Renumber as the mechanism, cites P.w as the safety check, includes the "ask when uncertain" beat, and reasserts the Append default for the silent case.
- [x] **Appended cycle-discipline section to `_header-cycle.md`** — two paragraphs ("Work stories in document order" + "Recovery when already out of order") with cross-references to `project-guide git-push` (P.v detection) and the reference-accretion renumber-safety rule (P.w).
- [x] **Ran `pyve run project-guide update`** → "All files are up to date" (heal hook auto-propagated both template edits to `docs/project-guide/`).
- [x] **Ran `pyve test`** → **581 passed** (baseline preserved).
- [x] **Ran `pyve testenv run ruff check project_guide/ tests/`** → **All checks passed!**
- [x] **Bumped `project_guide/version.py`** to `2.10.2`.
- [x] **Bumped `pyproject.toml`** to `2.10.2`.
- [x] **CHANGELOG.md** new `## [2.10.2] - 2026-05-25` entry under `### Changed`.
- [x] **Flipped story status** `[Planned]` → `[Done]` and checked off all `[ ]` items.

**Version assignment:** **v2.10.2** — patch. Doc-only template content change at developer direction. No code path affected, no test changes. Bumped as a deliberate `.N` line (not bundled with a preceding code story) per developer choice.

**Out of scope:**
- **Programmatic enforcement of the cycle-discipline rule.** The rule is LLM-readable guidance. A future check could verify "no new `[Done]` story has earlier `[Planned]` stories in document order" at story-flip time, but the existing P.v `git-push` check already catches the resulting state at commit time, and YAGNI rules until field use shows the LLM rule alone is insufficient.
- **Retroactive audit of dogfooded `stories.md`.** No existing stories in this repo are out of order (per P.v's check on the recent commit history). The change is rule-text only.
- **Extending the recovery rule to multi-story out-of-order cases.** The rule's "ask the developer" framing already handles N out-of-order stories without special-casing. If field experience shows the LLM needs more structured guidance for multi-story recovery, that is a separate story.
- **A magic-phrase glossary for the priority signal.** The rule lists examples (higher priority, prerequisite, blocker, ad-hoc interrupt request) and explicitly says "or similar" plus "ask when uncertain." Enumerating every possible signal phrase would be both incomplete and over-prescriptive.
- **Updating the cycle-mode templates' Step 2 wording** to repeat the "next-in-sequence `[Planned]`" rule. The rule lives in `_header-cycle.md`, which is included into every cycle mode at render time — no per-mode duplication needed. If a specific mode's Step 2 needs sharper guidance (e.g., `debug` mode's "investigate before authoring"), that is a separate per-mode story.

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
