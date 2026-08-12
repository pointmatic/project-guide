# Change request: a failed pyve detection silently and permanently strips the Pyve guidance from `go.md`

**Target repo:** [`project-guide`](https://github.com/pointmatic/project-guide).
**Consumption:** One item below (the host tool supplying its own version) needs a coordinating pyve change — a flag on the `project-guide init` invocation in `run_project_guide_init_in_env` (`lib/project_guide.sh`) — and would carry a min-version dependency. The other four are self-contained upstream fixes with no pyve-side change.

---

## Problem statement

`project-guide init` detects pyve by shelling out to a bare `pyve --version` on `PATH` and caches the raw stdout in `.project-guide.yml`:

```python
# cli.py — init
detected_pyve_version: str | None = None
try:
    pyve_result = subprocess.run(['pyve', '--version'], capture_output=True, text=True, timeout=5)
    if pyve_result.returncode == 0:
        detected_pyve_version = pyve_result.stdout.strip()
except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
    detected_pyve_version = None
```

That cached value then gates **content**, not just display:

```python
# every render site: init, update, mode
pyve_installed=config.pyve_version is not None

# render.py — _read_pyve_essentials
if not pyve_installed:
    return ""
```

So when detection fails once, at init, the rendered `go.md` **permanently omits the entire Pyve guidance section** — and nothing ever re-detects.

### Measured impact

Two projects, identical except whether `pyve` was on `PATH` at `project-guide init`:

| | `pyve_version` | `go.md` |
|---|---|---|
| pyve on PATH | `pyve version 3.2.2` | 675 lines |
| pyve off PATH | `null` | 595 lines |

The 80 missing lines are the whole block:

```
## Project Essentials
### Pyve Essentials
#### Workflow rules — pyve environment conventions
#### Named test environments (`[tool.pyve.testenvs]`)
#### `pyve update` vs. `pyve init --force`
#### LLM-internal vs. developer-facing invocation
#### Python invocation rule
#### `requirements-dev.txt` story-writing rule
#### Editable install and testenv dependency management
```

**It never recovers.** All three render sites read `config.pyve_version` rather than re-detecting. Verified empirically: install pyve *after* the bad init, then run `project-guide update` **and** `project-guide mode <x>` — `pyve_version` stays `null`, the section stays absent. Every command exits 0; nothing warns.

### Why this is worse than it sounds

The omitted content is precisely the guidance that stops an LLM from damaging the environment: use `pyve test` rather than `pyve run pytest`; the two-environment isolation rule; *don't* `pip install -e ".[dev]"` into the main venv; `python` never `python3`; and the LLM-internal vs. developer-facing invocation convention. A project in this state hands its LLM a guide that never mentions pyve at all — so the LLM does the plausible wrong thing, silently, and the guide that existed to prevent exactly that is the thing that went missing.

Note that **staleness is benign**; a *false null* is the defect. Because the gate is a null check rather than a version comparison, an out-of-date cached value still renders the section correctly. (pyve's own repo carries `pyve_version: pyve version 2.6.2` against a running 3.2.2 and renders fine.) The failure mode is binary, not gradual.

### Why detection fails in practice

`subprocess.run(['pyve', ...])` assumes pyve is reachable by bare name. Two routine situations where it is not:

1. **A `pyve self install` layout.** pyve lives at `~/.local/bin/pyve`, and that directory reaching `PATH` was itself unreliable until very recently (pyve story P.ak: only `pyve self install` wrote the entry; Homebrew installs, `self provision`, `check --fix`, and the lazy ensure path all created shims there without it).
2. **A development checkout driven by `./pyve.sh`.** Nothing puts `pyve` on `PATH`, so the subprocess cannot find it — even though pyve is manifestly present and running the init.

This is the same failure class as [shell-completion-ownership.md](shell-completion-ownership.md)'s defect 1, mirrored: there a pyve-emitted snippet could not find `project-guide` by bare name; here project-guide cannot find `pyve` by bare name. In both cases the tool doing the looking already had a more reliable answer available and did not use it.

---

## Proposed change

### 1. Let the host tool supply the fact

pyve invokes `project-guide init` and knows its own version with certainty. Accept it directly and skip the guess:

```
project-guide init --pyve-version 3.2.2
```

(or a `PYVE_VERSION` environment variable, if a flag is unwelcome on the init surface). When supplied, it wins outright; when absent, fall back to today's detection. This is the same shape as `--bin` in the completion request: **project-guide owns the rendering decision; the host tool supplies the fact it is uniquely positioned to know.**

### 2. Re-detect on every render, not once at init

`pyve_version` is a **cache**, so treat it as one: refresh it during `update` / `mode` / any re-render, and write the refreshed value back to `.project-guide.yml`. A machine that installs pyve after the fact should gain the section on the next render rather than being stuck forever. This alone converts a permanent failure into a transient one.

### 3. Do not derive a capability flag from a version string

`pyve_installed` and `pyve_version` answer different questions — "should the Pyve guidance render?" and "which pyve was seen?". Deriving the first from `is not None` on the second is what turns a *detection miss* into *content loss*. Consider persisting the boolean explicitly, or gating rendering on something more durable than a one-shot probe result.

### 4. Fail loudly

A detection failure currently writes `null` and prints nothing. It should warn on stderr — something like *"pyve not found on PATH; the Pyve guidance section will be omitted from go.md. Re-run `project-guide update` once pyve is available."* A silent `null` is indistinguishable from a deliberate non-pyve project.

### 5. Store a bare version, not raw stdout

The field currently holds the whole `pyve --version` line (`"pyve version 2.6.2"`), which is why `_pyve_version_token()` exists to re-parse it at display time. Storing `"2.6.2"` removes the parser and makes the field usable for comparison. Keep tolerating the legacy raw-string form when reading, since existing `.project-guide.yml` files carry it.

---

## Motivation

- **A silent, permanent, content-level failure is the worst shape a bug can take.** Nothing in the affected project ever reports a problem: exit codes are 0, the file exists, and the missing content is only visible by diffing against a correct render. Items 2 and 4 each independently downgrade it to recoverable-and-visible.
- **The guidance is safety-critical to its actual audience.** `go.md` is read by an LLM that is about to modify the project's environment. Losing "use `pyve test`, don't install into the main venv" is not a documentation gap; it is the removal of a guardrail.
- **Detection by bare name is the weakest available signal.** The caller already knows the answer (item 1), and the answer can change over a project's life (item 2). Neither is a case for a one-shot `PATH` probe.

---

## Compatibility notes

- **Items 2–5 are self-contained** upstream changes needing nothing from pyve.
- **Item 1 is additive**: a new optional flag / env var. Consumers that do not pass it keep today's behavior exactly.
- **Config-shape change (item 5) is backward compatible** as long as the reader keeps accepting the legacy raw-string form — existing `.project-guide.yml` files in the wild carry `"pyve version X.Y.Z"`.
- **A re-render that newly *adds* the Pyve section (item 2) is a content change to a managed file.** project-guide's existing content-aware update machinery (hash comparison, `.bak.<timestamp>` siblings) already covers this; worth confirming `go.md` is treated as regenerated rather than user-owned.
- **pyve's coordinating change** for item 1 is one flag on the `project-guide init` invocation in `run_project_guide_init_in_env` (`lib/project_guide.sh`), gated on a min-version check. Not part of this request; it lands pyve-side once the supporting release exists.
