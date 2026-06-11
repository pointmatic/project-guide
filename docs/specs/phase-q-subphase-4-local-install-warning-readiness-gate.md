# Change request: Readiness-gate the local-install warning — coordinate via a pyve hosting-status query

**Target repo:** [`project-guide`](https://github.com/pointmatic/project-guide) (primary), with a coordinating addition in [`pyve`](https://github.com/pointmatic/pyve).
**Consumption:** Refines contract item #2 ("Pyve-managed-hosting awareness") of [`pyve-toolchain-hosting.md`](pyve-toolchain-hosting.md). Under the pyve-hosted model, project-guide is hosted once in pyve's toolchain venv and shimmed onto `~/.local/bin`. When a *second*, per-project copy is also pip-installed into a project `.venv`, project-guide warns. This request makes that warning **readiness-gated** and **non-destructive**, by introducing a stable pyve query project-guide can consult instead of guessing.

---

## Problem statement

Running `project-guide <cmd>` from inside an activated project `.venv` that has a local `project-guide` pip install emits, today:

```
⚠ Local project-guide install detected at …/.venv/lib/python3.14/site-packages/project_guide.
  Pyve is configured to manage project-guide globally.
  Remove the local install with: pip uninstall project-guide
```

This is wrong in two ways, and the failure is not hypothetical — it reproduced on a developer machine where the global hosting was **not** provisioned (a `pyve self provision` hang had prevented it):

1. **The advice is backwards and currently destructive.** The warning prescribes `pip uninstall project-guide` *without verifying the global replacement exists and runs*. On that machine `command -v project-guide` resolved **only** to the venv copy — there was no `~/.local/bin/project-guide` shim and no toolchain venv. Following the advice would have left the developer with **zero** working project-guide. "Remove the local install" is only safe *after* global hosting is provisioned and runnable; the safe order is the inverse (`pyve self provision` → verify → *then* uninstall).

2. **It warns on the benign condition and stays silent on the broken one.** A local install, by itself, works. The signal that actually matters — "is your *global* hosting ready?" — is neither checked nor mentioned. The message is inverted: noisy about the harmless state, silent about the real gap.

A local install *is* worth flagging, because pyve's internal resolver deliberately ignores `PATH` (it resolves project-guide by hosted **absolute path** — pyve's anti-shim fix), so "the project-guide the developer invokes from the activated venv" can silently differ from "the one pyve invokes internally." But the warning must be **conditioned on global-hosting readiness**, and it must never advise removal of the only working copy.

---

## Proposed change

The fix has two sides. Project-guide must not reach into pyve's private filesystem layout (the toolchain path is version-keyed and `XDG_DATA_HOME`-relative; the shim path can move) — that would hard-code pyve internals into project-guide and rot on the next pyve layout change. Instead, **pyve owns the truth about its own hosting and exposes it through a stable query; project-guide consults that query.**

### Pyve side (coordinating addition — new)

Add a stable, machine-readable hosting-status query that any tool can call **without** a project context and **without** knowing pyve's internal paths:

```text
pyve self provision --status [--json]
```

- **Exit codes** (the contract surface project-guide keys off):
  - `0` — pyve-managed hosting is **ready**: toolchain venv runnable **and** the hosted `project-guide` shim runnable.
  - `1` — pyve manages hosting but it is **not ready** (never provisioned, or provisioned-but-broken — e.g. a dangling shim / dead-shebang interpreter).
  - `2` — pyve does **not** manage project-guide hosting in this context (project explicitly manages it via `.project-guide.yml` deps source, or hosting is disabled). "Not my department."
  - `127` / command-not-found — pyve absent or too old to support the query (see graceful degradation below).
- **Runnability, not existence.** The status MUST execute the artifacts (`python --version`, `project-guide --version`) to classify them, per pyve's own "health checks must probe runnability" rule — a dangling symlink or dead shebang passes `[[ -x ]]` but cannot run, and reporting it "ready" is exactly the corruption that strands a developer.
- **`--json` payload** (optional, for richer consumers):
  ```json
  {
    "pyve_managed": true,
    "toolchain":     { "provisioned": true, "runnable": true, "version": "3.14.5" },
    "project_guide": { "hosted": true, "runnable": true, "version": "2.13.1",
                       "shim": "/Users/me/.local/bin/project-guide" }
  }
  ```
- Read-only, side-effect-free, fast (no network, no provisioning). It is the read-only sibling of `pyve self provision`; reuse the same hosting predicates `pyve check` already calls (`pyve_toolchain_venv_dir`, `pyve_project_guide_is_hosted`) but upgraded to the runnability probe.

### Project-guide side (this request)

When project-guide detects it is running from a **local (non-hosted)** install, gate the message on the query:

```text
pyve not on PATH                      → standalone usage; NO warning (unchanged)
else status = `pyve self provision --status`:
  exit 2  (not pyve-managed here)      → NO warning (the project manages project-guide deliberately)
  exit 0  (global ready & runnable)    → benign-duplicate notice — removal is now safe:
        "A pyve-managed global project-guide (v2.13.1) is active; this local copy in
         .venv is redundant. Remove it with:  pip uninstall project-guide"
  exit 1 or 127 (global NOT ready)     → readiness-first guidance — NEVER advise removal:
        "Running project-guide from a local .venv install. Pyve manages project-guide
         globally, but its hosting isn't ready yet. Provision it first:
             pyve self provision
         Keep this local install until the global one is ready."
```

- **Never advise `pip uninstall` unless the query returns `0`.** This is the core invariant.
- **Graceful degradation.** If the query is missing/unrecognized (`127`, or a pyve too old to support `--status`), treat it as "global not ready / coordination unavailable" and fall through to the **readiness-first** branch — the conservative, non-destructive default. project-guide never assumes global hosting works.
- **Optional convenience (TTY only):** in the not-ready branch, project-guide MAY offer to run provisioning on the developer's behalf — `Provision pyve-managed project-guide now? [Y/n]` → shell out to `pyve self provision`. It MUST delegate to that command and MUST NOT pip-install into pyve's toolchain venv itself: pyve owns that venv and the package install. Off by default in non-interactive contexts.

---

## Coordination mechanism (summary)

```
project-guide (running from local .venv)
        │
        │  is `pyve` on PATH?  ── no ──▶ standalone; no warning
        │  yes
        ▼
   pyve self provision --status        ◀── single source of truth, pyve-owned,
        │                                   layout-agnostic, runnability-probed
        ├─ exit 0 ▶ global ready    ▶ "redundant local copy; safe to pip uninstall"
        ├─ exit 1 ▶ not ready       ▶ "run `pyve self provision` first; keep local install"
        │           (127 → same as 1: degrade safe)            └─ optional: offer to run it now
        └─ exit 2 ▶ not pyve-managed ▶ no warning
```

The boundary stays clean: **pyve** is the only component that knows where its toolchain lives, whether it is provisioned, and whether the hosted package runs; **project-guide** asks and reacts, never inspects pyve internals, never installs into pyve's venv.

---

## Motivation

- **Stops a data-loss-class footgun:** the current message can direct a developer to delete their only working project-guide. Readiness-gating makes the destructive advice impossible to emit when it would be destructive.
- **Surfaces the signal that matters** (global-hosting readiness) instead of the benign one (a harmless duplicate).
- **Keeps the cross-repo contract decoupled:** a single documented query replaces any temptation for project-guide to stat pyve's version-keyed toolchain path or shim — which would silently break on a `DEFAULT_PYTHON_VERSION` bump or an `XDG_DATA_HOME` override.
- **Reusable beyond this warning:** a machine-readable `pyve self provision --status` is useful to any tool (CI gates, editor integrations, future plugins) that needs to know whether pyve hosting is ready, without parsing the human-formatted `pyve check` output.

---

## Suggested CLI / API shape

```text
# pyve (new): read-only, project-independent, runnability-probed
pyve self provision --status          # exit 0 ready / 1 not-ready / 2 not-managed
pyve self provision --status --json   # machine-readable detail (schema above)

# project-guide (changed): the bare command, gated internally on the query
project-guide git-push <branch>       # the warning path that triggered this request
project-guide <any-cmd>               # same gating wherever the local-install warning is emitted
```

No new project-guide **subcommand** is required — the change is in the warning's decision logic plus the call-out to the pyve query.

---

## Compatibility notes

- **Standalone project-guide (no pyve): unchanged.** `pyve` absent → no warning, exactly as today.
- **Additive on the pyve side:** `pyve self provision --status` is a new flag on an existing subcommand; no behavior change to bare `pyve self provision`.
- **Two-way version coordination:**
  - project-guide's new gating requires **pyve ≥ the release that ships `pyve self provision --status`**; below that it degrades to the safe readiness-first branch (never advises removal).
  - pyve adopting project-guide's readiness-aware messaging pins **project-guide ≥ the release implementing this request** (mirrors the existing `≥ 2.13.0` hosting pin).
- **No state-format change:** `.project-guide.yml` and the toolchain layout are untouched; this is purely a status surface + messaging contract.

---

## Pyve-side follow-up

After project-guide ships the readiness-gated warning, on the pyve side:

- **New story (Subphase N-9 / Phase P "Harden and heal Pyve"):** add `pyve self provision --status [--json]` — read-only, runnability-probed (reuse the `_compose_check_pyve_hosting` predicates, upgraded from `[[ -x ]]` to an executed `--version` probe per the "health checks must probe runnability" essential). Exit-code contract `0/1/2`; bats coverage for ready / not-provisioned / provisioned-but-broken (dangling shim) / not-managed.
- This pairs with **Story N.bv** (the `self provision` hang fix) — together they make provisioning both *non-hanging* and *introspectable*, so neither pyve nor project-guide has to guess whether hosting is ready.
- Pin `project-guide ≥ <release>` once the upstream change lands; document the `--status` contract in pyve's project-essentials alongside the `.project-guide.yml` and hosting entries.
