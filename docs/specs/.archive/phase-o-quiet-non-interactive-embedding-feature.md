# Change request: Quiet / machine-friendly mode for embedded invocation

**Target repo:** [`project-guide`](https://github.com/pointmatic/project-guide)  
**Consumption:** `pyve` invokes `project-guide init` / `project-guide update` from `lib/utils.sh` (`run_project_guide_init_in_env`, `run_project_guide_update_in_env`) with **`--no-input`** when refreshing scaffolding during `pyve init`, `pyve init --force`, and **`pyve update`**. Output from `project-guide` is interleaved with pyve's own **`log_info`** / **`header_box`** stream; CI and non-interactive logs can become noisy without a counterpart to **`--no-input`**.

---

## Problem statement

- **`--no-input`** correctly suppresses prompts but does not guarantee minimal progress/banner/logging on stderr/stdout.
- Embedding tools (`pyve`, CI scripts, other wrappers) need a **predictable**, **low-volume** invocation that still surfaces **hard errors**.
- Working around chatter inside pyve (silent pipelines, stripping stdout) hides legitimate diagnostics and duplicates logic in consumers.

---

## Proposed change

Add one of:

1. **`--quiet`** global option (recommended): suppress non-error progress, spinner-style updates, decorative banners when set; preserve **explicit errors** on stderr and non-zero exits on failure, **or**
2. **`--log-level error`** (alternative): aligns with logging conventions across Python CLIs.

**Minimum behavior contract when quiet:**

- Exit codes unchanged vs current behavior.
- On success: optionally **silence stdout** entirely or emit a single final line (`project-guide update: ok`) — bikeshed upstream; preference from pyve consumer: **silent stdout on success**.
- On failure: error message(s) printable to stderr unchanged or slightly more concise.

---

## Motivation

- Phase L Track 2 finding **T2-01** (`docs/specs/phase-l-pyve-polish-audit.md`).
- Cleaner integration with **`pyve update`** logs and scripted refreshes without maintenance-heavy output filtering in Bash.

---

## Suggested CLI / API shape

```text
project-guide init --no-input [--quiet|-q]
project-guide update --no-input [--quiet|-q]
```

- Document interaction with existing verbose/debug flags (`--verbose` if any) explicitly: **`--quiet` wins** when both passed, or mutually exclusive — decide at implementation time.

---

## Compatibility notes

- **Additive** optional flag → backward compatible default **off**.
- Consumers that already parse **`--no-input`** keep working.
- **`pyve`** adoption story carries **minimum `project-guide` version** after release; grep touchpoints remain `lib/utils.sh` wrappers.

**Upstream contract (canonical):** `docs/specs/features.md` → **FR-9 Quiet Mode**; implementation notes in `docs/specs/tech-spec.md` (CLI Design → Machine-quiet commands). As of **v2.5.1**, `project-guide init|update|purge --quiet` uses **silent stdout on success** and **stderr** for errors and material warnings.

---

## Pyve-side follow-up

After upstream release **`v2.5.1`** (embedded-quiet contract) or later:

- Extend `run_project_guide_init_in_env` / `run_project_guide_update_in_env` argument lists conditionally (`--quiet` when supported **or** always if minimum version bumped).
- Optional: derive minimum version alongside existing comment block citing **`--no-input` ≥ 2.2.3**.
