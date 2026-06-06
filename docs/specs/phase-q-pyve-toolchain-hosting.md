# Change request: Host project-guide as a Pyve-managed global tool (toolchain-venv hosting)

**Target repo:** [`project-guide`](https://github.com/pointmatic/project-guide)
**Consumption:** Today `pyve` installs project-guide **per-project** via `pip install --upgrade project-guide` into the project's Python environment (`install_project_guide` in `lib/utils.sh`) and reaches it through that env's `.envrc` `PATH_add`. This request moves to a model where `pyve` hosts a **single** project-guide install in its own **toolchain venv** and exposes the `project-guide` console script globally via a `~/.local/bin` shim — so no project-guide machinery is installed inside individual projects.

---

## Problem statement

- project-guide began as a Python development tool and shipped as a PyPI package installed into each project's venv. Both pyve and project-guide have since become **any-stack** tools (pyve is a Bash CLI distributed via Homebrew; project-guide is a Python package — an asymmetry that no longer reflects how either is used).
- On a non-Python stack (Node-only, Node-rooted polyglot) there is **no project Python env** to host project-guide. To keep the per-project model, pyve would have to provision a dedicated per-project "utility root" venv **and** add bespoke `.envrc` PATH plumbing for a non-plugin env — just to run a version-agnostic utility. That is complexity out of proportion to the need (the pyve composed `.envrc` only `PATH_add`s *plugin* bin dirs, so a non-plugin utility env is not even reachable from the project shell without new machinery).
- project-guide is **not version-precious**: it needs *a* Python ≥ 3.x to run simple scaffolding logic, not a project-pinned interpreter. Installing its full dependency tree into every project is wasteful and couples a global-feeling tool to per-project lifecycle.
- Pyve already owns a reliable, developer-environment-independent interpreter — its **toolchain venv** (`${XDG_DATA_HOME:-$HOME/.local/share}/pyve/toolchain/<DEFAULT_PYTHON_VERSION>/venv`, provisioned by `pyve self install`). A single venv hosts arbitrarily many console scripts, and pyve's own helpers import only stdlib (`tomllib`), so co-hosting project-guide introduces **no dependency conflict**.

---

## Proposed change

Adopt a **pyve-hosted, globally-shimmed** model. The mechanics split across the two repos.

**Pyve side (informational — tracked in pyve Story N.aw; no project-guide work):**

- `pyve self install` installs/upgrades project-guide into the toolchain venv and creates/refreshes a `~/.local/bin/project-guide` symlink → `<toolchain-venv>/bin/project-guide`.
- `pyve self uninstall` removes the shim (the toolchain-tree removal already drops the package).
- A `DEFAULT_PYTHON_VERSION` bump (which re-keys the toolchain venv path) reinstalls project-guide into the new venv and re-points the shim.
- Pyve stops provisioning a per-project venv for project-guide. Per-project artifacts still scaffold into the project (see contract item 1).

**Project-guide side (this request):**

1. **Install-location independence (make it a guaranteed, tested contract).** `project-guide init` / `update` / `mode` must operate purely on the **current working directory** — scaffolding `docs/project-guide/`, writing `.project-guide.yml`, and reading/writing mode state relative to cwd, never relative to the package install location. This is almost certainly already how it behaves; the request is to make it an explicit, tested contract, because pyve now invokes it from a *global* install whose location is unrelated to the project.
2. **Pyve-managed-hosting awareness.** project-guide already detects whether pyve is installed. When it is, project-guide should treat its own installation as **pyve-managed**: do not advise the user to `pip install` it per project, and do not warn or degrade when it finds itself outside a project-local venv. Onboarding/help text should reflect "pyve manages project-guide for you."
3. **Version-introspection contract.** Provide a stable `project-guide --version` (and/or a programmatic equivalent) that pyve can pin a minimum against — mirroring the existing `--no-input ≥ 2.2.3` precedent already cited in pyve's `lib/utils.sh`.
4. **`.project-guide.yml` marker stability.** The per-project `.project-guide.yml` remains pyve's load-bearing install marker and Python-active signal (see pyve project-essentials, "`.project-guide.yml` is the canonical project-guide install marker"). Its filename, root-level location, and the `installed_version` / `target_dir` fields are a cross-repo contract; any rename or reshape is a coordinated breaking change.

---

## Motivation

- Removes per-project project-guide machinery — the developer's explicit goal: *"It would be convenient to not have to install all the Project-Guide machinery inside every project."*
- Eliminates the need for pyve to provision a per-project utility-root venv + non-plugin `.envrc` PATH plumbing on non-Python stacks (retires pyve's drafted F2 per-project provisioning and the highest-risk F3 "utility-root-only check/status mode").
- One global install means one upgrade path (`pyve self install`) instead of N per-project `pip install`s, and `project-guide` resolves in **every** shell regardless of stack or whether direnv has activated.

---

## Suggested CLI / API shape

```text
# Pyve drives installation; the developer keeps invoking the bare command,
# now globally resolvable via the ~/.local/bin shim:
project-guide --version            # stable, pin-able by pyve
project-guide init   --no-input    # operates on cwd, regardless of install location
project-guide update --no-input
project-guide mode <mode>
```

- No new project-guide subcommand is strictly required. The change is mostly **contractual guarantees** (cwd-relative operation, pyve-managed-hosting awareness) plus a pinnable version surface.

---

## Compatibility notes

- **Backward compatible for standalone users:** project-guide installed via plain `pip install project-guide` (no pyve) keeps working exactly as today — the cwd-relative behavior is already how it operates.
- The pyve-managed-hosting awareness is **additive** and gated on detecting pyve (already detected), so non-pyve usage is unchanged.
- Pyve adoption carries a **minimum project-guide version**, pinned after this release.

---

## Pyve-side follow-up

After upstream release **`vX.Y.Z`** implementing the contract (pin `project-guide ≥ vX.Y.Z`):

- **Story N.aw:** `pyve self install` installs project-guide into the toolchain venv + creates/refreshes the `~/.local/bin` shim; `pyve self uninstall` removes the shim; `DEFAULT_PYTHON_VERSION`-bump reconcile; remove per-project provisioning.
- Repoint or retire the per-project `install_project_guide` venv-targeting path so it no longer pip-installs into the project env.
- **Reconcile the N.aj gate:** under global hosting, `.project-guide.yml` presence no longer implies a *project-local* Python env, so it should no longer force the Python plugin active on a non-Python stack — this is precisely what makes the F3/N.ax utility-root-only mode unnecessary.
- Update pyve project-essentials (the `.project-guide.yml` entry) to describe global hosting rather than "installed via pip into a venv-backed `root` `utility` env."
