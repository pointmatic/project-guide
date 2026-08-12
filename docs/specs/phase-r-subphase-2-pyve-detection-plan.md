# Subphase R-2 Plan — pyve detection must not silently strip the Pyve guidance

**Phase:** R — Quality of Life Improvements and Bug Fixes
**Subphase:** R-2 — Pyve Detection & Render Gate
**Change request:** [`pyve-detection-render-gate.md`](pyve-detection-render-gate.md) (incoming from the pyve repo)
**Planned:** 2026-08-12 via `plan_production_phase`
**Anticipated version bump target:** **`v2.20.0`** (minor — additive + bug fix)

---

## Production-readiness waiver

The Step 2 checklist was walked once for Phase R during Subphase R-1 planning and scored **6 of 8**. Branch protection and PR-based workflow remain **deliberately waived** for a sole-maintainer repo (see [`phase-r-subphase-1-shell-completion-plan.md`](phase-r-subphase-1-shell-completion-plan.md) § Production-readiness waiver). No item changed between subphases; the waiver carries forward.

---

## Problem statement

`project-guide init` probes for pyve by bare name and caches the raw stdout:

```python
# cli.py:255
subprocess.run(['pyve', '--version'], capture_output=True, text=True, timeout=5)
```

That cached value then gates **content**, not merely display. Every render site derives `pyve_installed=config.pyve_version is not None`, and:

```python
# render.py:210
if not pyve_installed:
    return ""
```

So a **single detection miss at init permanently strips the entire Pyve guidance section from `go.md`** — roughly 80 lines — and nothing ever re-detects. Exit codes stay 0. Nothing warns. The loss is visible only by diffing against a correct render.

**Why that is the worst possible shape.** The omitted content is exactly the guardrail: use `pyve test` not `pyve run pytest`; the two-environment isolation rule; *don't* `pip install -e ".[dev]"` into the main venv; `python` never `python3`. A project in this state hands its LLM a guide that never mentions pyve — so the LLM does the plausible wrong thing, and the guidance that existed to prevent precisely that is the thing that went missing.

**Staleness is benign; a false null is the defect.** Because the gate is a null check rather than a version comparison, an out-of-date cached value still renders correctly — this repo carries `pyve version 2.6.2` against a running 3.2.2 and renders fine. The failure is binary, not gradual.

### Why detection fails in practice

1. **A `pyve self install` layout** — pyve lives at `~/.local/bin/pyve`, and that directory reaching `PATH` was itself unreliable until recently (pyve story P.ak).
2. **A development checkout driven by `./pyve.sh`** — nothing puts `pyve` on `PATH`, even though pyve is manifestly present and *is the thing running the init*.

This mirrors Subphase R-1's defect 2 exactly, with the arrows reversed: there, a pyve-emitted snippet could not find `project-guide` by bare name; here, project-guide cannot find `pyve` by bare name. In both cases the tool doing the looking already had a better answer available and did not use it.

---

## Findings that constrain the fix

### Finding 1 — "re-detect on every render" would re-open the Q.t hang

The request's item 2 asks to re-detect at every render site. The four sites are `init` (cli.py:272), `set_mode` (694), `update` (1136), and **`_apply_heal` (1216)**.

`_apply_heal` is invoked by the **pre-invoke auto-hook on every command**, including `--help` and `--version`. Putting a pyve subprocess there means a probe before literally every invocation — the exact failure class of **Story Q.t (v2.15.1): "Fix pre-invoke hang — bound the `pyve self provision --status` probe."** That probe hung in the field, and the fix was to bound it to `timeout=5` *and* narrow it to fire only in one specific state.

**Decision:** re-detect on `update` and on an explicit `mode <name>` switch. **Never in `_apply_heal`.** The auto-hook stays subprocess-free.

### Finding 2 — the request contradicts a documented invariant, but the invariant anticipated it

`project-essentials.md` § Pyve cross-repo contracts, invariant **(b)**:

> Pyve detection is cached, not re-run per invocation… Do not add per-invocation pyve probing; **if a refresh is ever needed, do it explicitly (e.g., on `update`), not implicitly on every command.**

The invariant's own escape clause names `update` as the sanctioned refresh point. Scoping refresh to `update` + explicit `mode` switch lands inside it. Invariant (b) must still be **amended** to record the second sanctioned refresh point alongside the existing Q-4 readiness-gate exception — that is a deliverable of this subphase, not an afterthought.

### Finding 3 — no cross-repo coordination is required

`pyve_version` is **not** in the `.project-guide.yml` field subset pinned by pyve (`version`, `installed_version`, `target_dir`, `current_mode`). Changing its stored format and adding a sibling field are therefore unilateral changes, not coordinated ones.

Adding `pyve_installed` is **additive-with-default**, so per the config-schema policy it does **not** bump `SCHEMA_VERSION`.

---

## Decisions taken at planning time

| Decision | Choice | Rationale |
|---|---|---|
| **Refresh sites** | `update` + explicit `mode <name>`; never `_apply_heal` | Inside invariant (b)'s escape clause; keeps the auto-hook subprocess-free (Finding 1) |
| **Render gate** | Persist `pyve_installed` as its own boolean field | Decouples "should the guidance render?" from "which pyve was seen?" — deriving the first from the second is what turns a detection miss into content loss |
| **Sticky-true semantics** | Detection may turn the flag **on**, never **off** | See below — this is the core of the fix |
| **Host-supplied version** | `--pyve-version` flag + `PYVE_VERSION` env var, **`init` only** | Mirrors `--project-name`'s resolution chain. Later changes are handled by re-detection, not by more flags |
| **`--project-name` parity** | **Not** elevated to other commands | Different fact class: identity (stable, deliberately changed) vs. environment (changes on its own). Symmetric flags would imply a symmetry that does not exist |
| **Detection miss** | Warn on stderr | A silent `null` is indistinguishable from a deliberate non-pyve project |
| **Stored format** | Bare `"3.2.2"`, reader tolerates the legacy `"pyve version 3.2.2"` form | Removes the re-parse at display time and makes the field comparable |

### The sticky-true rule

This is the load-bearing invariant of the subphase:

> **Automatic detection may only ever set `pyve_installed` to `true`. It never sets it to `false`.**

- At `init`, the flag is set from the host-supplied value if present, else from detection. A miss writes `false` **and warns loudly**.
- At `update` / `mode`, a **successful** detection sets `true` and writes back. A **failed** detection leaves the existing value untouched and does not warn (absence is the steady state for non-pyve projects).
- Turning it off is an **explicit user action** — hand-editing `.project-guide.yml`.

Consequence: once a project has seen pyve even once, no subsequent probe failure can ever strip the guidance again. The false-null failure mode becomes unreachable after first success, and recoverable before it.

**Accepted trade:** a project that genuinely stops using pyve keeps rendering the section until the developer opts out. That is the benign direction of the asymmetry — irrelevant guidance is noise; missing guidance is a removed guardrail.

### Migration default

An existing `.project-guide.yml` has no `pyve_installed` key. On read, it defaults to `config.pyve_version is not None` — exactly today's derived behavior — so no existing project changes behavior at the moment of upgrade. It changes on the next `update` / `mode`, which is the intended repair.

---

## Production concerns

- **A re-render that newly *adds* the Pyve section is a content change to a managed file.** `go.md` is regenerated output, not user-owned, so the existing hash-comparison machinery covers it. Worth an explicit confirmation during implementation that no `.bak` proliferation results.
- **Do not reintroduce an unbounded subprocess.** Any probe added by this subphase inherits the Q.t discipline: bounded `timeout`, every exception class caught, failure degrades to "leave the cached value alone."
- **The warning must not become noise.** It fires on a detection miss at `init` — a once-per-project event — not on every refresh failure.

---

## Anticipated breaking changes

**None.** Per Step 5 negotiation:

| Change | Assessment |
|---|---|
| New `pyve_installed` config field | Additive with a behavior-preserving default → not breaking, no `SCHEMA_VERSION` bump |
| `pyve_version` stored bare instead of raw stdout | Reader tolerates both forms; field is not in the pyve-pinned subset → not breaking |
| New `--pyve-version` flag / `PYVE_VERSION` env var | Purely additive; callers that ignore it keep today's behavior |
| Affected projects gain ~80 lines in `go.md` on next render | This *is* the bug fix. `go.md` is generated output, not a public API |

Target: **minor**, **`v2.20.0`**.

**Multi-release note.** Phase R now carries three release tags — `v2.18.1` (R.a), `v2.19.0` (Subphase R-1), `v2.20.0` (Subphase R-2). This is the documented multi-release exception rather than the preferred single-bundle shape, driven by the subphases being independently shippable fixes to unrelated surfaces.

---

## Story breakdown

Story letters continue monotonically from Subphase R-1's last story (R.i).

| ID | Story | Notes |
|---|---|---|
| **R.j** | Decouple the render gate — persist `pyve_installed` with sticky-true semantics | The core fix. Everything else is reachability and visibility |
| **R.k** | Host-supplied version — `--pyve-version` / `PYVE_VERSION` on `init` | Removes the guess where the caller already knows |
| **R.l** | Re-detect on `update` and explicit `mode <name>` | Converts permanent to transient. Explicitly **not** `_apply_heal` |
| **R.m** | Warn loudly on a detection miss at `init` | Converts invisible to visible |
| **R.n** | Store a bare version string; tolerant legacy reader | Retires the `_pyve_version_token` re-parse |
| **R.o** | **`v2.20.0` Subphase R-2 bundled release** | Docs incl. the invariant (b) amendment; CHANGELOG; version bump |

**Ordering rationale.** R.j lands first because the sticky-true flag is what makes every later story safe: once the gate can no longer be turned off by a failed probe, adding re-detection (R.l) cannot regress anything. R.m before R.n so the observable-behavior fixes precede the storage-format cleanup.

**No spike.** Unlike R-1, nothing here is unproven — every affected line is identified and the mechanisms are ordinary config and subprocess work.

---

## Out of scope

- **Auto-detection in `_apply_heal` / the auto-hook.** Deliberately excluded (Finding 1). The Q.t hang is recent enough to be a live lesson.
- **Elevating `--project-name` to `update` / `mode`.** Different fact class; no demand; trivially additive later if demand appears.
- **A `pyve_essentials: auto|always|never` opt-out setting.** Considered as an alternative gate design — render by default, opt out explicitly. Rejected for now because sticky-true achieves the safety goal without adding ~10KB to every non-pyve project's `go.md`. Revisit if the sticky-true flag proves insufficient.
- **Reducing the size of the rendered Pyve section.** The ~10KB cost of `pyve-essentials.md` in every `go.md` is real but belongs to Story R.z's token-budget work, not here.
- **The pyve-side coordinating change.** Passing `--pyve-version` from `run_project_guide_init_in_env` (`lib/project_guide.sh`) lands in the pyve repo, gated on `v2.20.0` and a min-version check.
- **Validating that a supplied `--pyve-version` is truthful.** The host tool is trusted; project-guide does not second-guess it, exactly as it does not second-guess `--bin` in Subphase R-1.
