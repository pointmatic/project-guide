# phase-p-auto-heal-plan.md — project-guide (Python)

Phase P plan: Auto-heal & Production Hardening (v2.6.0).

This phase has two complementary themes:

1. **Auto-heal** — collapse the `docs/project-guide/` install footprint in consumer repos to a single committed file (`go.md`) plus the committed config (`.project-guide.yml`). Every `project-guide` invocation quietly runs a self-contained `heal` command that detects drift and offers `[Y/n]` (default Y) to repopulate from the bundled package. Goal: zero-friction "clone and go" — the only thing a new contributor does after `git clone` is run any `project-guide` command (including `--help`) and the install heals itself.
2. **Production hardening (subset)** — close the production-readiness gaps that are appropriate for solo-dev project-guide *today*: mandatory CI on PRs, `SECURITY.md`, `CONTRIBUTING.md`, and `.github/dependabot.yml`. Branch protection and PR-only workflow are explicitly **deferred** until contributors join (per developer override at the production-readiness checklist).

**Implementation strategy:** Land `heal` first (P.a–P.c), since the `.gitignore` template change (P.d) depends on `heal` being in place to repopulate fresh clones. Production hardening items (P.e–P.h) are independent of the `heal` work and can ship in any order. Final story (P.i) bundles the version bump + CHANGELOG and updates `project-essentials.md`.

---

## Gap Analysis

### Bundled-template clutter in consumer repos

`project-guide init` currently writes ~35 files under `docs/project-guide/` (developer reference docs, mode templates, artifact templates, header partials), and only `*.bak.*` is gitignored. The full template tree gets committed to consumer repos, which:

- Bloats `git status`, `git diff`, and PR reviews for changes that aren't part of the consumer's codebase value.
- Makes `project-guide update` noisy — every template tweak shows up in the consumer's working tree as churn.
- Couples consumer repo history to the project-guide template surface, which the consumer didn't author and shouldn't have to review.

The **only** file the consumer's LLM workflow actually requires is `docs/project-guide/go.md` — the entry point that the developer points the LLM at. Everything else is rendered output from package-bundled sources, recoverable by re-running the install pipeline.

### No self-healing flow

`init` is the one-time bootstrap; `update` is "refresh files that exist". Neither command handles the post-clone case where `.project-guide.yml` and `go.md` are committed but the rest of the tree is gitignored and absent — that scenario currently has no command. A developer cloning a project-guide-using repo today must read the README, run `project-guide init` (which errors on existing `.project-guide.yml` without `--force`), and figure out the right escape hatch.

### Production-readiness gaps post-1.0

Project-guide is at v2.5.15 and well past its v1.0.0 threshold but has not adopted the production-readiness items appropriate for a published consumer-facing tool:

- **No `SECURITY.md`** — no vulnerability reporting channel.
- **No `CONTRIBUTING.md`** — no documented dev setup, code style, or PR/release process for outside contributors.
- **No `.github/dependabot.yml`** — runtime and CI dependency updates are not automated.
- **CI exists (`ci.yml`, `test.yml`, `publish.yml`, `deploy-docs.yml`) but is not wired as a PR gate** — solo-dev mode currently merges direct to `main`, so "merge blocked on red" is not enforced. We are *deferring* PR-only workflow until contributors join, but tightening the CI workflows themselves to be PR-ready is in scope.
- Trusted PyPI publisher is already configured (developer confirmed at checklist walk).

---

## Feature Requirements

### P-FR-1: `heal` command

A new top-level CLI command, `project-guide heal`. Idempotent and self-contained.

**Behavior:**

1. Loads `.project-guide.yml`. **Missing config is a hard error** with exit code 1 and stderr message: `Missing .project-guide.yml — run 'project-guide init' to bootstrap the project.` (No DNA, can't heal.)
2. Runs the same drift detection as `project-guide status` (file discovery via `sync.py`, hash comparison against bundled templates).
3. If **no drift** (zero missing, zero stale) → exit 0 with **no stdout**. Silent success is essential because `heal` runs invisibly on every CLI invocation via the auto-hook.
4. If drift is detected → print a one-line summary to stderr (`N templates missing or stale.`), then prompt `Update? [Y/n] ` (default Y). On yes, run the equivalent of `update` (with create-if-missing semantics for files absent from disk). On no, exit 1 with no further action. On `--no-input` → auto-yes (see P-FR-3).
5. Re-renders `go.md` for the current mode after applying updates.
6. Schema mismatch behavior is unchanged from `update` — `SchemaVersionError` propagates with the same older/newer guidance.

**Difference from `update`:** `update` only refreshes files that exist on disk; `heal` also creates missing files. `heal` is the right command for the "fresh clone with templates gitignored" case.

**Difference from the deferred `project-guide check` (in `Future`):** `check` is read-only verify-flow with nonzero exit on integrity violations, suitable for CI/pre-commit. `heal` is fix-flow with interactive prompt. They are complementary, not overlapping; `check` remains deferred.

### P-FR-2: Auto-hook on every CLI command

Every `project-guide` invocation (including `--help`) runs `heal` as a pre-step. Implementation point: a Click group-level callback on the `main` group that runs before any subcommand dispatch.

**Behavior:**

1. The hook is silent in the steady state (no drift → no output → no perceived overhead beyond the cheap status check).
2. The hook respects `PROJECT_GUIDE_HEALING=1` (set by `heal` itself) and skips re-entry to prevent recursion.
3. If `.project-guide.yml` is missing, the hook **does not** run heal — it lets the actual subcommand handle the missing-config case. (Otherwise `project-guide init` would fail before bootstrapping, since `heal` errors on missing config.)
4. If the user declines the prompt (answers `n`), the hook continues to dispatch the original subcommand. The original command is allowed to run even with stale templates — refusing the heal is the user's choice. (Exception: if the *user's actual command* fundamentally requires the templates that are missing, the original command's existing error path takes over — `heal` does not block.)

### P-FR-3: `--no-input` → auto-yes for `heal`

`heal` follows the existing `--no-input` contract (`should_skip_input()` from `runtime.py`). When `--no-input` is in effect (flag, env var, CI=1, or non-TTY stdin):

1. Skip the `[Y/n]` prompt; behave as if the user answered `Y` (auto-yes).
2. **Emit a one-line stderr notice** before applying changes: `Auto-healing N templates under --no-input.` This is so CI logs and embedding callers (pyve scaffolding, etc.) have a visible signal that file writes occurred — silent file writes under automation would be a surprise.
3. Apply updates and re-render `go.md` as usual.

The auto-hook also respects `--no-input` semantics. When the auto-hook fires inside a `--no-input` parent invocation, it auto-yes's the heal so the parent command can proceed.

### P-FR-4: `.gitignore` template change

`init` writes a different `.gitignore` block than today. Current behavior (per tech-spec.md `## .gitignore Management`):

```gitignore
docs/project-guide/go.md
docs/project-guide/**/*.bak.*
```

(Wait — that's incorrect. Today `go.md` is **tracked**, not gitignored; the comment in tech-spec is misleading. The actual current behavior is that only `*.bak.*` is gitignored under the target dir. Confirm this with the implementation in `cli.py:_ensure_gitignore_entry` during P.d.)

**New behavior:** `init` writes a gitignore block that ignores everything under `target_dir` *except* `go.md`. Plus the existing `*.bak.*` entry. Everything else (including `.metadata.yml`) is static bundled data and gets healed on the first `project-guide` invocation after clone.

**Why `go.md` is the one exception (and the only one):** IDE-integrated LLMs (Cursor, Claude Code, etc.) typically hide gitignored files from the LLM's view by default. Since the entire developer-LLM contract is "tell your LLM to read `go.md`," the file *must* remain visible to the LLM, which means it cannot be gitignored. The repo-history value of `go.md` is incidental and largely negative — it churns on every `mode` switch — but the tooling constraint is non-negotiable. No other file under `target_dir` has this constraint, so all of them get gitignored.

Concretely:

```gitignore
# project-guide
docs/project-guide/**
!docs/project-guide/go.md
docs/project-guide/**/*.bak.*
```

**Migration for existing consumer repos:** No migration story. Consumer repos that already track the full tree continue to do so until the developer runs `project-guide init --force`, which rewrites the `.gitignore` block. The developer is responsible for `git rm --cached` on the now-ignored paths if they want to clean up history-going-forward. (This is acceptable per the "no migration" decision at planning time.)

### P-FR-5: Mandatory CI workflow tightening

Update `.github/workflows/ci.yml` (and possibly `test.yml`) to fully gate on lint + test results. Concrete changes:

- Ensure CI triggers on `pull_request` (not just `push`) so future contributors' PRs are gated.
- Confirm exit codes propagate (no `continue-on-error: true` on lint/test steps).
- Document in `CONTRIBUTING.md` that CI must be green before merge (informal until branch protection is added).

This is **scoped to workflow correctness**, not branch protection enforcement (which is deferred per developer override). The goal is "if/when branch protection is enabled, the workflows are already PR-ready."

### P-FR-6: `SECURITY.md`

Top-level `SECURITY.md` with:

- Supported versions table (latest minor only, per typical small-OSS policy).
- Reporting channel — GitHub Security Advisories (preferred) or a contact email.
- Response expectations (acknowledge within N days; no hard SLA).

### P-FR-7: `CONTRIBUTING.md`

Top-level `CONTRIBUTING.md` with:

- Dev environment setup using `pyve` (cite the two-environment pattern from `pyve-essentials.md`).
- Code style — `ruff check` + `ruff format`, mypy clean.
- Test process — `pyve test`, 85% coverage minimum.
- PR process — fork, branch, PR, await CI green, await maintainer review.
- Release process — `plan_production_phase` for new phases, `bump-version` at end-of-phase, GitHub Release triggers `publish.yml`.
- Pointer to the `project-guide` workflow itself for substantive contributions (use `code_direct` or `code_test_first` to scope changes via stories).

### P-FR-8: `.github/dependabot.yml`

Dependabot config for two ecosystems:

- `pip` — runtime + dev dependencies, weekly schedule.
- `github-actions` — workflow action versions, weekly schedule.

Group minor + patch updates into a single PR per ecosystem to reduce noise. Major updates land as separate PRs.

---

## Technical Changes

### New module / new commands

- **`project_guide/cli.py`** — add `heal` Click command. Reuse `sync.py`'s file discovery, hash comparison, and copy-with-backup helpers; add a thin "create missing" wrapper since `sync.sync_files` today assumes existing files.
- **`project_guide/cli.py`** — add a Click group-level callback on `main` that calls `heal` before subcommand dispatch. Gate on `PROJECT_GUIDE_HEALING` env var to prevent re-entry. Skip when `.project-guide.yml` is absent (let the subcommand handle missing-config).
- **`project_guide/sync.py`** — extend with a `heal_files(config)` helper or modify `sync_files` to accept a `create_missing=True` flag. Decision deferred to implementation; favor extension over modification if the delta is small.

### Modified files

- **`project_guide/cli.py`** `_ensure_gitignore_entry()` — rewrite the gitignore block per P-FR-4.
- **`project_guide/templates/project-guide/templates/modes/`** — no template changes; `go.md` re-render is unchanged.
- **`tests/test_cli.py`** — new tests for `heal` (clean state silent, drift state prompts, `--no-input` auto-yes + stderr notice, missing-config hard error, recursion guard via env var, hook-fires-before-subcommand integration test).
- **`tests/test_sync.py`** — new tests for create-missing behavior.
- **`docs/specs/features.md`** — new functional requirement section for `heal`; CLI input section updated; `.gitignore` Management note updated; modes list / acceptance criteria / Outputs file structure updated to reflect new gitignore policy.
- **`docs/specs/tech-spec.md`** — new module/command rows in CLI Design and Cross-Cutting Concerns; gitignore block updated; CLI command count updated.
- **`README.md`** — multiple corrections needed:
  - Line 91 ("The rendered `go.md` and `.bak.*` backup files are gitignored.") — already inaccurate today (`go.md` is **not** gitignored today; `.bak.*` is); rewrite to reflect new policy: "Everything under `docs/project-guide/` is gitignored except `go.md` and `.bak.*`."
  - Line 39 ("CLI Interface - Nine intuitive commands…") — will be ten with `heal`.
  - Add a `### heal` section to Command Reference.
  - `## Quick Start` step 1 — update the "creates" list and the gitignore footnote.
  - `## Development` section — keep as-is for now (CONTRIBUTING.md is the canonical source going forward; README's section is a quick-reference summary).

### New files (production hardening)

- **`SECURITY.md`** — top-level.
- **`CONTRIBUTING.md`** — top-level.
- **`.github/dependabot.yml`** — config.
- (Possibly) **`.github/workflows/ci.yml`** edits for PR triggers.

### Dependencies

No new dependencies. `heal` reuses existing `click`, `jinja2`, `pyyaml`, `packaging`.

### Config schema

No schema bump. `heal` reads existing fields. `SCHEMA_VERSION` stays at `"2.0"`.

---

## Production Concerns

1. **Auto-yes under `--no-input` writes files without confirmation.** Mitigation: P-FR-3's stderr notice gives CI/embedding callers a visible signal. Long-term, downstream tooling (pyve scaffolding) should opt into auto-heal explicitly via env var or explicit `project-guide heal --no-input` rather than relying on the implicit auto-hook — capture this in `CONTRIBUTING.md` and `pyve-essentials.md` if relevant.
2. **Recursion guard correctness.** The `PROJECT_GUIDE_HEALING=1` env var must be set on the *current process* environment before any subcommand dispatch, not just on subprocess invocations. Test: a contrived `heal` flow that itself shells out to `project-guide` (none planned today, but the guard must hold even if introduced later). Covered by P.b's recursion-guard test.
3. **Auto-hook startup cost on `--help`.** The drift check is cheap (file stat + SHA-256 on small files) but non-zero. If users notice latency on `--help`, the hook can short-circuit on `--help`/`--version` flags before running the check. Defer this optimization unless complaints surface; record in `Future` if observed.
4. **Behavioral surprise on first post-upgrade invocation.** A user who pip-upgrades project-guide and runs any command will be prompted to heal stale templates. This is *expected* and the prompt is the UX; just confirming it's intentional.

---

## Anticipated Breaking Changes

Per the breaking-change negotiation step:

| Change | Substantive? | Decision |
|--------|--------------|----------|
| Auto-hook fires on every command (including `--help`) | Technically a UX change; not a contract change. Silent in steady state. | **Non-breaking** — minor bump suffices. |
| `.gitignore` template flips most files to ignored on fresh `init` | Only affects fresh `init` runs. Existing repos unaffected until `init --force`. | **Non-breaking** — minor bump suffices. |
| `--no-input` auto-yes writes files without explicit consent | New behavior on a new command (`heal`); doesn't change existing command behavior. | **Non-breaking** — additive. |
| Production hardening files (`SECURITY.md`, etc.) | Additive only. | **Non-breaking** — additive. |

**Anticipated version bump target: `v2.6.0` (minor).** Phase ships as one bundled release; stories within the phase run unversioned.

---

## Out of Scope

Walked with the developer. Each item is a deliberate deferral, not an oversight:

1. **Branch protection on `main`.** Deferred until contributors join — solo-dev today; ceremony cost not justified yet. Re-evaluate on first external PR.
2. **PR-only workflow for project-guide itself.** Same rationale as above — direct commits to `main` continue. CI workflows are PR-ready (P-FR-5) so the switch is one settings flip when the time comes.
3. **Migration story for existing consumer repos.** `project-guide init --force` is the documented migration; no automatic detection of "tracked-but-now-ignored" files. Developers who care about cleaning history use `git rm --cached` themselves.
4. **`project-guide check` integrity command.** Already in `Future`/`Integrity & Validation [Deferred]` in `stories.md`. `heal` is fix-flow; `check` is verify-flow; they're complementary and `check` remains deferred until a second concrete integrity rule justifies it.
5. **`--help` / `--version` short-circuit in the auto-hook.** Optimization deferred until/unless the cost is observed in practice (see Production Concerns #3).
6. **Subprocess-based recursion guard hardening.** The env-var guard is sufficient for the in-process auto-hook; if `heal` ever shells out to other `project-guide` commands, revisit.
7. **`pyve-essentials.md` update for auto-heal awareness.** If pyve's scaffolding flow needs to know about the auto-hook (e.g., to call `heal --no-input` explicitly rather than relying on the implicit hook), that's pyve's call to make. Project-guide just exposes the surface.

---

## Story Outline (Preview)

The full story breakdown lands in `stories.md` at step 7 (after this plan is approved). Anticipated stories:

- **P.a** — `heal` command: drift detection + `[Y/n]` prompt + create-missing semantics. (Owns the v2.6.0 bump at end-of-phase.)
- **P.b** — Auto-hook + recursion guard.
- **P.c** — `--no-input` auto-yes + stderr notice.
- **P.d** — `.gitignore` template change for `init`.
- **P.e** — `SECURITY.md`.
- **P.f** — `CONTRIBUTING.md`.
- **P.g** — `.github/dependabot.yml`.
- **P.h** — CI workflow tightening for PR-readiness.
- **P.i** — Doc-only: update `features.md`, `tech-spec.md`, **`README.md`** (gitignore policy, ten-command count, new `heal` command-reference entry, Quick Start corrections), append `project-essentials.md` facts (auto-heal hook contract; gitignore inversion; **the IDE-LLM-visibility constraint that forces `go.md` to be tracked**). Bundles the v2.6.0 release.

(Spike story not needed — no new integration boundary; `heal` is an extension of existing `sync.py` and `cli.py` patterns.)
