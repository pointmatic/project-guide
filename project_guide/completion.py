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

import contextlib
import functools
import io
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
#: it can be *reported*, never edited.
_FOREIGN_SENTINEL_RE = re.compile(r"^\s*#.*project-guide completion", re.IGNORECASE)

#: pyve's own block header, written by ``add_project_guide_completion`` in
#: pyve's ``lib/utils.sh``. Its *closing* line is byte-identical to
#: :data:`SENTINEL_END`, so the two blocks are told apart by their headers
#: alone — never by the terminator.
PYVE_SENTINEL_START = "# >>> project-guide completion (added by pyve) >>>"

#: Content pyve plausibly generated. Adoption (Story R.g) is the single
#: sanctioned exception to "only project-guide's own sentinel is touched", and
#: it stays bounded by this predicate: pyve's *generated* body may be replaced,
#: but a block someone has since edited is foreign again and is left alone.
#: Deliberately permissive across pyve generations — the older
#: ``command -v project-guide && eval …`` form and the current
#: ``_pyve_pg_bin`` form both qualify — and deliberately blind to anything
#: else, so a user's own line inside the block blocks adoption.
_PYVE_BODY_TOKENS = (
    "_pyve_pg_bin",
    "_PROJECT_GUIDE_COMPLETE",
    "project-guide",
    "compdef",
    "compinit",
)
_PYVE_STRUCTURAL_LINES = frozenset({"fi", "else", "}", "{", "then"})


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
    #: True when pyve's legacy block was replaced by ours (Story R.g). Worth
    #: reporting on its own: the user did not ask for another tool's wiring to
    #: be rewritten, so they are told that it was.
    adopted_legacy: bool = False


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


def _find_pyve_block_span(lines: list[str]) -> tuple[int, int] | None:
    """Locate pyve's legacy block as an inclusive ``(start, end)`` range.

    Keyed on the *header*: pyve's terminator is the same string as ours, so a
    search anchored on the closing sentinel could not tell the two apart.
    """
    try:
        start = lines.index(PYVE_SENTINEL_START)
    except ValueError:
        return None
    for index in range(start + 1, len(lines)):
        if lines[index] == SENTINEL_END:
            return start, index
    return None  # unterminated: not recognizably pyve's, so not ours to touch


def _is_pyve_generated(lines: list[str], span: tuple[int, int]) -> bool:
    """Whether every body line in ``span`` is plausibly pyve's own output."""
    for line in lines[span[0] + 1 : span[1]]:
        stripped = line.strip()
        if not stripped or stripped in _PYVE_STRUCTURAL_LINES:
            continue
        if not any(token in stripped for token in _PYVE_BODY_TOKENS):
            return False
    return True


def _drop_separator_blank(lines: list[str], index: int) -> None:
    """Reclaim the blank line that separated a removed block, in place.

    Only when it is genuinely adjacent slack — the block ended the file, or a
    second blank line follows — never a blank line structuring the user's own
    content. ``index`` is where the removed block started.
    """
    if index > 0 and lines[index - 1] == "":
        if index == len(lines) or lines[index] == "":
            del lines[index - 1]


def _foreign_block_headers(lines: list[str], span: tuple[int, int] | None) -> tuple[str, ...]:
    """Return completion-wiring headers outside our own block.

    Mirrors ``_ensure_gitignore_entry()``'s ours-vs-foreign predicate: anything
    we did not write is left exactly as found and merely reported. The block we
    own is excluded from the scan, since its own header mentions the command.

    The bare lines are returned rather than finished sentences, because the
    same fact needs different framing when writing ("leaving it untouched")
    and when reporting ("it is present").
    """
    ours = range(span[0], span[1] + 1) if span else range(0)
    return tuple(
        line.strip()
        for index, line in enumerate(lines)
        if index not in ours
        and line.strip() not in (SENTINEL_START, SENTINEL_END)
        and _FOREIGN_SENTINEL_RE.match(line)
    )


def _foreign_warnings(lines: list[str], span: tuple[int, int] | None) -> tuple[str, ...]:
    """Phrase foreign-block headers for a command that is about to write."""
    return tuple(
        f"⚠ Leaving a completion block we did not write untouched: {header}"
        for header in _foreign_block_headers(lines, span)
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


class CompletionState(Enum):
    """What `completion status` found for one shell."""

    #: Nothing installed. Not a defect — an uninstalled convenience is not drift.
    ABSENT = "absent"
    #: Wired up, and the baked binary still resolves.
    INSTALLED = "installed"
    #: Wired up, but the baked path no longer passes the script's own `[[ -x ]]`
    #: test. Degrades silently in both shells, which is why it went unnoticed
    #: in the field and why this command exists.
    STALE = "stale"
    #: zsh only: one of the two artifacts is missing, so the wiring is inert.
    PARTIAL = "partial"
    #: A sentinel block we cannot parse — hand-edited or truncated.
    DAMAGED = "damaged"


@dataclass(frozen=True)
class ShellStatus:
    """Inspection result for one shell."""

    shell: str
    state: CompletionState
    rc_path: Path
    autoload_path: Path | None = None
    bin_path: str | None = None
    details: tuple[str, ...] = ()
    #: A self-contained sentence naming why this install is defective, for
    #: callers that render one line rather than the full ``details`` list.
    #:
    #: Added in Story R.r, when ``STALE`` stopped meaning only one thing:
    #: ``heal`` hard-coded the dead-path wording, so a content-drifted block
    #: with a perfectly live binary would have been announced as "<path> is no
    #: longer executable" — false, and pointing at the wrong file.
    reason: str | None = None

    @property
    def is_defect(self) -> bool:
        """Whether this state is something the user should act on."""
        return self.state in (
            CompletionState.STALE,
            CompletionState.PARTIAL,
            CompletionState.DAMAGED,
        )

    @property
    def reinstall_fixes_it(self) -> bool:
        """Whether re-running `completion install` is the remedy.

        Not for :attr:`CompletionState.DAMAGED`: `install` refuses to guess
        where an unterminated block ends, so it fails with the same parse
        error. Offering it there would send the user in a circle.
        """
        return self.state in (CompletionState.STALE, CompletionState.PARTIAL)


# The path baked into the script's executable guard, shell-quoted by
# `postprocess_script`. This is the single source of truth for "which binary
# will the completion callback actually invoke".
_BAKED_BIN_RE = re.compile(r"\[\[ -x (.+?) \]\]")

# The `fpath` line in the zsh bootstrap, which names the autoload directory the
# shell will really consult.
_FPATH_LINE_RE = re.compile(r"^\s*fpath=\((.+?) \$fpath\)\s*$", re.MULTILINE)


def _unquote(value: str) -> str:
    """Reverse ``shlex.quote`` for a single word."""
    parts = shlex.split(value)
    return parts[0] if parts else value


def _baked_bin(script: str) -> str | None:
    """Return the path baked into ``script``'s guard, if it has one.

    A bare-name install (the ``PATH`` fallback) bakes no guard at all, so the
    absence of a match is meaningful rather than an error.
    """
    match = _BAKED_BIN_RE.search(script)
    return _unquote(match.group(1)) if match else None


#: The provenance comment `build_block` writes, which carries the version that
#: generated the block. Diagnostic only — see `_content_drift`.
_STAMP_RE = re.compile(r"\(project-guide v([^)]+)\)")


def _block_body(block: str) -> str:
    """Strip the sentinel pair and provenance comments from an rc block.

    What remains is the part `build_script` / `build_zsh_bootstrap` produced —
    the only part worth comparing. The provenance line carries the version
    stamp, so leaving it in would make every release look like drift, which is
    exactly the false-positive mode Story R.r exists to avoid.
    """
    lines = [
        line
        for line in block.splitlines()
        if line not in (SENTINEL_START, SENTINEL_END)
        and not line.startswith("# Added by `project-guide completion install`")
        and not line.startswith("# Do not edit:")
    ]
    return "\n".join(lines).strip()


def _stamped_version(block: str) -> str | None:
    """The project-guide version recorded in the block, when it has one."""
    match = _STAMP_RE.search(block)
    return match.group(1) if match else None


def _version_tuple(version: str) -> tuple[int, ...]:
    """Best-effort numeric comparison key; unparseable parts sort as 0."""
    parts: list[int] = []
    for chunk in version.split(".")[:3]:
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


@functools.lru_cache(maxsize=8)
def _script_for_comparison(shell: str, bin_path: str) -> str:
    """``build_script`` for *inspection*: no stderr, and generated at most once.

    Click's bash generator calls ``_check_version``, which shells out to
    ``bash --norc -c 'echo $BASH_VERSION'`` and prints "Shell completion is not
    supported for Bash versions older than 4.4." That message is right at
    install time and wrong here: inspection is not an install request, and
    ``inspect_shell`` runs from the pre-invoke hook ahead of *every* command —
    so an unsuppressed warning becomes a line on every invocation for every
    macOS user whose ``PATH`` finds system bash 3.2. The subprocess is cached
    for the same reason: the hook should stay cheap.

    Only the message is suppressed. The generated script is byte-identical
    whichever bash is found, so the comparison stays environment-independent —
    which it must be, or the same install would read stale on one machine and
    current on another.
    """
    with contextlib.redirect_stderr(io.StringIO()):
        return build_script(shell, bin_path)


def _content_drift(
    shell: str,
    callback_script: str,
    block: str,
    bin_path: str,
    autoload_dir: Path | None,
) -> str | None:
    """Would reinstalling change anything? Returns a reason, or ``None``.

    Story R.r. The predicate R.f left as a TODO is a *content* comparison, not
    a version comparison: regenerate from the parameters recovered out of the
    installed artifacts and see whether the result differs. Comparing the
    stamped version to ``__version__`` instead would fire on every release,
    including the large majority that never touch the completion template.

    zsh is checked in both halves — the autoload file carries the callback, the
    rc block carries the bootstrap — because either can drift alone. A block
    predating the bootstrap's "register explicitly when `compinit` already ran"
    fix wires up nothing while its autoload file looks perfect.

    **Warn-less rule.** A block stamped *newer* than the running project-guide
    is left alone. Two installs commonly coexist (a pyve toolchain copy and a
    project-local one — the whole subject of Subphase Q-4), and when the older
    one inspects the newer one's block, "stale" is backwards: reinstalling
    would downgrade it. The stamp suppresses here without ever being what
    fires.
    """
    stamp = _stamped_version(block)
    if stamp is not None and _version_tuple(stamp) > _version_tuple(__version__):
        return None

    if callback_script.strip() != _script_for_comparison(shell, bin_path).strip():
        return "the installed script differs from the one this version generates"

    if shell == "zsh" and autoload_dir is not None:
        if _block_body(block) != build_zsh_bootstrap(autoload_dir).strip():
            return "the rc block differs from the one this version generates"

    return None


def _binary_resolves(bin_path: str) -> bool:
    """Apply the *same* predicate the installed script bakes in.

    ``[[ -x ]]`` is an executable test, not an existence test. Using
    ``Path.exists()`` here would let ``status`` disagree with the shell about a
    file whose permission bit was lost.
    """
    return os.access(bin_path, os.X_OK)


def _read_block_body(rc_path: Path) -> tuple[str | None, tuple[str, ...], bool]:
    """Return ``(block body, notes, damaged)`` for ``rc_path``.

    Reading is best-effort by design: this is a reporting surface, so an
    unparseable block is data to report rather than an exception to raise.
    """
    if not rc_path.exists():
        return None, (), False
    try:
        lines = rc_path.read_text().splitlines()
    except OSError as e:
        return None, (f"could not read {rc_path}: {e}",), True

    try:
        span = _find_block_span(lines)
    except CompletionError as e:
        return None, (str(e),), True

    notes = tuple(
        f"a completion block project-guide did not write is present: {header}"
        for header in _foreign_block_headers(lines, span)
    )
    if span is None:
        return None, notes, False
    return "\n".join(lines[span[0] : span[1] + 1]), notes, False


def inspect_shell(
    shell: str, *, rc_path: Path | None = None, autoload_dir: Path | None = None
) -> ShellStatus:
    """Report how completion is wired up for ``shell``. Reads only.

    For zsh the autoload directory is taken from the installed ``fpath`` line
    when there is one: the shell obeys what the rc file says, so reporting
    against a default the rc file does not name would describe a directory
    nothing consults.
    """
    _require_supported(shell)
    rc_path = rc_path or default_rc_path(shell)
    block, details, damaged = _read_block_body(rc_path)

    if damaged:
        return ShellStatus(shell, CompletionState.DAMAGED, rc_path, details=details)

    if shell == "bash":
        if block is None:
            return ShellStatus(shell, CompletionState.ABSENT, rc_path, details=details)
        # bash keeps everything in the one block, so the callback under test is
        # the block with its sentinels and provenance stripped away.
        return _classify(
            shell, rc_path, None, _block_body(block), details, block=block
        )

    # zsh: two artifacts, either of which can go missing on its own.
    if block is not None:
        match = _FPATH_LINE_RE.search(block)
        if match:
            autoload_dir = Path(_unquote(match.group(1)))
    autoload_dir = autoload_dir or default_autoload_dir()
    autoload_path = autoload_dir / AUTOLOAD_FILENAME
    has_file = autoload_path.exists()

    if block is None and not has_file:
        return ShellStatus(shell, CompletionState.ABSENT, rc_path, details=details)
    if block is None:
        return ShellStatus(
            shell,
            CompletionState.PARTIAL,
            rc_path,
            autoload_path=autoload_path,
            details=details + ("the rc block is missing, so nothing adds the "
                               "autoload file's directory to fpath",),
        )
    if not has_file:
        return ShellStatus(
            shell,
            CompletionState.PARTIAL,
            rc_path,
            autoload_path=autoload_path,
            details=details + ("the autoload file is missing, so the rc block "
                               "does nothing",),
        )
    return _classify(
        shell,
        rc_path,
        autoload_path,
        autoload_path.read_text(),
        details,
        block=block,
        autoload_dir=autoload_dir,
    )


def _classify(
    shell: str,
    rc_path: Path,
    autoload_path: Path | None,
    script: str,
    details: tuple[str, ...],
    *,
    block: str,
    autoload_dir: Path | None = None,
) -> ShellStatus:
    """Decide installed-vs-stale for an install whose structure is intact.

    Two staleness tests, in order of how actionable their message is. The dead
    path (R.f) comes first: when the baked binary has rotted *and* the script
    predates the current template, naming the dead path is the sentence that
    helps. The content comparison (R.r) catches the case R.f could not — a
    block whose binary is fine but whose script nobody generates any more.
    """
    bin_path = _baked_bin(script)

    if bin_path is None:
        # No recorded `--bin` means no parameter to regenerate from, so the
        # content comparison has nothing to compare against. Guessing one
        # would test against a script we cannot know was requested; warning
        # less is the correct failure direction.
        return ShellStatus(
            shell,
            CompletionState.INSTALLED,
            rc_path,
            autoload_path=autoload_path,
            details=details + ("installed without a baked path; the callback "
                               "resolves project-guide through PATH",),
        )

    if not _binary_resolves(bin_path):
        return ShellStatus(
            shell,
            CompletionState.STALE,
            rc_path,
            autoload_path=autoload_path,
            bin_path=bin_path,
            details=details + ("that path is not executable, so completion "
                               "silently does nothing",),
            reason=(f"{bin_path} is no longer executable, so completion "
                    f"silently does nothing"),
        )

    drift = _content_drift(shell, script, block, bin_path, autoload_dir)
    if drift is not None:
        stamp = _stamped_version(block)
        provenance = (
            (f"the installed block was generated by project-guide v{stamp}",)
            if stamp is not None
            else ()
        )
        return ShellStatus(
            shell,
            CompletionState.STALE,
            rc_path,
            autoload_path=autoload_path,
            bin_path=bin_path,
            details=details + (drift,) + provenance,
            reason=drift + (f" (generated by project-guide v{stamp})" if stamp else ""),
        )

    return ShellStatus(
        shell,
        CompletionState.INSTALLED,
        rc_path,
        autoload_path=autoload_path,
        bin_path=bin_path,
        details=details,
    )


def install_block(rc_path: Path, block: str) -> RcResult:
    """Write ``block`` into ``rc_path``, creating or refreshing it in place.

    Idempotent: an already-current block is a no-op with no write and no
    backup. An existing block is replaced *where it sits* rather than moved to
    the tail, so a user who repositioned it keeps their layout.

    **Legacy adoption (Story R.g).** pyve wrote its own completion block before
    project-guide owned this, and the two tools upgrade independently — so
    neither may assume the other has cleaned up. When pyve's block is present
    and still carries pyve's generated content, it is *replaced* rather than
    left in place beside ours, which would leave two blocks registering the
    same completion. The replacement happens at pyve's position: pyve inserts
    above SDKMan's must-be-last marker, and appending at the tail instead would
    move the wiring past it.
    """
    existed = rc_path.exists()
    content = rc_path.read_text() if existed else ""
    lines = content.splitlines()
    span = _find_block_span(lines)
    block_lines = block.rstrip("\n").split("\n")

    pyve_span = _find_pyve_block_span(lines)
    adoptable = pyve_span is not None and _is_pyve_generated(lines, pyve_span)
    # A block we are about to replace is not "left untouched", so it is
    # reported as an adoption instead of warned about as foreign.
    warnings = tuple(
        warning
        for warning in _foreign_warnings(lines, span)
        if not (adoptable and PYVE_SENTINEL_START in warning)
    )

    new_lines = list(lines)
    if span is not None:
        start, end = span
        unchanged = lines[start : end + 1] == block_lines
        if unchanged and not adoptable:
            return RcResult(RcOutcome.UNCHANGED, rc_path, warnings=warnings)
        new_lines[start : end + 1] = block_lines
        outcome = RcOutcome.UPDATED
    elif adoptable and pyve_span is not None:
        # Adopt in place: our block takes over pyve's exact position.
        new_lines[pyve_span[0] : pyve_span[1] + 1] = block_lines
        outcome = RcOutcome.CREATED
    else:
        # One blank line separates the block from whatever came before, and
        # `remove_block` consumes exactly that line again on the way out.
        separator = [""] if lines else []
        new_lines = lines + separator + block_lines
        outcome = RcOutcome.CREATED

    if adoptable and pyve_span is not None and span is not None:
        # Both blocks existed. Ours was refreshed above; pyve's duplicate goes.
        # Recompute the span, since replacing ours may have shifted the file.
        stale_span = _find_pyve_block_span(new_lines)
        if stale_span is not None:
            del new_lines[stale_span[0] : stale_span[1] + 1]
            _drop_separator_blank(new_lines, stale_span[0])

    backup = _backup(rc_path) if existed else None
    rc_path.parent.mkdir(parents=True, exist_ok=True)
    rc_path.write_text("\n".join(new_lines) + "\n" if new_lines else "")
    return RcResult(
        outcome,
        rc_path,
        backup=backup,
        warnings=warnings,
        adopted_legacy=adoptable,
    )


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
    _drop_separator_blank(new_lines, start)

    backup = _backup(rc_path)
    rc_path.write_text("\n".join(new_lines) + "\n" if new_lines else "")
    return RcResult(RcOutcome.REMOVED, rc_path, backup=backup, warnings=warnings)
