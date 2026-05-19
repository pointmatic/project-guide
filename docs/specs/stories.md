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
- Strengthening Step 5's authorship language ("you, the LLM, write this story yourself") and adding an Anti-Pattern entry for "Deferring the Gate Artifact to the Developer," plus a trigger for "prevention-scan discovery spawned a new cycle." These gaps were identified during this conversation but are a separate fix — they govern *who authors* the Step-5 artifact, not *what structural changes* are in-bounds. Scope as a follow-up story (likely P.p) if the developer agrees they are worth landing.
- Cross-cutting `features.md` / `tech-spec.md` scope rules (parallel to the `stories.md` rule). No drift observed; defer until one is.

---

### Story P.o: Untracked-by-default `go.md` policy [Planned]

Reframe `go.md` from "the one tracked file under `target_dir`" to "unignored-but-untracked, regenerated on demand." The IDE-LLM-visibility constraint that drove the entire P.d → P.l line of work is about **gitignore status**, not **tracking status**: an unignored-but-untracked file is fully visible to IDE-integrated LLMs (Cursor, Claude Code, VS Code forks), while removing it from version control eliminates an entire class of dirty-working-tree failures during branch switches and post-merge cleanup.

**Found in the field** (consumer report from pyve): a `update/project-guide-v2.7.1` feature branch was pushed, the PR was merged on GitHub, and gitbetter's post-merge `git switch main` aborted with `error: The following untracked working tree files would be overwritten by checkout: docs/project-guide/go.md`. Diagnostics confirmed pyve's main tracked `go.md` (last touched in pyve's `322423d project-guide upgrade to v2.6.0`), the feature branch's tip did not (`git ls-files` empty for the path), and no gitignore rule matched (`git check-ignore` empty). The structural cause was the hybrid status — git's branch-switch safety check sees an untracked-unignored file in the working tree and refuses to overwrite it with main's tracked version. Re-rendering `go.md` from `.project-guide.yml:mode` in `heal` (a related architectural improvement) doesn't help here because git aborts *before* any `project-guide` command runs. Collapsing to untracked-by-default removes the conflict entirely: git doesn't gate `switch` on untracked-unignored files.

**Visibility vs. tracking — the key distinction:**
- **Gitignore status** governs IDE-LLM visibility. The constraint from P.d / the IDE-LLM-visibility section of `project-essentials.md` is: `go.md` must remain **non-gitignored** so Cursor / Claude Code / VS Code-fork LLM tooling can read it via `@-mention` and fuzzy-search. This story preserves that constraint unchanged — the v2.7.1 explicit-list gitignore block already leaves `go.md` un-listed (and therefore unignored).
- **Tracking status** governs version-control churn. The current "tracked by historical accident" state means `go.md` appears in every mode-switch diff, every cross-branch comparison, every merge resolution, and (as in the pyve case) every post-merge `git switch`. Untracking removes the churn without affecting visibility.

**Implementation:**

- [ ] `project_guide/cli.py:heal` — add a step that detects when `docs/project-guide/go.md` is in the consumer's git index (via `git ls-files --error-unmatch <path>` returning 0). When tracked, emit a single-line stderr warning with the copyable migration command:
  ```
  Warning: docs/project-guide/go.md is tracked. The current policy is untracked-by-default — run `git rm --cached docs/project-guide/go.md && git commit` once to migrate.
  ```
  - Silent when go.md is untracked (the steady state).
  - Silent when the cwd is not a git repository (use `git rev-parse --is-inside-work-tree`; fall through on non-zero exit).
  - Suppressed under `PROJECT_GUIDE_HEALING=1` (recursion guard already in place).
  - Suppressed under `--no-input` per the contract.
  - **Do NOT auto-run `git rm --cached`.** That is a history-changing operation on the consumer's index; consistent with the approval-gate-discipline rule (no LLM/wrapper-initiated git ops beyond declared scope), `project-guide` warns and the consumer runs the command on their own schedule.
- [ ] `project_guide/cli.py:init` — after the initial `go.md` render, emit a single-line stderr note: `Note: docs/project-guide/go.md is intentionally untracked. Do not 'git add' it.`. Suppressed under `--quiet` / `--no-input` per the contract. This prevents fresh installs from immediately landing in the same tracked-from-historical-accident state.
- [ ] Project-guide's own dogfooded repo: as part of shipping this story, run `git rm --cached docs/project-guide/go.md && git commit` so the source-of-truth repo matches the new policy and self-validates on next clone.
- [ ] Docs reshape:
  - [ ] `docs/specs/project-essentials.md` — **"IDE-LLM visibility constraint"** subsection: rewrite to make the visibility-vs-tracking distinction explicit. Add the new canonical state: `go.md` is **untracked-but-unignored**.
  - [ ] `docs/specs/project-essentials.md` — **"Inverted gitignore policy"** subsection: append the v2.8.0 stage to the existing v2.6.0 → v2.6.1 → v2.7.1 evolution narrative ("the gitignore block stays at v2.7.1 form; tracking status flips").
  - [ ] `docs/specs/features.md` — FR-14 (Inverted gitignore policy): same evolution-note addition.
  - [ ] `docs/specs/tech-spec.md` — `.gitignore Management` section: add a "Visibility vs. tracking" paragraph and a "Why untracked-by-default?" rationale paragraph citing the pyve incident as the field-evidence trigger.
  - [ ] `README.md` Quick Start: one-line note that `go.md` is intentionally not tracked; consumers upgrading from v2.6.x–v2.7.x run `git rm --cached docs/project-guide/go.md && git commit` once.
  - [ ] `CHANGELOG.md` — `## [2.8.0] - <date>` entry framed as a behavior change with the one-line migration command and the visibility-vs-tracking rationale.
- [ ] Tests:
  - [ ] `tests/test_cli.py` — `init` test asserting the stderr "intentionally untracked" note appears, and is suppressed under `--quiet`.
  - [ ] `tests/test_cli.py` — `heal` test in an `isolated_filesystem` git repo with a tracked `docs/project-guide/go.md`: assert the warning text appears on stderr, the command suggestion is copy-pasteable verbatim, and `heal` exits 0 (warning is non-fatal).
  - [ ] `tests/test_cli.py` — `heal` test in an `isolated_filesystem` git repo with an untracked `docs/project-guide/go.md`: assert no warning is emitted (steady state silent).
  - [ ] `tests/test_cli.py` — `heal` test in a non-git directory: assert no warning, no error, no spurious `git` invocations.
  - [ ] `tests/test_cli.py` — `heal` test with `PROJECT_GUIDE_NO_INPUT=1`: assert the warning is suppressed.
- [ ] Bump `project_guide/version.py`: `__version__ = "2.8.0"`
- [ ] Bump `pyproject.toml`: `version = "2.8.0"`
- [ ] Add `## [2.8.0] - <date>` entry to `CHANGELOG.md`.

**Migration:** consumers run `git rm --cached docs/project-guide/go.md && git commit` once on their default branch. The next `project-guide` invocation (auto-heal hook) regenerates `go.md` as an untracked-unignored working-tree file; IDE LLMs continue to see it; the cross-branch dirty-tree class of failures disappears. Consumers who don't migrate continue to function — `heal` warns on every invocation but doesn't error or refuse work; the cost is `go.md` keeps appearing in their working-tree diff on every mode switch.

**Why "warn-don't-auto-fix":** auto-running `git rm --cached` from inside `project-guide` would mutate the consumer's git index — the same wrapper-initiates-git-ops concern that constrained P.k's `git-push` to a thin gitbetter passthrough. Project-guide writes its own files (templates, `.project-guide.yml`, the gitignore block) but does not edit the consumer's index or HEAD. The warning surfaces the issue with a copyable command; the consumer decides when to apply it.

**Out of scope:**
- A dedicated `project-guide untrack-go-md` subcommand. YAGNI — the heal warning gives the consumer the exact command verbatim, and a dedicated subcommand would expand the wrapper-initiates-git-ops surface that the project has been deliberate about keeping narrow.
- A `project-guide check` integrity rule that flags tracked `go.md` as a defect with non-zero exit. Defer until the broader integrity-check surface is built (see Future > Integrity & Validation); the heal warning covers the same ground with a softer touch.
- Pre-flight on the `project-guide git-push` wrapper to detect dirty/untracked `go.md` before invoking gitbetter. The post-P.o steady state is "go.md is untracked-unignored on every branch" — branch switches no longer fail on it. If a pre-flight is still wanted after P.o ships and field-tests, scope it as a separate follow-up story.
- Backporting the new policy to v2.6.x or v2.7.x. Consumers on older project-guide versions stay on the historical tracked-`go.md` model; upgrading to v2.8.0 surfaces the heal warning and the README migration note.
- Changing the v2.7.1 explicit-list gitignore block. The block is unchanged — `go.md` is still un-listed and therefore unignored. Only tracking status flips.
- Applying the same untracked-by-default policy to other generated artifacts under `target_dir` (e.g., rendered mode files in `templates/`). Those are already gitignored under the v2.7.1 block, so the question doesn't arise; if a future artifact lands in the same "tracked + generated" hybrid as `go.md` is leaving, that would warrant its own story (and possibly a new phase via `plan_phase`).

---

### Story P.p: LLM workflow discipline — documentation timing, spike-awareness, gate handoff [Planned]

Bake four cross-cutting workflow rules into the universal Rules block of `_header-common.md` so every rendered `go.md` carries them, and reinforce the rules that hit hardest at `debug`-mode's Step 5 with inline guidance plus a new anti-pattern entry. The rules address structural LLM failure modes observed in this conversation and in prior cycles: undocumented work, off-by-one story numbering when work is paused/resumed, conflation of documentation with implementation, deferral of the gate artifact to the developer.

**Failure mode this story closes:** in a prior turn, the LLM (this assistant) made template changes after misreading "go" as approval for a recommendation rather than as a directive to implement the planned story. The work was completed without a story; at the approval gate, the LLM asked the developer how to wrap it instead of writing the story itself. The developer correctly named both the immediate fix (renumber + insert) and the structural gap (the templates don't tell the LLM *who* writes the Step-5 artifact). P.p installs the missing rules at the template level so the next LLM in this situation just knows what to do.

**The four rules** (full text lands in `_header-common.md` Rules block; summary here for the story record):

1. **Sequential, story-by-story documentation.** Every chunk of LLM-produced work that lands in the repo (code, tests, docs, templates) is captured as a story in `stories.md` under the existing phase, in the order performed. One coherent unit of work → one story → one developer commit.
2. **Documentation timing.** Default: write the story with its `[ ]` checklist → execute → flip to `[x]` → present at the gate. Exception for `debug` mode: when the root cause is unknown until exploration, the legitimate sequence is explore → reproduce → small-scope fix → write the story (Step 5). Either way, **the story exists on disk by the time the cycle reaches its approval gate.**
3. **Spikes for uncertainty reduction.** When the path forward is uncertain, document the work as a spike — a time-boxed throwaway effort whose deliverable is a documented outcome. Three flavors recognized (integration / architectural / investigation); full definitions in `developer/best-practices-guide.md`'s "Hello World First — Spike Early, Spike Often" section. *(P.q lands the three-flavor expansion at that destination; P.p's Rule 3 forward-references the section, which already exists.)*
4. **Approval-gate documentation handoff.** Every gate presents (a) a story reflecting current completion state (`[x]` done, `[ ]` outstanding, one-line note on in-progress items) alongside (b) the files changed. If you enter a gate with undocumented work, write or update the story *before* pausing. The developer returns distracted; the handoff names what's done, what's next, what decision is being asked for.

**Implementation:**

- [ ] `project_guide/templates/project-guide/templates/modes/_header-common.md` — add four bullets to the Rules block, immediately after the "Scope of authority — structural changes to `stories.md`" bullet added in P.n. Use bold-leading-title style matching the existing substantive rules. Rule 3 points at `developer/best-practices-guide.md` § "Hello World First — Spike Early, Spike Often"; the section exists today, P.q expands its content.
- [ ] `project_guide/templates/project-guide/templates/modes/debug-mode.md` Step 5 — add a "Documentation timing in `debug`" paragraph after the existing "Scope reminder before you write" paragraph (added in P.n), before "(a) The story write-up." Names the exception explicitly (debug discovers root cause then writes the story) and reinforces the on-disk-before-gate invariant.
- [ ] `project_guide/templates/project-guide/templates/modes/debug-mode.md` Anti-Patterns section — add a new entry: **"Deferring the Gate Artifact to the Developer"**, sibling to the existing "Declaring the Fix Complete After Step 4". Names the exact failure shape from this session: stopping at Step 4 and asking the developer how to story-ize the work, or asking permission to write the story. Solution points at Rule 4.
- [ ] Run `pyve run project-guide update` to propagate the template edits to `docs/project-guide/templates/modes/_header-common.md` and `docs/project-guide/templates/modes/debug-mode.md`.
- [ ] Verify rendered `docs/project-guide/go.md` contains the four new rule bullets and the two new debug-mode insertions.
- [ ] Flip this story's status to `[Done]` and all `[ ]` checklist items to `[x]`.

**Version assignment:** doc-only template change. Per Version Cadence, doc-only stories do not bump for themselves; P.p rides the next code-story release. No `project_guide/version.py`, `pyproject.toml`, or `CHANGELOG.md` change in this story.

**Migration:** none. The new Rules-block bullets affect LLM behavior on the next `project-guide mode <X>` render or the next auto-heal sync of installed templates. Existing consumers see the new wording without any consumer-side action.

**Out of scope:**
- **The XP methodology grounding and the three-spike-flavor expansion in `developer/best-practices-guide.md`.** Scoped as P.q so the cycle-mode discipline rules (P.p) and the foundation-terminology reconciliation (P.q) can be reviewed and committed independently.
- **Inline reinforcement of Rules 1–4 in `code_direct`, `code_test_first`, `refactor_document`, `refactor_plan` mode templates.** The universal `_header-common.md` rule covers them; defer per-mode reinforcement until evidence shows it's needed.
- **Tooling helper to detect "approval gate reached without story update"** (e.g., a `project-guide check` rule). Defer until the broader integrity-check surface is built.

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
