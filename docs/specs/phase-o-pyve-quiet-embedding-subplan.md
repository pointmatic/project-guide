# Phase O subplan — Pyve integration & embedded CLI quiet mode

Planning artifact within Phase O: ties **O.a** (bundled `pyve-essentials.md` auto-render, shipped in v2.5.0) to the remaining work driven by [`quiet-non-interactive-embedding.md`](quiet-non-interactive-embedding.md).

## Gap analysis

| Area | Current state | Target |
|------|----------------|--------|
| Pyve rules in `go.md` | Auto-rendered from bundled `pyve-essentials.md` when `pyve_installed` | Done (O.a) |
| `--no-input` | Suppresses prompts; used by pyve wrappers | Done |
| `--quiet` | Suppresses per-file progress on `init` / `update` / `purge` | Partial vs embedding spec |
| Success stdout under `--quiet` | Still prints banners, summaries, green checkmarks, idempotent `init` message | Embedding spec: **silent stdout on success** (pyve preference) |
| Errors / warnings | Mixed stdout/stderr | Failures and material warnings remain visible; prefer **stderr** for diagnostics where practical |
| `--quiet` vs `--verbose` | Only `mode` has `--verbose`; no documented precedence | Document: no conflict today; if a command gains both, **`--quiet` wins** |
| Consumer docs | `features.md` FR-9 promises “summary always shown” | Align FR-9 / tech-spec with tightened contract |

## Feature requirements (mini)

1. **`init --quiet`**: On success (including “already initialized” early exit), emit **no** ordinary stdout; errors and config-backup notices that are safety-relevant may use stderr or remain visible per FR-9 refinement.
2. **`update --quiet`**: On success, **no** celebratory stdout (including dry-run summary lines where policy says silent); keep overridden-file warnings and errors visible (stderr preferred for errors).
3. **`purge --quiet`**: On success, suppress completion banner when consistent with init/update; errors always visible.
4. **Exit codes**: Unchanged vs current behavior for each path.
5. **Tests**: Extend `tests/test_cli.py` quiet tests to assert stdout silence on success paths; preserve regression guard that errors are not swallowed.

## Technical notes

- Implementation lives in `project_guide/cli.py` (`init`, `update`, `purge`, helpers).
- May introduce small helpers (e.g. `_emit_quiet_aware`) only if it reduces branching noise; prefer minimal diff.
- `click.echo(..., err=True)` for diagnostics that must survive embedding.

## Out of scope (Phase O)

- Pyve repo changes (`lib/utils.sh` passing `--quiet`) — tracked as downstream follow-up in `quiet-non-interactive-embedding.md`.
- `--log-level` style API — deferred unless explicitly preferred later.
- Adding `--quiet` to `mode`, `status`, or other commands — not requested by embedding spec; revisit if consumers need it.
