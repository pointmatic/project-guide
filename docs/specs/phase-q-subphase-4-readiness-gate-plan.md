# phase-q-subphase-4-readiness-gate-plan.md — project-guide (Python)

Subphase Q-4 plan: **Readiness-gated local-install warning.**

Subphase Q-4 of [Phase Q (DX Improvements & Subphase Support)](phase-q-dx-subphases-plan.md). Refines contract item #2 ("Pyve-managed-hosting awareness") shipped in Subphase Q-3 (Story Q.m, v2.13.0). The Q.m local-install warning (`_warn_if_local_install_under_pyve` in [`cli.py`](../../project_guide/cli.py)) prescribes `pip uninstall project-guide` *unconditionally* once it detects a project-local install coexisting with a pyve-managed host. Q-4 makes that advice **readiness-gated** and **non-destructive** by consulting a new pyve-owned status query before ever recommending removal.

Companion input digested for this planning session: [`phase-q-subphase-4-local-install-warning-readiness-gate.md`](phase-q-subphase-4-local-install-warning-readiness-gate.md) — the cross-repo change request. It specifies the pyve-side query (`pyve self provision --status [--json]`, a coordinating addition shipped separately in the Pyve repo) and the project-guide-side messaging contract (this subphase).

---

## Gap Analysis (Subphase Q-4)

### The Q.m warning is destructive in exactly the case it should help

`_warn_if_local_install_under_pyve` ([cli.py:1573](../../project_guide/cli.py)) currently fires whenever (a) pyve was detected at init time (`config.pyve_version is not None`), (b) the running package lives under `Path.cwd()`, and (c) it sits inside a `site-packages` directory. When all three hold it emits:

```
⚠ Local project-guide install detected at …/.venv/lib/python3.14/site-packages/project_guide.
  Pyve is configured to manage project-guide globally.
  Remove the local install with: pip uninstall project-guide
```

This is wrong in two ways — and the failure is not hypothetical; it reproduced on a developer machine where a `pyve self provision` hang had prevented global hosting from ever being provisioned:

1. **The advice is destructive when the global replacement does not exist.** The warning prescribes `pip uninstall project-guide` *without verifying the global host is provisioned and runnable*. On the affected machine, `command -v project-guide` resolved **only** to the venv copy — no `~/.local/bin/project-guide` shim, no toolchain venv. Following the advice would have left the developer with **zero** working project-guide. "Remove the local install" is only safe *after* global hosting is confirmed runnable; the safe order is the inverse (`pyve self provision` → verify → *then* uninstall).

2. **It warns on the benign state and stays silent on the broken one.** A local install, by itself, works. The signal that actually matters — "is your *global* hosting ready?" — is neither checked nor mentioned. The message is inverted: noisy about the harmless state, silent about the real gap.

A local install *is* worth flagging, because pyve's internal resolver deliberately ignores `PATH` (it resolves project-guide by hosted **absolute path** — pyve's anti-shim fix), so the project-guide the developer invokes from an activated venv can silently differ from the one pyve invokes internally. But the warning must be **conditioned on global-hosting readiness**, and it must never advise removal of the only working copy.

### Project-guide must not inspect pyve internals

The naïve fix — have project-guide stat pyve's toolchain path and shim — hard-codes pyve internals into project-guide. The toolchain path is version-keyed and `XDG_DATA_HOME`-relative; the shim path can move. Any such check would rot on the next pyve layout change (`DEFAULT_PYTHON_VERSION` bump, `XDG_DATA_HOME` override). The boundary must stay clean: **pyve owns the truth about its own hosting and exposes it through a stable query; project-guide consults that query and reacts.**

### The coordinating query does not exist in pyve yet

`pyve self provision --status` is a **pyve-side addition** tracked as a separate Pyve story (Subphase N-9 / Phase P "Harden and heal Pyve"), paired with the `self provision` hang fix (Pyve Story N.bv). Project-guide therefore ships against the *contract* (exit codes `0/1/2/127`), not against a runnable query — which is exactly why graceful degradation is load-bearing: when the query is missing or too old, project-guide degrades to the conservative, non-destructive readiness-first branch and never assumes global hosting works. This lets project-guide ship first and the real cross-repo verification happen when pyve's side lands.

---

## Feature Requirements (Subphase Q-4)

### Q-4-FR-1: Readiness-gated decision logic in the local-install warning

Refactor `_warn_if_local_install_under_pyve` so that, **after** the local-install detection, it consults pyve before emitting any message. The Q.m cached pre-gate (`config.pyve_version is not None`) is **replaced** by a **live** `shutil.which("pyve")` check, so the warning correctly engages even when pyve was installed *after* `project-guide init` (closing the cache-staleness gap raised at the plan gate). Detection gates **(b)** the running package lives under `Path.cwd()` and **(c)** it sits inside a `site-packages` directory are preserved; the former gate **(a)** `config.pyve_version is not None` becomes the live pyve-on-PATH check:

```
pyve not on PATH (shutil.which("pyve") is None)  → standalone usage; NO warning (unchanged net effect)
else run: pyve self provision --status --json
  exit 0  (global ready & runnable)   → benign-duplicate notice — removal is now safe
  exit 2  (not pyve-managed here)      → NO warning (the project manages project-guide deliberately)
  exit 1  (global NOT ready)           → readiness-first guidance — NEVER advise removal
  exit 127 / OSError / any other       → readiness-first guidance (degrade safe)
```

- **The core invariant: never emit `pip uninstall` advice unless the query returns exit 0.** Exit 0 is the *only* path that recommends removal. Every other outcome is either silent (exit 2, or pyve absent) or readiness-first (exit 1, 127, subprocess error, unrecognized).
- **Message — exit 0 (benign duplicate, safe to remove):**
  ```
  A pyve-managed global project-guide (v<version>) is active; this local copy in
  <path> is redundant. Remove it with:  pip uninstall project-guide
  ```
  `<version>` is read from the `--json` payload's `project_guide.version`. If the JSON is absent or unparseable while the exit code is still 0, fall back to a version-less phrasing ("A pyve-managed global project-guide is active; …") — never block the message on the parse.
- **Message — readiness-first (exit 1 / 127 / error):**
  ```
  Running project-guide from a local install. Pyve manages project-guide globally,
  but its hosting isn't ready yet. Provision it first:
      pyve self provision
  Keep this local install until the global one is ready.
  ```
- **Graceful degradation.** A missing/old/unrecognized query (`127`, `OSError`/`FileNotFoundError`, or any non-`0`/non-`2` exit) is treated as "global not ready / coordination unavailable" → readiness-first branch. project-guide never assumes global hosting works. (A pre-`--status` pyve that returns its own argparse usage error — exit 2 — is read as "not managed → no warning", which is also non-destructive; the only path that emits removal advice remains a clean exit 0.)
- **Live detection, not cached `pyve_version` — a documented exception to Q-3 invariant (b).** Q-3's invariant (b) ("pyve detection is cached, not re-run per invocation") still holds for `status`, help text, and template branches. This guard is the deliberate exception: it uses live `shutil.which("pyve")` because correctness — never stranding a developer, and catching a pyve install that post-dates `project-guide init` — outweighs cheapness here. `shutil.which` is a cheap pre-filter that runs before any subprocess; the `--status` subprocess fires only when a local install **and** pyve-on-PATH coexist, never in the steady state. The function no longer reads `config.pyve_version`.
- **Side-effect-free probe.** `pyve self provision --status` is documented read-only/fast (no network, no provisioning). Invoke via `subprocess.run([pyve, "self", "provision", "--status", "--json"], capture_output=True, text=True, check=False)`; wrap in a try/except for `OSError` → readiness-first.

### Q-4-FR-2: Optional interactive provisioning offer (TTY, heal-scoped)

In the **readiness-first** branch, project-guide offers to run provisioning on the developer's behalf:

```
Provision pyve-managed project-guide now? [Y/n]
```

**Deliberate departure from soft-touch discipline.** Project-guide's standing rule is warn-don't-act (P.k git-push, P.o `go.md`-tracking, the Q.m warning itself): it surfaces a state and lets the developer act on their own schedule. This offer is a **sanctioned, scoped exception** — Q-4 is a special handoff for a new *tight* integration with pyve, and the recommended remedy is a single, pyve-owned command (`pyve self provision`) rather than a generic side effect. The departure is bounded precisely: project-guide **delegates** the fix to pyve's command and never performs an install itself, the offer is TTY-only and suppressed under `--no-input`, and it appears only in the readiness-first (footgun) state. This is the one place project-guide intentionally crosses from "warn" to "offer to fix," and it does so only because the fix is a clean delegation to the integration partner.

- **Accept** → shell out to `pyve self provision` (`subprocess.run([pyve, "self", "provision"], check=False)`). project-guide **delegates** to pyve's command; it MUST NOT pip-install into pyve's toolchain venv itself — pyve owns that venv and the install.
- **Decline** → leave the readiness-first message standing; no side effect.
- **Scoped to the `heal` command, not the pre-invoke auto-hook.** The readiness-first *warning text* (FR-1) fires everywhere the function runs (the auto-hook on every command **and** `heal`). The interactive *provisioning offer* fires **only** from `heal` — the explicit, user-initiated drift-repair surface. Firing a `[Y/n]` provisioning prompt from the auto-hook would hijack every `project-guide` command (`status`, `mode`, …) with a provisioning question; scoping the offer to `heal` keeps the auto-hook lightweight and matches `heal`'s existing role as the place where drift gets repaired. *(Design call surfaced for the approval gate — the change request leaves the offer's placement open; this is the least-intrusive shape consistent with the existing auto-hook discipline.)*
- **`should_skip_input()` gates the offer.** Under `--no-input` / `CI=1` / non-TTY stdin, the offer is suppressed (no prompt, no provisioning) — the readiness-first warning still prints. Default at the interactive prompt is `Y`, per the change request.

### Q-4-FR-3: Cross-repo contract + architectural-invariant documentation

Two doc surfaces (Story Q.r):

- **`features.md` Cross-Repo Contracts section.** Refine contract #2 ("Pyve-managed-hosting awareness") to describe the readiness-gated warning and its dependency on the `pyve self provision --status` query (exit-code contract `0/1/2/127`, graceful degradation, never-uninstall-unless-0). Note the two-way version coordination.
- **`project-essentials.md` "Pyve cross-repo contracts" section.** Append the Q-4 invariants after the Q-3 content:
  - **Never advise `pip uninstall project-guide` unless `pyve self provision --status` returns exit 0** (a runnable global replacement is confirmed). This is the core safety invariant.
  - **The readiness guard is the documented exception to invariant (b) "pyve detection is cached, not re-run per invocation."** This guard uses **live** detection — `shutil.which("pyve")` plus the `pyve self provision --status` probe — rather than the cached `config.pyve_version`, because correctness (never strand a developer; catch a pyve install that post-dates `init`) outweighs cheapness here. Invariant (b) still governs `status`, help text, and template branches (they read the cached value). The probe is a *readiness check*, not version detection, and `shutil.which` is a cheap pre-filter: the `--status` subprocess fires **only** when a local install (a `site-packages` copy under cwd) and pyve-on-PATH coexist. In the steady state — no local install, or an editable dogfood checkout — no subprocess fires. The per-invocation cost is bounded to the exact broken state being remediated and is transient until the user resolves it.
  - **project-guide consults the query; it never inspects pyve internals** (toolchain path, shim location). The query is the single coordination surface.
  - **The provisioning offer delegates to `pyve self provision`; project-guide never pip-installs into pyve's toolchain venv.** Same wrapper-initiates-side-effects discipline as P.k / P.o, extended: where heal *warns* about other drift, here it may *delegate* a fix to pyve's own command, but never performs the install itself.
  - **Two-way version coordination.** project-guide's gating requires **pyve ≥ the release that ships `pyve self provision --status`**; below that it degrades to readiness-first. pyve adopting this readiness-aware messaging pins **project-guide ≥ v2.15.0** (mirrors the existing `≥ 2.13.0` hosting pin).

---

## Technical Changes (Subphase Q-4)

- **Edits only to `cli.py`, tests, and two spec docs.** No `.project-guide.yml` schema change, no metadata change, no new CLI subcommand, no new runtime dependency (`subprocess` already imported at [cli.py:18](../../project_guide/cli.py); `shutil.which` already used at [cli.py:2011](../../project_guide/cli.py)).
- **Files touched** (source of truth, not installed copies):
  - **Edited**: `project_guide/cli.py` — refactor `_warn_if_local_install_under_pyve` into readiness-gated decision logic (FR-1); add a `heal`-scoped provisioning offer (FR-2). Drop the `config.pyve_version` early-return in favor of a live `shutil.which("pyve")` gate (closes the cache-staleness gap). Likely shape: a pure helper that classifies readiness from the `--status` result and returns the appropriate message/branch, the shared warning emitter called by both the auto-hook and `heal`, and a `heal`-only "maybe offer provisioning" step. Keep `_running_install_path()` monkeypatchable; add a thin `shutil.which("pyve")` lookup and a `subprocess.run` call factored so tests can mock it.
  - **Edited**: `docs/specs/features.md` — Cross-Repo Contracts #2 refinement (Q.r).
  - **Edited**: `docs/specs/project-essentials.md` — Q-4 invariants appended to the Pyve cross-repo contracts section (Q.r).
  - **Bumped**: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` — once, on the Q-4 release story (Q.s).
- **Installed-copy propagation.** `_warn_if_local_install_under_pyve` lives in `cli.py` (package code), not a template, so no `project-guide update` is required for the code change. The `project-essentials.md` edit flows into the rendered `go.md` via the auto-render path, so Q.r re-renders `go.md` and spot-checks it.
- **Test impact.** New cases in `tests/test_cli.py` exercising the readiness branches by mocking `shutil.which`, `_running_install_path`, and `subprocess.run`: exit 0 → benign/safe-to-remove (with and without a parseable JSON version); exit 2 → silent; exit 1 → readiness-first, no uninstall advice; exit 127 / `OSError` → readiness-first (degrade safe); pyve-not-on-PATH → silent; the existing gates (`pyve_version is None`, not-under-cwd, not-site-packages, skip-input) → silent; provisioning offer from `heal` accepted → `pyve self provision` invoked; declined → not invoked; under `--no-input` → no prompt, no invoke. The parametrized render-mode regression remains green (no template change).

---

## Production Concerns

**Bounded subprocess on the footgun path only.** Q-4 introduces a per-invocation `pyve self provision --status` subprocess — but gated behind the local-install detection, so it fires only in the broken state it remediates and never in the steady state or the editable dogfood checkout. The probe is documented read-only/fast (no network, no provisioning). The provisioning offer's `pyve self provision` shell-out is TTY-only, `heal`-scoped, off under `--no-input`, and delegates to pyve rather than performing any install itself. No new security boundary, no network surface, no state-format change. (Per the developer's direction, the Phase-Q production-readiness checklist was walked at the start of the phase and needs no re-walk for this subphase.)

---

## Anticipated Breaking Changes

**None substantive.** Walked at Step 5:

- **The warning's message and trigger conditions change**, but the warning is **operator-facing diagnostic output**, not a documented public-API contract (parallel to the log-format worked example in the Version Cadence breaking-change rule — technically-but-trivially breaking at most, and here strictly an improvement: the old message could *strand* a developer; the new one cannot).
- **No change to any `project-guide` command's exit code, arguments, or output schema.** The subprocess + branching is internal to the warning's decision logic.
- **The new pyve dependency degrades safely.** Environments without `pyve self provision --status` (standalone, or pyve too old) see no destructive advice — they fall to the readiness-first branch or stay silent.
- **The provisioning offer is additive and opt-in** (TTY, `heal`-scoped, default-`Y` but suppressed under `--no-input`).

No version-bump escalation triggered → **minor**.

---

## Anticipated Version Bump Target

**v2.15.0 — minor.** New readiness-gated behavior + an interactive provisioning convenience, both additive; the messaging-contract refinement and the published cross-repo dependency are feature surfaces. Per Version Cadence "Feature or improvement → minor."

Bundled release at end of Subphase Q-4; bumped exactly once on the last story (Q.s).

Subphase Q-1 = v2.11.0; Q-2 = v2.12.0; Q-3 = v2.13.0; Q-2/Q-3 doc-fix tail closed at v2.14.0 (Q.p); **Q-4 = v2.15.0**.

---

## Out of Scope

Walked at the gate; deferred items:

- **Pyve-side `pyve self provision --status [--json]` implementation.** Lives in the Pyve repo (Subphase N-9 / Phase P), paired with the `self provision` hang fix (Pyve Story N.bv). Project-guide's deliverable is the consuming side, written against the exit-code contract; the real cross-repo integration verification happens when pyve's query ships.
- **Pyve-side minimum-version pin.** Pyve pins `project-guide ≥ v2.15.0` once this subphase ships; that edit lives in the Pyve repo.
- **project-guide performing the toolchain install itself.** The provisioning offer delegates to `pyve self provision`; project-guide never pip-installs into pyve's venv. Pyve owns that venv and the package install.
- **A provisioning offer in the pre-invoke auto-hook.** The interactive offer is `heal`-scoped to avoid hijacking every command; the readiness-first *warning* still fires from the hook. (Revisit only if field use shows the heal-scoped offer is too easy to miss.)
- **Runtime pyve version re-detection / a `project-guide refresh-detection` surface.** Still deferred from Q-3 (YAGNI). The readiness probe is a separate, narrowly-gated subprocess, not a general re-detection path.
- **Richer `--json` consumption beyond `project_guide.version`.** The exit-0 message reads only the hosted version for display; the rest of the `--json` schema (toolchain runnable/version, shim path) is available to future consumers but unused here.
- **Subphase Q-5 and beyond.** Each future Q-N subphase planned via its own `plan_production_phase` session.

---

## Implementation Strategy

Three stories in Subphase Q-4, executed in document order:

1. **Q.q — Readiness-gate the local-install warning (implementation + tests).** Refactors `_warn_if_local_install_under_pyve` into the readiness-gated decision logic (FR-1) and adds the `heal`-scoped provisioning offer (FR-2). Adds the branch-coverage tests. No doc/contract edits, no version bump.
2. **Q.r — Cross-repo contract + invariant doc sync (FR-3).** Refines `features.md` contract #2 and appends the Q-4 invariants to `project-essentials.md`'s Pyve cross-repo contracts section; re-renders `go.md` and spot-checks. No code change, no version bump.
3. **Q.s — v2.15.0 Subphase Q-4 bundled release.** Bumps `project_guide/version.py`, `pyproject.toml`, adds `## [2.15.0]` CHANGELOG entry covering Q.q + Q.r; cross-references this plan and the change request. Closes Subphase Q-4.

Stories within Subphase Q-4 carry **no version in their title** until Q.s.

**Story-letter continuity** across the Q-3 → Q-4 boundary: Q-3's release closed at `Q.n` (v2.13.0), then `Q.o`/`Q.p` landed as post-release tail stories (Q.p owning the v2.14.0 bump). Q-4 picks up at **`Q.q`** — the next monotonic letter. Per the `_phase-letters.md` Subphases rule, story letters do not reset across subphase boundaries.

**No upstream dependency within project-guide.** Q-1/Q-2/Q-3 and the Q.o/Q.p tail have all shipped; Q-4 implementation can begin immediately after approval. The pyve-side query is *not* a blocker — graceful degradation means project-guide ships and degrades safely until pyve's `--status` lands.

---

## Acceptance Criteria (Subphase Q-4)

1. `_warn_if_local_install_under_pyve` gates on a **live** `shutil.which("pyve")` (not cached `config.pyve_version`), then consults `pyve self provision --status` after detecting a local install, and emits `pip uninstall` advice **only** on exit 0; exit 1 / 127 / subprocess error → readiness-first guidance with no removal advice; exit 2 and pyve-not-on-PATH → silent. A pyve install that post-dates `project-guide init` is correctly detected.
2. Graceful degradation verified: a missing/erroring query degrades to the readiness-first (non-destructive) branch.
3. The `heal`-scoped provisioning offer shells out to `pyve self provision` on accept, does nothing on decline, and is suppressed under `--no-input`; the readiness-first warning text still fires from the auto-hook on every command.
4. `features.md` Cross-Repo Contracts #2 reflects the readiness-gated warning and the `--status` query dependency.
5. `project-essentials.md` Pyve cross-repo contracts section carries the Q-4 invariants (never-uninstall-unless-0; the bounded `--status` exception to invariant (b); consult-the-query-never-inspect-internals; delegate-don't-install; two-way version coordination), and the rendered `go.md` reflects them.
6. New tests cover all readiness branches and the provisioning offer; `pyve test` and `pyve testenv run ruff check project_guide/ tests/` pass on the v2.15.0 commit.
7. `CHANGELOG.md` `## [2.15.0]` entry dated, describes the readiness-gated warning + provisioning offer as one bundled release; cross-references [`phase-q-subphase-4-local-install-warning-readiness-gate.md`](phase-q-subphase-4-local-install-warning-readiness-gate.md) and this plan.
