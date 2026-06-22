#### Workflow rules — pyve environment conventions

This project uses `pyve` with **two separate environments**. Picking the wrong invocation form often "works" but leads to subtle drift. Use the canonical forms below:

- **Runtime code (the package itself):** `pyve run python ...` or `pyve run <entry-point> ...`.
- **Tests:** `pyve test [pytest args]` — **not** `pyve run pytest`. Pytest is not installed in the main `.venv/`; it lives in the dev test env at `.pyve/envs/testenv/venv/`, which Pyve **auto-creates (installing `pytest`) on the first `pyve test`** when the backend is venv.
- **Dev tools (ruff, mypy, pytest):** `pyve env run ruff check ...`, `pyve env run mypy ...`.
- **Provision a test env (when you need to pre-install dev tools or add another env):** the default `testenv` auto-creates on the first `pyve test`; to set one up explicitly, `pyve env init [<name>]` creates `.pyve/envs/<name>/venv/` (default name `testenv`), and `pyve env purge` removes one. See the [pyve `env` subcommand reference](https://pointmatic.github.io/pyve/usage/#env-subcommand).
- **Install dev tools:** `pyve env install -r requirements-dev.txt`. **Do not** run `pip install -e ".[dev]"` into the main venv — that pollutes the runtime environment with test-only dependencies and breaks the two-env isolation.

Pyve 3.0.x uses the env layout `.pyve/envs/<name>/<backend>/` — the default test env is `.pyve/envs/testenv/venv/`, and additional named envs live alongside it. The default `testenv` auto-creates on the first `pyve test`. Pre-3.0 projects migrate transparently the first time `pyve update` / `pyve test` / `pyve env …` runs against a 3.x binary.

If `pytest` fails with "not found" that is the signal to use `pyve test`, not to `pip install pytest` into the wrong venv. If `pyve env install` or `pyve env run` fails complaining the env doesn't exist, run `pyve test` (which auto-creates the default `testenv`) or `pyve env init` first.

#### Named test environments (`[tool.pyve.testenvs]`)

Pyve v2.8.0 introduced declarative test-env configuration in `pyproject.toml` under `[tool.pyve.testenvs]`. Each named entry can pick its `backend` (`venv` / `micromamba` / `inherit`), declare its dependency source (`requirements` / `extra` / `manifest`), and opt into lazy lifecycle (`lazy = true`). The default single-`testenv` workflow above remains identical — declaring the table is opt-in awareness for projects that need multiple test envs (e.g., a `lint` env separate from `test`, or a conda-backed env for native deps).

Project-guide does not duplicate Pyve's schema; one paragraph + a pointer. For the full schema and worked examples, see Pyve's [`testing.md` § "Named test environments"](https://pointmatic.github.io/pyve/testing/#named-test-environments).

#### `pyve update` vs. `pyve init --force`

`pyve update` is the **non-destructive** refresh path (Pyve v2.0+): preserves the env contents, refreshes Pyve-managed files (and any project-guide scaffolding pyve oversees), and is the right command for picking up a Pyve upgrade. `pyve init --force` is the **destructive** rebuild: purges and recreates the main venv. Reach for `pyve init --force` only when env contents are known-corrupt; default to `pyve update`. For diagnostics, use `pyve check` (CI-safe 0/1/2 exit codes) — Pyve v2.0 hard-removed the legacy `pyve doctor` / `pyve validate` aliases in favor of it.

#### LLM-internal vs. developer-facing invocation

`pyve run` is for the LLM's own Bash-tool invocations; developer-facing command suggestions use the bare form verbatim from the mode template.

- ✅ Developer-facing: `project-guide mode plan_phase`
- ❌ Developer-facing: `pyve run project-guide mode plan_phase`
- ✅ LLM Bash-tool: `pyve run project-guide mode plan_phase`

**Why:** the LLM's Bash-tool shell does not auto-activate `.venv/`, so the LLM must wrap its own commands with `pyve run`. The developer's shell is typically already pyve/direnv-activated, so the bare form resolves correctly and matches the commands quoted throughout mode templates and documentation.

**How to apply:** never prepend environment wrappers (`pyve run`, `poetry run`, `uv run`, etc.) to commands you quote back to the developer from a mode template. Use the wrapper only when you execute the command yourself through the Bash tool.

#### Python invocation rule

Always use `python`, never `python3`. The `python3` command bypasses `asdf` version shims and may resolve to the system interpreter rather than the project-pinned version, leading to subtle version mismatches.

#### `requirements-dev.txt` story-writing rule

Any story that introduces dev tooling (ruff, mypy, pytest, types-* stubs) **must** include a task to create or update `requirements-dev.txt` so that `pyve env init && pyve env install -r requirements-dev.txt` reproduces the full dev environment in two commands. This keeps the dev environment reproducible and prevents "it works on my machine" drift.

#### Editable install and testenv dependency management

LLMs often get confused about *where* to install an editable package when using pyve's two-environment model. The wrong choice "works" but creates subtle drift.

**Main environment only (preferred for library projects):**
```bash
pyve run pip install -e .
```
Then configure pytest to find the source tree without a second editable install:
```toml
# pyproject.toml
[tool.pytest.ini_options]
pythonpath = ["."]   # or ["src"] for src layout
```
`pythonpath` handles import discovery cleanly and avoids maintaining two editable installs with potentially diverging dependency resolution.

**Testenv editable install (required for CLI projects):**
```bash
pyve env init                                    # one-time, creates .pyve/envs/testenv/venv/
pyve env run pip install -e .
pyve env install -r requirements-dev.txt
```
Use this when tests invoke CLI entry points (console scripts), because `pythonpath` only handles imports — it does not register entry points.

**Rule of thumb:** use `pythonpath` for library/package projects; use editable install in testenv for projects whose tests exercise CLI entry points.

**Important:** When `pyve` purges and reinitialises the main environment, the testenv remains intact and the testenv editable install survives. Re-running `pyve run pip install -e .` restores the main-environment editable install. See `developer/python-editable-install.md` for the full decision guide.
