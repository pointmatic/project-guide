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

from click.shell_completion import get_completion_class

from project_guide.exceptions import CompletionError

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


def build_script(shell: str, bin_path: str) -> str:
    """Return the completion script to install or print for ``shell``.

    Post-processing is applied only when ``bin_path`` is absolute. The baked
    guard is a *filesystem* test, so a bare name (the last-resort ``PATH``
    fallback from :func:`resolve_bin`) would become ``[[ -x project-guide ]]``
    — a test against ``$PWD``. In that case Click's script is emitted verbatim,
    keeping the historical ``PATH``-dependent behavior rather than a broken one.
    """
    script = generate_script(shell)
    if not os.path.isabs(bin_path):
        return script
    return postprocess_script(script, shell=shell, bin_path=bin_path)


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
