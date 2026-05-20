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
  - [x] `CHANGELOG.md` — `## [Unreleased]` entry with P.o-tagged Changed/Documented/Migration subsections (the unified `## [2.8.0]` entry is assembled by P.z at release time).
- [x] Tests:
  - [x] `tests/test_cli.py::test_init_emits_untracked_note_on_stderr`
  - [x] `tests/test_cli.py::test_init_quiet_suppresses_untracked_note`
  - [x] `tests/test_cli.py::test_init_no_input_suppresses_untracked_note`
  - [x] `tests/test_cli.py::test_heal_warns_when_go_md_is_tracked` — asserts copy-pasteable migration command verbatim
  - [x] `tests/test_cli.py::test_heal_silent_when_go_md_is_untracked`
  - [x] `tests/test_cli.py::test_heal_silent_when_not_in_git_repo`
  - [x] `tests/test_cli.py::test_heal_suppresses_warning_under_no_input`

**Version assignment:** P.o is the code-bearing story in the Phase P v2.8.0 release bundle. The version bump itself (`project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` entry) is owned by **P.z** — the bundled-release story for v2.8.0 — following the same single-story-owns-the-bump pattern used by P.i for v2.6.0. P.o's CHANGELOG bullet (consumer migration command, heal-warning text, etc.) lands inside the unified `## [2.8.0]` entry that P.z assembles.

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

**Version assignment:** template change (code abstracted into text — see P.z's principle note). Rides P.z's bundled v2.8.0 release; no per-story version bump.

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

**Version assignment:** patch-level regex bug fix; rides P.z's v2.8.0 bundled release. No standalone version bump in this story.

**Migration:** none. The permissive regex retains backward compatibility with the bare form (historical wrapper output and direct developer use) and adds forward compatibility with the `"Story "` prefix form (legacy hand-typed style). Consumers with mixed history get coherent recognition automatically on upgrade to v2.8.0.

**Out of scope:**
- **Updating `derive_commit_message` to emit the `"Story "` prefix.** Considered (Option 2 in triage) and rejected: docs examples are being aligned *to* the bare form, not away from it; changing the wrapper's emitted format would also require updating the P.k test pinning and would propagate a longer prefix into every wrapper-generated commit.
- **A `project-guide check` integrity rule** verifying that every `[Done]` story in `stories.md` has a matching commit-subject parse under the regex. Defer until the broader integrity-check surface exists; the wrapper's own error message already surfaces this kind of mismatch interactively.
- **Backporting the regex fix to v2.7.x as a patch release.** Consumers stay on v2.7.2 until v2.8.0 ships; bundling under P.z avoids a stand-alone v2.7.3 release that would only contain this one regex tweak.
- **Auto-detecting and warning when an existing repo's commit history contains a mix of `"Story <id>:"` and bare `"<id>:"` subjects.** The mix is benign under the permissive regex; no warning needed.

---

### Story P.z: v2.8.0 bundled release [Planned]

**Placeholder ID convention.** `P.z` is a placeholder, deliberately drafted at the end of Phase P's alphabet so it stays out of the way of in-flight work. At release time the developer renumbers this story to whatever the next sequential letter is in Phase P (likely `P.s` or `P.t` after P.o/P.p/P.q/P.r ship) so the final on-disk record matches Rule 1's "in the order performed" invariant.

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

- [ ] Verify every story in the bundle list is `[Done]` on disk. If any are still `[Planned]`, either ship them first or remove them from the bundle (and update the CHANGELOG entry accordingly).
- [ ] Bump `project_guide/version.py`: `__version__ = "2.8.0"`
- [ ] Bump `pyproject.toml`: `version = "2.8.0"`
- [ ] Add a unified `## [2.8.0] - <date>` entry to `CHANGELOG.md`. Recommended structure:
  - One opening paragraph naming the release theme — "Phase P closing bundle: cycle-mode LLM-workflow discipline + XP methodology grounding + untracked-by-default `go.md` policy."
  - `### Added` / `### Changed` / `### Fixed` / `### Documented` subsections as appropriate, with each bundled story summarized as one bullet and credited by ID.
  - **Migration** subsection at the bottom: one-line consumer command for P.o (`git rm --cached docs/project-guide/go.md && git commit`) plus the link to P.o's body for full rationale.
- [ ] Renumber this story's ID from `P.z` to the next sequential letter in Phase P at release time (verify by reading the highest `[Planned]` letter currently in the file and incrementing). Update any in-body references (none expected; this story is self-contained) and any commit-message draft.
- [ ] Flip this story's status to `[Done]` and all `[ ]` checklist items to `[x]`.

**Version assignment:** **v2.8.0** — minor bump driven by P.o's new behavior (heal warning + consumer migration path). The four template stories (P.n, P.p, P.q, P.r) ride this release per the principle above. P.z owns the single bump; individual bundled stories do **not** carry their own `Bump version.py` / `Bump pyproject.toml` / `CHANGELOG.md` tasks.

**Migration:** see P.o's Migration section for the consumer-side `git rm --cached docs/project-guide/go.md && git commit` one-liner. No migration needed for the template-only stories beyond running `project-guide update`.

**Out of scope:**
- **Splitting the release into a v2.7.3 patch (templates only) followed by v2.8.0 (P.o code).** Previously considered; rejected because the template changes are themselves "code abstracted into text" — they require a release tag to reach consumers, so there's no real "doc-only patch" available, and bundling everything as v2.8.0 keeps the consumer-visible changelog coherent rather than fragmenting across two close-spaced releases.
- **Bundling stories from outside Phase P.** Phase P's bundle is the bundle; if work in a future phase lands before this release ships, it gets its own release story.
- **Pre-release rebasing or squashing** of individual story commits. Each bundled story keeps its own commit per `code_direct` convention; the bundled release is the version-bump commit on top, with the CHANGELOG entry referencing every bundled story by ID.
- **Updating the Version Cadence rule** (top of this file) to call out the "templates are code abstracted into text" principle explicitly. The current wording ("Doc-only stories do not bump for themselves") is misleading because it conflates true prose-doc-only stories (very rare in this project) with template-touching stories (common, and effectively code). Worth a follow-up doc fix at the Version-Cadence-section level; out of scope for this bundled-release story.

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
