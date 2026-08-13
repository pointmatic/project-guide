# Copyright (c) 2026 Pointmatic
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Shell-completion script generation, independent of ``PATH``.

Click generates a completion script whose callback resolves the **bare command
name** through ``PATH`` *at completion time* — long after the rc block that
installed it ran. When project-guide is hosted in pyve's toolchain venv behind
a shim that is not on ``PATH``, that callback silently yields nothing. Baking an
absolute path into the rc block does not help; the lookup happens inside the
generated function.

So project-guide post-processes Click's output rather than emitting it verbatim:

* **zsh** — the ``(( ! $+commands[...] ))`` ``PATH`` guard becomes ``[[ -x <bin> ]]``,
  and the callback invokes ``<bin>`` instead of the bare name.
* **bash** — the callback's ``$1`` becomes ``<bin>``, and an ``[[ -x <bin> ]]``
  guard is *inserted* above it. bash ships no guard of its own, so without one a
  stale ``--bin`` makes ``env`` print "No such file or directory" on every TAB.

Both rewrites are line-local and deliberately narrow: ``#compdef project-guide``,
``compdef … project-guide``, and ``complete -F … project-guide`` all register
against the name the user *types* and must survive untouched.

The same post-processed script serves every install route — Click's own
``loadautofunc`` branch picks the right registration path — so zsh's fpath
autoload file and bash's rc block are fed by one generator.

Rather than pin a Click version, each substitution asserts it matched **exactly
once**. Click's templates have been byte-stable across 8.1.8 → 8.4.x, and a
future template change should fail loudly at generation time rather than emit a
quietly-unmodified script. See ``docs/specs/phase-r-subphase-1-shell-completion-plan.md``
§ "Spike result (Story R.b)" for the evidence behind all of the above.
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from click.shell_completion import get_completion_class

from project_guide.exceptions import CompletionError
from project_guide.version import __version__

#: The command name users type, and the name Click registers completion against.
COMMAND_NAME = "project-guide"

#: Shells this command group supports. fish uses a third install mechanism
#: (a file in ``~/.config/fish/completions/``, no rc block) and is deferred.
SUPPORTED_SHELLS = ("bash", "zsh")

# zsh's PATH guard: `(( ! $+commands[project-guide] )) && return 1`.
# Horizontal whitespace only — `\s` would span newlines and swallow the
# blank line that follows.
_ZSH_GUARD_RE = re.compile(
    r"^([ \t]*)\(\([ \t]*![ \t]*\$\+commands\[[^\]]+\][ \t]*\)\)[ \t]*&&[ \t]*return[ \t]+1[ \t]*$",
    re.MULTILINE,
)

# The completion callback's command word, per shell. `[^\s)]+` stops at the
# closing paren of the surrounding command substitution.
_CALLBACK_RE = {
    "zsh": re.compile(r"(_[A-Z0-9_]+_COMPLETE=zsh_complete[ \t]+)[^\s)]+"),
    "bash": re.compile(r"(_[A-Z0-9_]+_COMPLETE=bash_complete[ \t]+)[^\s)]+"),
}

# The whole callback line in the bash script, so a guard can be inserted above it.
_BASH_CALLBACK_LINE_RE = re.compile(
    r"^([ \t]*)response=\$\(env .*_COMPLETE=bash_complete.*$", re.MULTILINE
)

# The bash script's self-registration line: `complete -o nosort -F <func> <name>`.
_BASH_REGISTER_RE = re.compile(
    r"^([ \t]*)complete[ \t]+-o[ \t]+nosort[ \t]+(-F[ \t]+\S+[ \t]+\S+)[ \t]*$", re.MULTILINE
)


def _require_supported(shell: str) -> None:
    """Reject a shell outside :data:`SUPPORTED_SHELLS`.

    Click can generate for fish too, but project-guide cannot yet *install*
    what it would generate (fish uses a completions directory, not an rc
    block), so the supported set is project-guide's, not Click's.
    """
    if shell not in SUPPORTED_SHELLS:
        raise CompletionError(
            f"Unsupported shell '{shell}'. Supported shells: {', '.join(SUPPORTED_SHELLS)}."
        )


def generate_script(shell: str, *, prog_name: str = COMMAND_NAME) -> str:
    """Return Click's completion script for ``shell``, unmodified.

    This is the ``_PROJECT_GUIDE_COMPLETE=<shell>_source`` protocol invoked
    in-process rather than through a subprocess — same template, same output.
    """
    _require_supported(shell)
    completion_class = get_completion_class(shell)
    if completion_class is None:  # pragma: no cover - guarded by _require_supported
        raise CompletionError(f"Click provides no completion generator for '{shell}'.")
    from project_guide.cli import main

    complete_var = f"_{prog_name.replace('-', '_').upper()}_COMPLETE"
    return completion_class(main, {}, prog_name, complete_var).source()


def postprocess_script(script: str, *, shell: str, bin_path: str) -> str:
    """Rewrite ``script`` so its callback invokes ``bin_path`` instead of ``PATH``.

    ``bin_path`` is shell-quoted, so paths containing spaces survive as a single
    word. Every substitution must match exactly once; a miss raises
    :class:`CompletionError` naming the pattern that failed, which turns a
    future Click template change into a loud failure instead of a script that
    silently keeps its ``PATH`` dependency.
    """
    _require_supported(shell)
    quoted = shlex.quote(bin_path)

    # The callback is the pattern both shells share and the one the whole
    # exercise exists for, so it is checked first: an unrecognizable script
    # fails naming the callback, not a shell-specific detail.
    script, callback_count = _CALLBACK_RE[shell].subn(lambda m: m.group(1) + quoted, script)
    _require_one(callback_count, f"{shell} completion callback", shell)

    if shell == "zsh":
        script, guard_count = _ZSH_GUARD_RE.subn(
            lambda m: f"{m.group(1)}[[ -x {quoted} ]] || return 1", script
        )
        _require_one(guard_count, "zsh PATH guard", shell)
    else:
        # bash has no guard to replace, so add one above the callback: without
        # it a stale --bin prints `env: ...: No such file or directory` on
        # every TAB, and silent degradation is mandatory for completion.
        script, guard_count = _BASH_CALLBACK_LINE_RE.subn(
            lambda m: f"{m.group(1)}[[ -x {quoted} ]] || return 1\n{m.group(0)}", script
        )
        _require_one(guard_count, "bash callback line (executable guard)", shell)

    return script


def _require_one(count: int, what: str, shell: str) -> None:
    """Fail loudly when a post-processing pattern did not match exactly once."""
    if count != 1:
        raise CompletionError(
            f"Could not post-process the {shell} completion script: expected exactly "
            f"one match for the {what}, found {count}. This usually means the "
            f"installed Click version changed its completion template. "
            f"Please report it at https://github.com/pointmatic/project-guide/issues."
        )


def apply_bash_compat(script: str) -> str:
    """Make Click's self-registration line survive bash 3.2 (Story R.d).

    Click ends its bash script with ``complete -o nosort -F … project-guide``.
    ``-o nosort`` is bash >= 4.4; on stock macOS bash 3.2 the whole line fails
    with ``complete: nosort: invalid option name`` and **nothing registers at
    all** — not "completion works but unsorted", but no completion whatsoever.

    Stripping ``-o nosort`` outright would fix 3.2 at the cost of Click's
    deliberate ordering on every modern shell. Instead the line is rewritten to
    attempt the modern form and fall back:

    .. code-block:: bash

        complete -o nosort -F _f project-guide 2>/dev/null || complete -F _f project-guide

    bash 5.x takes the first form; 3.2's error is swallowed by ``2>/dev/null``
    (silent degradation is mandatory) and the fallback registers. Verified on
    bash 3.2.57 and 5.3.15.

    This is independent of ``--bin``, so unlike :func:`postprocess_script` it
    applies even on the bare-name ``PATH`` fallback.
    """
    script, count = _BASH_REGISTER_RE.subn(
        lambda m: f"{m.group(1)}complete -o nosort {m.group(2)} 2>/dev/null "
        f"|| complete {m.group(2)}",
        script,
    )
    _require_one(count, "bash completion registration line", "bash")
    return script


def build_script(shell: str, bin_path: str) -> str:
    """Return the completion script to install or print for ``shell``.

    Post-processing is applied only when ``bin_path`` is absolute. The baked
    guard is a *filesystem* test, so a bare name (the last-resort ``PATH``
    fallback from :func:`resolve_bin`) would become ``[[ -x project-guide ]]``
    — a test against ``$PWD``. In that case Click's script is emitted verbatim,
    keeping the historical ``PATH``-dependent behavior rather than a broken one.

    The bash 3.2 registration fix is applied either way — it fixes a defect
    Click's template has regardless of which binary the callback invokes.
    """
    script = generate_script(shell)
    if os.path.isabs(bin_path):
        script = postprocess_script(script, shell=shell, bin_path=bin_path)
    if shell == "bash":
        script = apply_bash_compat(script)
    return script


def resolve_shell(requested: str | None) -> str:
    """Resolve ``--shell``: an explicit value passes through, ``auto`` reads ``$SHELL``.

    An unrecognized or missing ``$SHELL`` is an error rather than a guess —
    writing the wrong shell's completion is worse than refusing to pick one.
    """
    if requested and requested != "auto":
        return requested

    shell_env = os.environ.get("SHELL", "")
    detected = os.path.basename(shell_env) if shell_env else ""
    if detected in SUPPORTED_SHELLS:
        return detected

    described = f"'{shell_env}'" if shell_env else "unset"
    raise CompletionError(
        f"Could not detect a supported shell from $SHELL ({described}). "
        f"Pass --shell explicitly: {' | '.join(SUPPORTED_SHELLS)}."
    )


def resolve_bin(explicit: str | None) -> str:
    """Resolve the binary path to bake into the completion script.

    Priority: explicit ``--bin`` → the console script this process was invoked
    as → a ``PATH`` lookup → the bare command name.

    Symlinks are deliberately **not** resolved. A host tool's stable handle is
    the shim (pyve passes ``~/.local/bin/project-guide``), not the version-keyed
    toolchain path behind it, which rots on every pyve Python bump.
    """
    if explicit:
        return os.path.abspath(os.path.expanduser(explicit))

    # argv[0] is the console script only when project-guide was invoked as
    # itself; under `python -m project_guide` it is a .py file, which would
    # bake in a callback that cannot execute.
    argv0 = sys.argv[0] if sys.argv else ""
    if argv0 and os.path.basename(argv0) == COMMAND_NAME:
        return os.path.abspath(os.path.expanduser(argv0))

    on_path = shutil.which(COMMAND_NAME)
    if on_path:
        return on_path

    return COMMAND_NAME


# ---------------------------------------------------------------------------
# rc-file blocks
#
# This is the first project-guide code that writes outside the project
# directory, so the safety contract is deliberately narrow: an exact sentinel
# pair marks what we own, we touch nothing else, every content-changing write
# is preceded by a timestamped backup, and `install` -> `uninstall` restores
# the file byte-for-byte.
# ---------------------------------------------------------------------------

#: Exact delimiters of the block project-guide owns. The conda-style pair is
#: the shape pyve's legacy block already uses, so it reads as familiar in an
#: rc file. Only a block bracketed by *both* of these is ever rewritten.
SENTINEL_START = "# >>> project-guide completion >>>"
SENTINEL_END = "# <<< project-guide completion <<<"

#: A comment that mentions project-guide completion but is not our own
#: sentinel — pyve's legacy header, or a user's hand-rolled wiring. Detected so
#: it can be *reported*, never edited. Adopting pyve's block is Story R.g.
_FOREIGN_SENTINEL_RE = re.compile(r"^\s*#.*project-guide completion", re.IGNORECASE)


class RcOutcome(Enum):
    """What an rc-file write actually did, for honest reporting."""

    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    REMOVED = "removed"
    ABSENT = "absent"


@dataclass(frozen=True)
class RcResult:
    """Result of an rc-file operation.

    ``warnings`` carries foreign-block notices for the caller to route to
    stderr; they are diagnostics, not failures, so they never change the
    outcome or the exit code.
    """

    outcome: RcOutcome
    path: Path
    backup: Path | None = None
    warnings: tuple[str, ...] = ()


def default_rc_path(shell: str) -> Path:
    """Return the rc file ``shell`` reads by default."""
    _require_supported(shell)
    return Path.home() / (".bashrc" if shell == "bash" else ".zshrc")


#: Name of the zsh autoload file. zsh looks up `_<command>` in ``fpath``, and
#: the generated script's ``#compdef project-guide`` header is written for it.
AUTOLOAD_FILENAME = f"_{COMMAND_NAME}"


def default_autoload_dir() -> Path:
    """Return the zsh autoload directory project-guide owns.

    Deliberately a project-guide-owned directory rather than a shared location
    like ``/usr/local/share/zsh/site-functions``: we create it, we are the only
    writer, and ``uninstall`` can remove it again without wondering whose files
    it is deleting. ``--dir`` points elsewhere for anyone who keeps a single
    completions directory of their own.
    """
    xdg = os.environ.get("XDG_DATA_HOME")
    root = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return root / "project-guide" / "zsh-completions"


def build_zsh_bootstrap(autoload_dir: Path) -> str:
    """Return the zsh rc-block body: make the autoload file findable, and used.

    Three requirements collide here, and the obvious two-liner satisfies only
    one of them:

    1. **The file must be readable before anything else happens.** A registered
       ``compdef`` pointing at a deleted autoload file defers its failure to TAB
       time, which is precisely the noise this subphase exists to remove. The
       whole block is therefore inert unless its own file is there.
    2. **``compdef`` may not exist yet** — the original field defect. Then the
       block runs ``compinit`` itself, which scans the freshly-extended
       ``fpath`` and registers us on the way through.
    3. **``compinit`` may already have run** — the *common* case, since this
       block lands at the end of ``~/.zshrc``, after oh-my-zsh or a hand-rolled
       ``compinit``. ``fpath`` entries added afterwards are simply not seen:
       verified directly against ``$_comps``, which stays unset. So when
       ``compdef`` exists we register explicitly instead, rather than re-running
       an expensive ``compinit`` (and overriding a configuration the user chose).

    Requirement 3 is why this is not the two-line bootstrap the subphase plan
    sketched; that shape covers only requirement 2.
    """
    quoted_dir = shlex.quote(str(autoload_dir))
    quoted_file = shlex.quote(str(autoload_dir / AUTOLOAD_FILENAME))
    return "\n".join(
        [
            f"if [[ -r {quoted_file} ]]; then",
            f"  fpath=({quoted_dir} $fpath)",
            "  if (( $+functions[compdef] )); then",
            f"    autoload -Uz {AUTOLOAD_FILENAME} && "
            f"compdef {AUTOLOAD_FILENAME} {COMMAND_NAME}",
            "  else",
            "    autoload -Uz compinit && compinit -i",
            "  fi 2>/dev/null",
            "fi",
        ]
    )


def install_autoload_file(autoload_dir: Path, script: str) -> RcResult:
    """Write the zsh autoload file, creating its directory if needed.

    No backup, unlike the rc file: this file is entirely project-guide's own
    output, so a copy of the previous version preserves nothing the next
    ``install`` cannot regenerate.
    """
    path = autoload_dir / AUTOLOAD_FILENAME
    body = script if script.endswith("\n") else script + "\n"

    if path.exists():
        if path.read_text() == body:
            return RcResult(RcOutcome.UNCHANGED, path)
        outcome = RcOutcome.UPDATED
    else:
        outcome = RcOutcome.CREATED

    autoload_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    return RcResult(outcome, path)


def remove_autoload_file(autoload_dir: Path) -> RcResult:
    """Delete the zsh autoload file, and the directory if we own it and emptied it.

    The directory is only removed when it is :func:`default_autoload_dir` — the
    one project-guide created. A ``--dir`` the user chose is theirs, and may be
    empty for reasons that are none of our business.
    """
    path = autoload_dir / AUTOLOAD_FILENAME
    if not path.exists():
        return RcResult(RcOutcome.ABSENT, path)

    path.unlink()
    if autoload_dir == default_autoload_dir() and not any(autoload_dir.iterdir()):
        autoload_dir.rmdir()
    return RcResult(RcOutcome.REMOVED, path)


def build_block(body: str) -> str:
    """Wrap ``body`` in the sentinel pair, with provenance for a human reader.

    The version stamp is what makes an old block identifiable on sight; it also
    means a re-run after an upgrade refreshes the block rather than reporting a
    stale one as current.
    """
    return "\n".join(
        [
            SENTINEL_START,
            f"# Added by `project-guide completion install` (project-guide v{__version__}).",
            "# Do not edit: re-run that command to refresh, or "
            "`project-guide completion uninstall` to remove.",
            body.rstrip("\n"),
            SENTINEL_END,
        ]
    ) + "\n"


def _find_block_span(lines: list[str]) -> tuple[int, int] | None:
    """Locate our block as an inclusive ``(start, end)`` line range.

    A start sentinel with no matching end is damage rather than a block, and
    guessing where it ought to stop risks eating the user's rc file — so it is
    an error the caller must surface.
    """
    try:
        start = lines.index(SENTINEL_START)
    except ValueError:
        return None
    for index in range(start + 1, len(lines)):
        if lines[index] == SENTINEL_END:
            return start, index
    raise CompletionError(
        f"Found an unterminated `{SENTINEL_START}` block (no closing "
        f"`{SENTINEL_END}`). Repair or delete it by hand; refusing to guess "
        "where the block ends."
    )


def _foreign_warnings(lines: list[str], span: tuple[int, int] | None) -> tuple[str, ...]:
    """Report completion wiring outside our own block that we must not touch.

    Mirrors ``_ensure_gitignore_entry()``'s ours-vs-foreign predicate: anything
    we did not write is left exactly as found and merely reported. The block we
    own is excluded from the scan, since its own header mentions the command.
    """
    ours = range(span[0], span[1] + 1) if span else range(0)
    found = [
        line.strip()
        for index, line in enumerate(lines)
        if index not in ours
        and line.strip() not in (SENTINEL_START, SENTINEL_END)
        and _FOREIGN_SENTINEL_RE.match(line)
    ]
    return tuple(
        f"⚠ Leaving a completion block we did not write untouched: {line}" for line in found
    )


def _backup(path: Path) -> Path:
    """Copy ``path`` aside before a content-changing write."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak.{timestamp}")
    counter = 1
    while backup_path.exists():
        backup_path = path.with_name(f"{path.name}.bak.{timestamp}.{counter}")
        counter += 1
    shutil.copy2(path, backup_path)
    return backup_path


def install_block(rc_path: Path, block: str) -> RcResult:
    """Write ``block`` into ``rc_path``, creating or refreshing it in place.

    Idempotent: an already-current block is a no-op with no write and no
    backup. An existing block is replaced *where it sits* rather than moved to
    the tail, so a user who repositioned it keeps their layout.
    """
    existed = rc_path.exists()
    content = rc_path.read_text() if existed else ""
    lines = content.splitlines()
    span = _find_block_span(lines)
    warnings = _foreign_warnings(lines, span)
    block_lines = block.rstrip("\n").split("\n")

    if span is not None:
        start, end = span
        if lines[start : end + 1] == block_lines:
            return RcResult(RcOutcome.UNCHANGED, rc_path, warnings=warnings)
        new_lines = lines[:start] + block_lines + lines[end + 1 :]
        outcome = RcOutcome.UPDATED
    else:
        # One blank line separates the block from whatever came before, and
        # `remove_block` consumes exactly that line again on the way out.
        separator = [""] if lines else []
        new_lines = lines + separator + block_lines
        outcome = RcOutcome.CREATED

    backup = _backup(rc_path) if existed else None
    rc_path.parent.mkdir(parents=True, exist_ok=True)
    rc_path.write_text("\n".join(new_lines) + "\n")
    return RcResult(outcome, rc_path, backup=backup, warnings=warnings)


def remove_block(rc_path: Path) -> RcResult:
    """Remove our block from ``rc_path``, restoring the file byte-for-byte.

    Safe to run blind: a missing file or a file without our block is reported
    as :attr:`RcOutcome.ABSENT`, not an error. Nothing outside the sentinel
    pair is modified, so a foreign block survives untouched.
    """
    if not rc_path.exists():
        return RcResult(RcOutcome.ABSENT, rc_path)

    content = rc_path.read_text()
    lines = content.splitlines()
    span = _find_block_span(lines)
    warnings = _foreign_warnings(lines, span)
    if span is None:
        return RcResult(RcOutcome.ABSENT, rc_path, warnings=warnings)

    start, end = span
    new_lines = lines[:start] + lines[end + 1 :]

    # Reclaim the blank separator `install_block` inserted — but only when it
    # is genuinely adjacent slack (the block ended the file, or a second blank
    # line follows), never a blank line structuring the user's own content.
    if start > 0 and new_lines[start - 1] == "":
        if start == len(new_lines) or new_lines[start] == "":
            del new_lines[start - 1]

    backup = _backup(rc_path)
    rc_path.write_text("\n".join(new_lines) + "\n" if new_lines else "")
    return RcResult(RcOutcome.REMOVED, rc_path, backup=backup, warnings=warnings)
