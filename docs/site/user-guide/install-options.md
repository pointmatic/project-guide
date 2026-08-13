# Installation

project-guide can be installed via pyve (recommended), pip, pipx, or from source.

## Requirements

- Python 3.11 or higher
- pyve, pip, or pipx package manager

project-guide depends on Jinja2 for its mode-driven templating system. This is installed automatically as a dependency.

## Install via pyve (recommended)

If you use [pyve](https://pointmatic.github.io/pyve/), let pyve install and manage Project-Guide globally for you:

```bash
pyve self install
```

`pyve self install` provisions project-guide in pyve's toolchain venv and creates a `~/.local/bin/project-guide` shim, so a single install on your `PATH` serves every project — no per-project `pip install` needed. project-guide keeps all per-project state in each project's `.project-guide.yml` and `docs/project-guide/` tree, so the shared install is never written to. When pyve is detected at `init` time, project-guide's onboarding, `status`, and `heal` output adapt to pyve-managed hosting.

## Install via pip

The simplest way to install project-guide is using pip:

```bash
pip install project-guide
```

This installs project-guide and its dependencies (including Jinja2) in your current Python environment.

## Install via pipx (recommended for standalone CLI use)

If you don't use pyve, pipx is the best way to get system-wide CLI access without affecting your project's dependencies:

```bash
pipx install project-guide
```

pipx installs the tool in an isolated environment while making the CLI command globally available.

If you don't have pipx installed:

```bash
# On macOS/Linux
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# On Windows
py -m pip install --user pipx
py -m pipx ensurepath
```

## Install from Source

To install the latest development version from GitHub:

```bash
git clone https://github.com/pointmatic/project-guide.git
cd project-guide
pip install -e .
```

For development with all optional dependencies:

```bash
pip install -e ".[dev,docs]"
```

## Verify Installation

After installation, verify that project-guide is available:

```bash
project-guide --version
```

You should see the version number displayed.

## Shell Completion (Optional)

Enable Tab completion for `project-guide` commands, flags, and mode names. project-guide installs it for you — you no longer hand-copy a snippet into your rc file.

```bash
project-guide completion install
```

Restart your shell (or `source` the rc file it names). Now you can:

- `project-guide <TAB>` — complete command names (`init`, `mode`, `status`, etc.)
- `project-guide mode <TAB>` — complete mode names (`default`, `plan_concept`, `code_direct`, etc.) — reads `.metadata.yml` from your current project
- `project-guide --<TAB>` — complete flags

Mode name completion is dynamic and reads the active project's `.metadata.yml`, so it works correctly even if you have custom modes.

### Supported shells

**bash and zsh.** `--shell` defaults to `auto`, detected from `$SHELL`; pass `--shell bash` or `--shell zsh` explicitly to set up the other one as well.

**fish is not supported yet.** Click can generate a fish script, but fish uses a different install mechanism (a file in `~/.config/fish/completions/`, no rc block), so project-guide cannot manage what it would generate. Rather than emit a script it cannot install, uninstall, or report on, the command refuses fish outright.

### What gets written where

| Shell | Artifacts |
|---|---|
| bash | one sentinel-bracketed block in `~/.bashrc` containing the completion script inline |
| zsh | an autoload file `_project-guide` in `$XDG_DATA_HOME/project-guide/zsh-completions`, plus a small block in `~/.zshrc` that adds it to `fpath` and registers it |

Override the locations with `--rc <path>` and (zsh) `--dir <path>`.

The block is bracketed by `# >>> project-guide completion >>>` / `# <<< project-guide completion <<<`, and:

- **Your rc file is backed up** (`.bak.<timestamp>`) before any change.
- **Re-running is a no-op** when everything is already current.
- **`project-guide completion uninstall` restores the file byte-for-byte**, and removes the zsh autoload file too.
- **Nothing else is touched.** A completion block project-guide did not write is reported and left alone. The one exception is a block written by an older pyve, which is replaced in place rather than left to register the same completion twice.

### Checking and repairing

```bash
project-guide completion status
```

Reports each shell as `absent`, `installed`, `stale`, `partial`, or `damaged`, and exits non-zero if anything needs attention.

**`stale`** means the binary path baked into the script no longer resolves — the usual cause is a host tool (pyve) bumping its toolchain. Completion degrades *silently* in that state by design, so `project-guide heal` warns about it on stderr with the remedy. It never edits your rc file on its own; re-run `project-guide completion install` when you choose.

To see the script without installing anything:

```bash
project-guide completion show --shell zsh
```

### Known limitations

- **macOS system bash 3.2** registers completion, but **directory and file** completions fail because Click's generated script calls `compopt`, a bash ≥ 4.0 builtin. Command, subcommand, mode-name, and flag completion all work. Homebrew bash and Linux bash are unaffected.
- **Staleness detection is a dead-path check.** If a project-guide upgrade changes the completion script itself, `status` will still say `installed`; re-run `completion install` after upgrading to refresh it.
- **PowerShell and other Windows shells** are not supported — Click ships no generator for them.
- **Windows is unverified even for bash and zsh.** Completion targets POSIX shells and has only been exercised on macOS and Linux. On Windows the baked binary path follows Windows conventions (`D:\…`), which a bash-family shell such as git-bash will not read the way you expect. The commands do not refuse to run there; they are simply untested.

## Next Steps

- [Getting Started](../getting-started.md) - Get started with your first project
- [Configuration](configuration.md) - Learn about configuration options
- [Commands](commands.md) - Explore all available commands
