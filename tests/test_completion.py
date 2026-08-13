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

"""Tests for the `completion` command group and its script post-processor.

The post-processing contract these tests pin was established by the Story R.b
integration spike; see `docs/specs/phase-r-subphase-1-shell-completion-plan.md`
§ "Spike result (Story R.b)".
"""

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from project_guide import completion
from project_guide.cli import main
from project_guide.exceptions import CompletionError
from project_guide.version import __version__


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


#: A test binary path built the way the platform builds absolute paths.
#:
#: `resolve_bin` runs its argument through `os.path.abspath`, and `build_script`
#: gates post-processing on `os.path.isabs` — both platform-dependent in ways a
#: hard-coded POSIX literal hides:
#:
#: * On Windows `os.path.abspath(BIN)` yields
#:   `D:\opt\pg\project-guide`, so an assertion spelling out the POSIX form
#:   never matches what was actually baked in.
#: * `ntpath.isabs("/opt/…")` was True through Python 3.12 but is False from
#:   3.13, so the same literal silently changes whether post-processing runs.
#:
#: Building the path with `os.sep` + `abspath` gives one honest answer per
#: platform, and `BIN_QUOTED` is what the product actually writes into a script
#: (`shlex.quote` escapes the Windows backslashes; on POSIX it is a no-op).
#:
#: **Any** test binary path must be built this way, not just this one. A literal
#: like `"/old/project-guide"` is not absolute on Windows under Python 3.13, so
#: `build_script` silently skips post-processing and two different paths yield
#: byte-identical scripts — which is how a refresh started reporting UNCHANGED.


def abs_bin(*parts: str) -> str:
    """Return an absolute binary path in the running platform's convention."""
    return os.path.abspath(os.path.join(os.sep, *parts))


BIN = abs_bin("opt", "pg", "project-guide")
BIN_QUOTED = shlex.quote(BIN)

#: True where there is no executable bit and no POSIX shell to speak of.
WINDOWS = os.name == "nt"


# ---------------------------------------------------------------------------
# Script generation
# ---------------------------------------------------------------------------


def test_abs_bin_is_absolute_on_this_platform():
    """The invariant every test binary path depends on.

    `build_script` post-processes only when `os.path.isabs` says so. A POSIX
    literal fails that check on Windows under Python 3.13, which makes two
    *different* `--bin` values produce byte-identical scripts — a silent
    failure that reads as "unchanged" rather than as a broken assertion.
    Pinning the helper keeps the trap from being reintroduced.
    """
    assert os.path.isabs(BIN)
    assert os.path.isabs(abs_bin("old", "project-guide"))


def test_generate_script_zsh_uses_click_source_protocol():
    """The zsh script is Click's own `zsh_source` output, unmodified."""
    script = completion.generate_script("zsh")

    assert script.startswith("#compdef project-guide")
    assert "_PROJECT_GUIDE_COMPLETE=zsh_complete project-guide" in script
    assert "(( ! $+commands[project-guide] )) && return 1" in script


def test_generate_script_bash_uses_click_source_protocol():
    """The bash script is Click's own `bash_source` output, unmodified."""
    script = completion.generate_script("bash")

    assert "_PROJECT_GUIDE_COMPLETE=bash_complete $1" in script
    assert "complete -o nosort -F _project_guide_completion project-guide" in script


def test_generate_script_rejects_an_unsupported_shell():
    """The supported set is project-guide's, not Click's.

    Click can generate a fish script, but project-guide cannot yet install one
    (fish uses a completions directory, not an rc block), so generating it
    would be a promise the command group cannot keep.
    """
    with pytest.raises(CompletionError, match="fish"):
        completion.generate_script("fish")


def test_postprocess_rejects_an_unsupported_shell():
    """The same gate applies on the post-processing entry point."""
    with pytest.raises(CompletionError, match="fish"):
        completion.postprocess_script("", shell="fish", bin_path=BIN)


# ---------------------------------------------------------------------------
# Post-processing — zsh
# ---------------------------------------------------------------------------


def test_postprocess_zsh_replaces_path_guard_with_executable_test():
    """The `$+commands` PATH guard becomes a filesystem test on the baked path."""
    script = completion.generate_script("zsh")

    result = completion.postprocess_script(script, shell="zsh", bin_path=BIN)

    assert "$+commands" not in result
    assert f"    [[ -x {BIN_QUOTED} ]] || return 1" in result


def test_postprocess_zsh_substitutes_bin_path_in_callback():
    """The completion callback invokes the absolute path, not the bare name."""
    script = completion.generate_script("zsh")

    result = completion.postprocess_script(script, shell="zsh", bin_path=BIN)

    assert f"_PROJECT_GUIDE_COMPLETE=zsh_complete {BIN_QUOTED})" in result
    assert "_PROJECT_GUIDE_COMPLETE=zsh_complete project-guide" not in result


def test_postprocess_zsh_preserves_the_typed_command_name():
    """`#compdef` and `compdef` register against the name the user types.

    A blanket substitution of the command name would break both — the spike's
    central caution about naive rewriting.
    """
    script = completion.generate_script("zsh")

    result = completion.postprocess_script(script, shell="zsh", bin_path=BIN)

    assert result.startswith("#compdef project-guide")
    assert "compdef _project_guide_completion project-guide" in result


def test_postprocess_zsh_preserves_surrounding_blank_lines():
    """Rewrites are line-local; the script's shape is otherwise untouched."""
    script = completion.generate_script("zsh")

    result = completion.postprocess_script(script, shell="zsh", bin_path=BIN)

    assert len(result.splitlines()) == len(script.splitlines())


# ---------------------------------------------------------------------------
# Post-processing — bash
# ---------------------------------------------------------------------------


def test_postprocess_bash_substitutes_bin_path_for_positional_arg():
    """`$1` (the PATH-resolved command word) becomes the baked path."""
    script = completion.generate_script("bash")

    result = completion.postprocess_script(script, shell="bash", bin_path=BIN)

    assert f"_PROJECT_GUIDE_COMPLETE=bash_complete {BIN_QUOTED})" in result
    assert "_PROJECT_GUIDE_COMPLETE=bash_complete $1" not in result


def test_postprocess_bash_inserts_executable_guard_above_the_callback():
    """R.b Amendment 2: bash ships no guard, so a stale path would print on every TAB."""
    script = completion.generate_script("bash")

    result = completion.postprocess_script(script, shell="bash", bin_path=BIN)

    lines = result.splitlines()
    callback_index = next(i for i, line in enumerate(lines) if "bash_complete" in line)
    assert lines[callback_index - 1] == f"    [[ -x {BIN_QUOTED} ]] || return 1"


def test_postprocess_bash_keeps_registration_line_intact():
    """The `complete -F … project-guide` registration still targets the typed name."""
    script = completion.generate_script("bash")

    result = completion.postprocess_script(script, shell="bash", bin_path=BIN)

    assert "complete -o nosort -F _project_guide_completion project-guide" in result


# ---------------------------------------------------------------------------
# Post-processing — shared contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("shell", ["zsh", "bash"])
def test_postprocess_quotes_a_bin_path_containing_spaces(shell):
    """A `--bin` path with spaces must survive as a single shell word."""
    script = completion.generate_script(shell)

    result = completion.postprocess_script(
        script, shell=shell, bin_path="/opt/my tools/project-guide"
    )

    assert "'/opt/my tools/project-guide'" in result


@pytest.mark.parametrize("shell", ["zsh", "bash"])
def test_postprocess_raises_when_the_callback_pattern_is_missing(shell):
    """A Click template change must fail loudly, not emit an unmodified script.

    This is the structural assertion that replaces a Click version pin (R.b
    stability finding): every substitution must match exactly once.
    """
    with pytest.raises(CompletionError, match="callback"):
        completion.postprocess_script(
            "# nothing here Click would recognize\n", shell=shell, bin_path=BIN
        )


def test_postprocess_raises_when_the_zsh_guard_pattern_is_missing():
    """The zsh PATH guard is equally load-bearing and equally asserted."""
    script = completion.generate_script("zsh")
    without_guard = script.replace("(( ! $+commands[project-guide] )) && return 1\n", "")

    with pytest.raises(CompletionError, match="guard"):
        completion.postprocess_script(
            without_guard, shell="zsh", bin_path=BIN
        )


# ---------------------------------------------------------------------------
# build_script — the absolute-path gate (R.b Amendment 3)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("shell", ["zsh", "bash"])
def test_build_script_post_processes_an_absolute_bin_path(shell):
    """An absolute `--bin` is the post-processed branch."""
    result = completion.build_script(shell, BIN)

    assert BIN in result


@pytest.mark.parametrize("shell", ["zsh", "bash"])
def test_build_script_skips_post_processing_for_a_bare_name(shell):
    """The baked guard is a filesystem test, so a bare name must not be baked in.

    R.b Amendment 3 — the bare-name `PATH` fallback keeps Click's historical
    resolution behavior rather than emitting `[[ -x project-guide ]]`, which
    would test a file relative to `$PWD`.

    Narrowed in R.d from "byte-identical to Click's output": bash additionally
    gets the 3.2 registration fallback, which is a defect in Click's template
    independent of how the callback resolves its binary.
    """
    result = completion.build_script(shell, "project-guide")

    assert "[[ -x" not in result
    assert "_PROJECT_GUIDE_COMPLETE=zsh_complete project-guide" in result or (
        "_PROJECT_GUIDE_COMPLETE=bash_complete $1" in result
    )
    if shell == "zsh":
        assert result == completion.generate_script(shell)


# ---------------------------------------------------------------------------
# Shell resolution
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("shell", ["zsh", "bash"])
def test_resolve_shell_passes_an_explicit_shell_through(shell):
    """An explicit `--shell` value never consults the environment."""
    assert completion.resolve_shell(shell) == shell


@pytest.mark.parametrize(
    ("shell_env", "expected"),
    [("/bin/zsh", "zsh"), ("/usr/local/bin/bash", "bash"), ("/opt/homebrew/bin/zsh", "zsh")],
)
def test_resolve_shell_auto_reads_the_shell_env_var(monkeypatch, shell_env, expected):
    """`auto` detects from `$SHELL`'s basename."""
    monkeypatch.setenv("SHELL", shell_env)

    assert completion.resolve_shell("auto") == expected


def test_resolve_shell_auto_errors_on_an_unsupported_shell(monkeypatch):
    """An unsupported `$SHELL` is an explicit error, never a silent guess."""
    monkeypatch.setenv("SHELL", "/usr/local/bin/fish")

    with pytest.raises(CompletionError, match="--shell"):
        completion.resolve_shell("auto")


def test_resolve_shell_auto_errors_when_shell_is_unset(monkeypatch):
    """No `$SHELL` (cron, some CI runners) is an error, never a default guess."""
    monkeypatch.delenv("SHELL", raising=False)

    with pytest.raises(CompletionError, match="--shell"):
        completion.resolve_shell("auto")


# ---------------------------------------------------------------------------
# --bin resolution
# ---------------------------------------------------------------------------


def test_resolve_bin_prefers_the_explicit_flag(monkeypatch):
    """Explicit `--bin` beats every form of self-detection."""
    monkeypatch.setattr(sys, "argv", ["/somewhere/else/project-guide"])

    assert completion.resolve_bin(BIN) == BIN


def test_resolve_bin_expands_a_tilde(monkeypatch, tmp_path):
    """pyve passes `~/.local/bin/project-guide`; the script needs it expanded.

    `USERPROFILE` is set alongside `HOME` because that is the variable
    `ntpath.expanduser` actually consults — patching only `HOME` would expand
    to the CI runner's real profile on Windows and quietly test nothing.
    """
    home = tmp_path / "dev"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))

    resolved = completion.resolve_bin("~/.local/bin/project-guide")

    assert "~" not in resolved
    assert resolved == os.path.join(str(home), ".local", "bin", "project-guide")


def test_resolve_bin_makes_a_relative_path_absolute(tmp_path, monkeypatch):
    """A relative `--bin` would break the baked filesystem guard."""
    monkeypatch.chdir(tmp_path)

    result = completion.resolve_bin("./bin/project-guide")

    assert result == str(tmp_path / "bin/project-guide")


def test_resolve_bin_does_not_resolve_symlinks(tmp_path):
    """The shim path is the stable handle; its target rots on every pyve bump.

    pyve deliberately passes `~/.local/bin/project-guide` rather than the
    version-keyed toolchain path behind it, so resolving the symlink would
    defeat the point of `--bin`.
    """
    target = tmp_path / "toolchain-3.13" / "project-guide"
    target.parent.mkdir()
    target.write_text("#!/bin/sh\n")
    shim = tmp_path / "project-guide"
    shim.symlink_to(target)

    assert completion.resolve_bin(str(shim)) == str(shim)


def test_resolve_bin_falls_back_to_its_own_console_script(monkeypatch, tmp_path):
    """With no `--bin`, project-guide bakes in the path it was invoked as."""
    own = tmp_path / "project-guide"
    own.write_text("#!/bin/sh\n")
    monkeypatch.setattr(sys, "argv", [str(own)])

    assert completion.resolve_bin(None) == str(own)


def test_resolve_bin_ignores_argv0_when_it_is_not_the_console_script(monkeypatch, tmp_path):
    """Under `python -m project_guide`, argv[0] is a .py file — not a usable bin.

    Baking `__main__.py` into the completion script would produce a callback
    that cannot execute, so this falls through to the PATH lookup.
    """
    monkeypatch.setattr(sys, "argv", [str(tmp_path / "__main__.py")])
    monkeypatch.setattr(completion.shutil, "which", lambda name: "/usr/local/bin/project-guide")

    assert completion.resolve_bin(None) == "/usr/local/bin/project-guide"


def test_resolve_bin_falls_back_to_the_bare_name(monkeypatch):
    """Last resort: the bare name, which `build_script` leaves un-post-processed."""
    monkeypatch.setattr(sys, "argv", ["/nonexistent/python"])
    monkeypatch.setattr(completion.shutil, "which", lambda name: None)

    assert completion.resolve_bin(None) == "project-guide"


# ---------------------------------------------------------------------------
# `completion show`
# ---------------------------------------------------------------------------


def test_completion_show_prints_the_zsh_script(runner):
    """`show` writes the script to stdout and exits 0."""
    result = runner.invoke(main, ["completion", "show", "--shell", "zsh", "--bin", BIN])

    assert result.exit_code == 0
    assert result.output.startswith("#compdef project-guide")
    assert f"_PROJECT_GUIDE_COMPLETE=zsh_complete {BIN_QUOTED})" in result.output


def test_completion_show_prints_the_bash_script(runner):
    """The bash route emits the guarded, path-substituted script."""
    result = runner.invoke(main, ["completion", "show", "--shell", "bash", "--bin", BIN])

    assert result.exit_code == 0
    assert f"[[ -x {BIN_QUOTED} ]] || return 1" in result.output


def test_completion_show_stdout_is_only_the_script(runner):
    """`eval "$(project-guide completion show)"` must not swallow chatter."""
    result = runner.invoke(main, ["completion", "show", "--shell", "bash", "--bin", BIN])

    assert result.output.rstrip("\n").endswith("_project_guide_completion_setup;")


def test_completion_show_auto_detects_the_shell(runner, monkeypatch):
    """No `--shell` means `auto`, which reads `$SHELL`."""
    monkeypatch.setenv("SHELL", "/bin/zsh")

    result = runner.invoke(main, ["completion", "show", "--bin", BIN])

    assert result.exit_code == 0
    assert result.output.startswith("#compdef project-guide")


def test_completion_show_errors_on_an_undetectable_shell(runner, monkeypatch):
    """An unsupported `$SHELL` fails with actionable guidance, not a guess."""
    monkeypatch.setenv("SHELL", "/usr/local/bin/fish")

    result = runner.invoke(main, ["completion", "show"])

    assert result.exit_code != 0
    assert "--shell" in result.output


def test_completion_show_rejects_an_unsupported_shell_value(runner):
    """`--shell fish` is refused by the Choice, listing what is supported."""
    result = runner.invoke(main, ["completion", "show", "--shell", "fish"])

    assert result.exit_code == 2
    assert "fish" in result.output


def test_completion_show_writes_nothing_to_the_filesystem(runner, tmp_path, monkeypatch):
    """The read-only slice: `show` never touches disk (installs land in R.d/R.e)."""
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.rglob("*"))

    result = runner.invoke(main, ["completion", "show", "--shell", "zsh"])

    assert result.exit_code == 0
    assert set(tmp_path.rglob("*")) == before


@pytest.mark.parametrize("flag", ["--quiet", "--no-input"])
def test_completion_show_has_no_output_suppressing_flags(runner, flag):
    """`show`'s stdout *is* its payload, and it never prompts.

    Accepting `--quiet` would make the command a no-op; accepting `--no-input`
    would imply a prompt that does not exist. Both are refused so the surface
    stays honest.
    """
    result = runner.invoke(main, ["completion", "show", "--shell", "zsh", flag])

    assert result.exit_code == 2
    assert "no such option" in result.output.lower()


# ---------------------------------------------------------------------------
# stdout purity — the coherence question a stdout-producing command raises
# ---------------------------------------------------------------------------


def _without_prompt_echo(stdout: str, answer: str) -> str:
    """Strip CliRunner's simulated typing from captured stdout.

    Click's test runner replaces `visible_prompt_func` with one that writes the
    prompt suffix and the supplied answer to `sys.stdout`, standing in for the
    characters a terminal would echo. Whether that lands in the captured stdout
    or the captured stderr differs across platforms and Click versions — it is
    stdout on Windows CI, stderr on macOS.

    It is a harness artifact either way: a real terminal echoes keystrokes to
    the tty, not to the program's stdout, so it can never reach a command
    substitution. The guarantee under test is about what *project-guide* writes,
    so the simulated echo is removed before asserting on it.
    """
    echo = f" {answer}\n"
    return stdout[len(echo):] if stdout.startswith(echo) else stdout


def test_completion_show_stdout_is_pure_when_the_heal_hook_prompts(runner, tmp_path, monkeypatch):
    """The auto-heal prompt must not land in `eval "$(… completion show)"`.

    The hook fires before every subcommand, so its prompt would otherwise be
    captured by a command substitution and evaluated as shell code.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        assert runner.invoke(main, ["init"]).exit_code == 0
        Path("docs/project-guide/README.md").unlink()  # drift the hook will notice
        monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
        monkeypatch.setattr("project_guide.cli.should_skip_input", lambda *a, **k: False)

        result = runner.invoke(
            main,
            ["completion", "show", "--shell", "zsh", "--bin", BIN],
            input="n\n",
        )

        assert result.exit_code == 0
        assert _without_prompt_echo(result.stdout, "n").startswith("#compdef project-guide")
        assert "Update?" not in result.stdout
        assert "Update?" in result.stderr


def test_completion_show_stdout_is_pure_when_the_heal_hook_auto_heals(runner, tmp_path, monkeypatch):
    """Same guarantee on the --no-input branch, whose notice is non-suppressible."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        assert runner.invoke(main, ["init"]).exit_code == 0
        Path("docs/project-guide/README.md").unlink()
        monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)

        result = runner.invoke(
            main, ["completion", "show", "--shell", "bash", "--bin", BIN]
        )

        assert result.exit_code == 0
        assert "Auto-healing" not in result.stdout
        assert "Auto-healing" in result.stderr


def test_completion_show_stdout_is_pure_during_legacy_config_migration(runner, tmp_path):
    """The one-time `.project-guides.yml` rename notice is diagnostic, not payload."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        assert runner.invoke(main, ["init"]).exit_code == 0
        Path(".project-guide.yml").rename(".project-guides.yml")

        result = runner.invoke(
            main, ["completion", "show", "--shell", "zsh", "--bin", BIN]
        )

        assert result.exit_code == 0
        assert result.stdout.startswith("#compdef project-guide")
        assert "Migrated" not in result.stdout
        assert "Migrated" in result.stderr


def test_completion_group_is_registered(runner):
    """The group is discoverable from the top-level help."""
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "completion" in result.output


def test_completion_help_lists_show(runner):
    """`completion --help` names the read-only subcommand."""
    result = runner.invoke(main, ["completion", "--help"])

    assert result.exit_code == 0
    assert "show" in result.output


def test_completion_help_lists_install_and_uninstall(runner):
    """The writing half of the group is discoverable too."""
    result = runner.invoke(main, ["completion", "--help"])

    assert result.exit_code == 0
    assert "install" in result.output
    assert "uninstall" in result.output


# ---------------------------------------------------------------------------
# bash 3.2 compatibility — Amendment 4
# ---------------------------------------------------------------------------


def test_bash_compat_falls_back_when_nosort_is_unsupported():
    """`complete -o nosort` is bash >= 4.4; on 3.2 the whole line fails.

    Stock macOS bash then registers *nothing* — `complete -p` reports no
    specification at all. Rather than strip `-o nosort` unconditionally
    (losing Click's ordering everywhere), the line is rewritten to try it and
    fall back, so modern bash keeps the ordering and 3.2 still registers.
    """
    script = completion.build_script("bash", BIN)

    assert (
        "complete -o nosort -F _project_guide_completion project-guide 2>/dev/null || "
        "complete -F _project_guide_completion project-guide" in script
    )


def test_bash_compat_is_applied_exactly_once():
    """The fallback must not stack if the transform is applied twice."""
    script = completion.build_script("bash", BIN)

    assert script.count("2>/dev/null ||") == 1


def test_bash_compat_applies_on_the_bare_name_fallback():
    """The `nosort` defect is independent of `--bin`, so the fix must be too.

    Post-processing is skipped for a non-absolute bin (Amendment 3), but a
    bash 3.2 user on the `PATH` fallback still needs the line to register.
    """
    script = completion.build_script("bash", "project-guide")

    assert "2>/dev/null || complete -F" in script
    assert "[[ -x" not in script  # post-processing correctly skipped


def test_bash_compat_is_not_applied_to_zsh():
    """`complete` is a bash builtin; the zsh script has no such line."""
    script = completion.build_script("zsh", BIN)

    assert "2>/dev/null" not in script


def test_bash_compat_fails_loudly_if_clicks_tail_line_changes():
    """Same exactly-once discipline as the other substitutions."""
    with pytest.raises(CompletionError, match="registration line"):
        completion.apply_bash_compat("no completion registration here\n")


# ---------------------------------------------------------------------------
# rc-block assembly
# ---------------------------------------------------------------------------


def test_build_block_is_sentinel_bracketed():
    """The block is delimited by an exact, greppable sentinel pair."""
    block = completion.build_block("echo hi")

    lines = block.splitlines()
    assert lines[0] == completion.SENTINEL_START
    assert lines[-1] == completion.SENTINEL_END
    assert "echo hi" in lines
    assert block.endswith("\n")


def test_build_block_records_the_generating_version():
    """The block says what wrote it, so a reader can date it without guessing."""
    block = completion.build_block("echo hi")

    assert __version__ in block
    assert "completion install" in block


# ---------------------------------------------------------------------------
# rc-file writing — install
# ---------------------------------------------------------------------------


def test_install_block_creates_a_missing_rc_file(tmp_path):
    """A user with no `~/.bashrc` still gets working completion."""
    rc = tmp_path / ".bashrc"

    result = completion.install_block(rc, completion.build_block("echo hi"))

    assert result.outcome is completion.RcOutcome.CREATED
    assert rc.read_text().startswith(completion.SENTINEL_START)
    assert result.backup is None


def test_install_block_appends_after_existing_content(tmp_path):
    """Prior rc content is preserved verbatim, separated by one blank line."""
    rc = tmp_path / ".bashrc"
    rc.write_text("export EDITOR=vim\nalias ll='ls -l'\n")

    result = completion.install_block(rc, completion.build_block("echo hi"))

    text = rc.read_text()
    assert result.outcome is completion.RcOutcome.CREATED
    assert text.startswith("export EDITOR=vim\nalias ll='ls -l'\n\n")
    assert completion.SENTINEL_START in text


def test_install_block_is_a_no_op_when_already_current(tmp_path):
    """Idempotent: an unchanged block means no write and no backup."""
    rc = tmp_path / ".bashrc"
    rc.write_text("export EDITOR=vim\n")
    block = completion.build_block("echo hi")
    completion.install_block(rc, block)
    after_first = rc.read_text()
    backups_after_first = set(tmp_path.glob(".bashrc.bak.*"))

    result = completion.install_block(rc, block)

    assert result.outcome is completion.RcOutcome.UNCHANGED
    assert rc.read_text() == after_first
    assert result.backup is None
    assert set(tmp_path.glob(".bashrc.bak.*")) == backups_after_first


def test_install_block_refreshes_a_stale_block_in_place(tmp_path):
    """A changed `--bin` rewrites the block where it sits, not at the tail."""
    rc = tmp_path / ".bashrc"
    rc.write_text("first\n")
    completion.install_block(rc, completion.build_block("OLD"))
    rc.write_text(rc.read_text() + "\nlast\n")

    result = completion.install_block(rc, completion.build_block("NEW"))

    text = rc.read_text()
    assert result.outcome is completion.RcOutcome.UPDATED
    assert "OLD" not in text
    assert "NEW" in text
    assert text.startswith("first\n")
    assert text.endswith("last\n")


def test_install_block_backs_up_before_modifying(tmp_path):
    """The first write outside the project directory is reversible by hand."""
    rc = tmp_path / ".bashrc"
    rc.write_text("original\n")
    completion.install_block(rc, completion.build_block("OLD"))

    result = completion.install_block(rc, completion.build_block("NEW"))

    assert result.backup is not None
    assert result.backup.exists()
    assert "OLD" in result.backup.read_text()


def test_install_block_rejects_an_unterminated_block(tmp_path):
    """A start sentinel with no end is damage, not a block — refuse to guess."""
    rc = tmp_path / ".bashrc"
    rc.write_text(f"{completion.SENTINEL_START}\nhalf a block\n")

    with pytest.raises(CompletionError, match="unterminated"):
        completion.install_block(rc, completion.build_block("echo hi"))


# ---------------------------------------------------------------------------
# rc-file writing — uninstall and round-trip
# ---------------------------------------------------------------------------


def test_install_uninstall_round_trips_the_rc_file_byte_for_byte(tmp_path):
    """The safety contract: the rc file comes back exactly as it was."""
    rc = tmp_path / ".bashrc"
    original = "export EDITOR=vim\n\n# my stuff\nalias ll='ls -l'\n"
    rc.write_text(original)

    completion.install_block(rc, completion.build_block("echo hi"))
    assert rc.read_text() != original
    completion.remove_block(rc)

    assert rc.read_text() == original


def test_remove_block_preserves_content_that_follows_it(tmp_path):
    """Removal is bounded by the sentinels; nothing downstream shifts."""
    rc = tmp_path / ".bashrc"
    rc.write_text("first\n")
    completion.install_block(rc, completion.build_block("echo hi"))
    rc.write_text(rc.read_text() + "\nlast\n")

    result = completion.remove_block(rc)

    assert result.outcome is completion.RcOutcome.REMOVED
    assert rc.read_text() == "first\n\nlast\n"


def test_remove_block_reports_absent_when_there_is_no_block(tmp_path):
    """Uninstalling what was never installed is a success, not an error."""
    rc = tmp_path / ".bashrc"
    rc.write_text("export EDITOR=vim\n")

    result = completion.remove_block(rc)

    assert result.outcome is completion.RcOutcome.ABSENT
    assert rc.read_text() == "export EDITOR=vim\n"


def test_remove_block_reports_absent_when_the_rc_file_is_missing(tmp_path):
    """A missing rc file is the same nothing-to-do case, and creates nothing."""
    rc = tmp_path / ".bashrc"

    result = completion.remove_block(rc)

    assert result.outcome is completion.RcOutcome.ABSENT
    assert not rc.exists()


def test_remove_block_backs_up_before_modifying(tmp_path):
    """Removal is a modification, so it is reversible too."""
    rc = tmp_path / ".bashrc"
    rc.write_text("original\n")
    completion.install_block(rc, completion.build_block("echo hi"))

    result = completion.remove_block(rc)

    assert result.backup is not None
    assert completion.SENTINEL_START in result.backup.read_text()


# ---------------------------------------------------------------------------
# ours-vs-foreign — never touch a block we did not write
# ---------------------------------------------------------------------------

PYVE_LEGACY_BLOCK = (
    "# >>> project-guide completion (added by pyve) >>>\n"
    'eval "$(_PROJECT_GUIDE_COMPLETE=bash_source project-guide)"\n'
    "# <<< project-guide completion <<<\n"
)

# The current block pyve writes, copied from `add_project_guide_completion`
# in pyve's `lib/utils.sh`. Both shell variants, because project-guide must
# recognize whichever one the user happens to carry.
PYVE_BLOCK_BASH = """\
# >>> project-guide completion (added by pyve) >>>
_pyve_pg_bin="$HOME/.local/bin/project-guide"
[ -x "$_pyve_pg_bin" ] || _pyve_pg_bin="$(command -v project-guide 2>/dev/null || true)"
if [ -n "$_pyve_pg_bin" ]; then
  eval "$(_PROJECT_GUIDE_COMPLETE=bash_source "$_pyve_pg_bin" 2>/dev/null)"
fi
unset _pyve_pg_bin
# <<< project-guide completion <<<
"""

# Hand-rolled wiring that is nobody's generated output — the case adoption
# must never touch, and the one the foreign-block warning is really for.
FOREIGN_BLOCK = """\
# my own project-guide completion setup
source ~/dotfiles/completions/project-guide.bash
export PROJECT_GUIDE_HACK=1
"""

PYVE_BLOCK_ZSH = """\
# >>> project-guide completion (added by pyve) >>>
_pyve_pg_bin="$HOME/.local/bin/project-guide"
[ -x "$_pyve_pg_bin" ] || _pyve_pg_bin="$(command -v project-guide 2>/dev/null || true)"
if [ -n "$_pyve_pg_bin" ]; then
  (( $+functions[compdef] )) || { autoload -Uz compinit && compinit -i; } 2>/dev/null
  if (( $+functions[compdef] )); then
    eval "$(_PROJECT_GUIDE_COMPLETE=zsh_source "$_pyve_pg_bin" 2>/dev/null)"
  fi
fi
unset _pyve_pg_bin
# <<< project-guide completion <<<
"""


def test_install_leaves_a_hand_modified_pyve_block_untouched(tmp_path):
    """A pyve block someone edited is no longer pyve's — so it is not ours.

    Adoption (R.g) is bounded to pyve's *generated* content. Once a user has
    put their own lines inside it, silently discarding them would be exactly
    the foreign-block edit the safety contract forbids.
    """
    rc = tmp_path / ".bashrc"
    hand_modified = PYVE_BLOCK_BASH.replace(
        "unset _pyve_pg_bin", "export MY_OWN_THING=1\nunset _pyve_pg_bin"
    )
    rc.write_text(hand_modified)

    result = completion.install_block(rc, completion.build_block("echo hi"))

    text = rc.read_text()
    assert hand_modified in text
    assert completion.SENTINEL_START in text
    assert any("added by pyve" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# Legacy pyve sentinel adoption (Story R.g)
#
# The one sanctioned exception to "only project-guide's own sentinel is
# touched": pyve's exact known pair, and only while its body is still pyve's.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "legacy", [PYVE_BLOCK_BASH, PYVE_BLOCK_ZSH, PYVE_LEGACY_BLOCK],
    ids=["pyve-bash", "pyve-zsh", "pyve-older-generation"],
)
def test_install_adopts_a_pyve_block(tmp_path, legacy):
    """Without this, `install` leaves two blocks registering the same completion."""
    rc = tmp_path / ".bashrc"
    rc.write_text(legacy)

    result = completion.install_block(rc, completion.build_block("echo hi"))

    text = rc.read_text()
    assert result.adopted_legacy
    assert completion.PYVE_SENTINEL_START not in text
    assert text.count(completion.SENTINEL_START) == 1
    assert result.warnings == ()  # replaced, not "left untouched"


def test_adoption_replaces_the_legacy_block_in_place(tmp_path):
    """Position is load-bearing: pyve inserts *above* the SDKMan marker.

    SDKMan requires its own block to load last, so pyve deliberately places
    the completion block before it. Removing pyve's block and appending ours
    at the tail would put our wiring after SDKMan's must-be-last region.
    """
    rc = tmp_path / ".bashrc"
    rc.write_text(
        "export EDITOR=vim\n\n"
        + PYVE_BLOCK_BASH
        + "\n#THIS MUST BE AT THE END OF THE FILE FOR SDKMAN TO WORK!!!\n"
        'source "$HOME/.sdkman/bin/sdkman-init.sh"\n'
    )

    completion.install_block(rc, completion.build_block("echo hi"))

    lines = rc.read_text().splitlines()
    assert lines.index(completion.SENTINEL_START) < lines.index(
        "#THIS MUST BE AT THE END OF THE FILE FOR SDKMAN TO WORK!!!"
    )
    assert lines[0] == "export EDITOR=vim"


def test_adoption_removes_the_legacy_block_when_ours_already_exists(tmp_path):
    """Both blocks present is the duplicate-registration state R.g closes."""
    rc = tmp_path / ".bashrc"
    rc.write_text(PYVE_BLOCK_BASH)
    completion.install_block(rc, completion.build_block("echo hi"))
    # Simulate pyve re-adding its block after project-guide installed its own.
    rc.write_text(PYVE_BLOCK_BASH + "\n" + rc.read_text())

    result = completion.install_block(rc, completion.build_block("echo hi"))

    text = rc.read_text()
    assert result.adopted_legacy
    assert completion.PYVE_SENTINEL_START not in text
    assert text.count(completion.SENTINEL_START) == 1


def test_adoption_of_a_duplicate_is_never_reported_as_unchanged(tmp_path):
    """Our block may be byte-identical, but removing pyve's still wrote."""
    rc = tmp_path / ".bashrc"
    block = completion.build_block("echo hi")
    completion.install_block(rc, block)
    rc.write_text(PYVE_BLOCK_BASH + "\n" + rc.read_text())

    result = completion.install_block(rc, block)

    assert result.outcome is not completion.RcOutcome.UNCHANGED
    assert result.adopted_legacy


def test_adoption_backs_up_the_rc_file_first(tmp_path):
    """Rewriting another tool's wiring is exactly when a backup earns its keep."""
    rc = tmp_path / ".bashrc"
    rc.write_text(PYVE_BLOCK_BASH)

    result = completion.install_block(rc, completion.build_block("echo hi"))

    assert result.backup is not None
    assert completion.PYVE_SENTINEL_START in result.backup.read_text()


def test_no_adoption_reported_when_there_was_no_legacy_block(tmp_path):
    """The flag must not misfire on an ordinary install."""
    rc = tmp_path / ".bashrc"
    rc.write_text("export EDITOR=vim\n")

    result = completion.install_block(rc, completion.build_block("echo hi"))

    assert not result.adopted_legacy


def test_adoption_preserves_surrounding_content_byte_for_byte(tmp_path):
    """Only the legacy block's own lines are replaced."""
    rc = tmp_path / ".bashrc"
    rc.write_text("first\n\n" + PYVE_BLOCK_BASH + "\nlast\n")

    completion.install_block(rc, completion.build_block("echo hi"))

    text = rc.read_text()
    assert text.startswith("first\n\n")
    assert text.endswith("\nlast\n")


def test_uninstall_after_adoption_leaves_no_completion_wiring(tmp_path):
    """Adopt then uninstall should not resurrect pyve's block."""
    rc = tmp_path / ".bashrc"
    rc.write_text("export EDITOR=vim\n\n" + PYVE_BLOCK_BASH)
    completion.install_block(rc, completion.build_block("echo hi"))

    completion.remove_block(rc)

    text = rc.read_text()
    assert completion.PYVE_SENTINEL_START not in text
    assert completion.SENTINEL_START not in text


def test_completion_install_reports_the_adoption_in_one_line(runner, tmp_path):
    """The user must be told their pyve block was replaced, not silently lose it."""
    rc = tmp_path / ".bashrc"
    rc.write_text(PYVE_BLOCK_BASH)

    result = runner.invoke(
        main,
        ["completion", "install", "--shell", "bash", "--rc", str(rc),
         "--bin", BIN],
    )

    assert result.exit_code == 0
    assert "pyve" in result.output
    assert completion.PYVE_SENTINEL_START not in rc.read_text()


def test_status_reports_nothing_foreign_after_adoption(runner, tmp_path):
    """The duplicate-block note `status` used to print is gone once adopted."""
    rc = tmp_path / ".bashrc"
    rc.write_text(PYVE_BLOCK_BASH)
    completion.install_block(rc, completion.build_block(
        completion.build_script("bash", BIN)
    ))

    status = completion.inspect_shell("bash", rc_path=rc)

    assert not any("did not write" in detail for detail in status.details)


def test_uninstall_leaves_a_foreign_block_untouched(tmp_path):
    """Symmetrically, uninstall removes only what project-guide itself wrote.

    Uses hand-rolled wiring rather than pyve's block, which `install` now
    adopts (R.g) — adoption is bounded to pyve's exact generated content.
    """
    rc = tmp_path / ".bashrc"
    rc.write_text(FOREIGN_BLOCK)
    completion.install_block(rc, completion.build_block("echo hi"))

    completion.remove_block(rc)

    assert rc.read_text() == FOREIGN_BLOCK


def test_no_foreign_warning_for_our_own_block(tmp_path):
    """The predicate must not misfire on the block we just wrote."""
    rc = tmp_path / ".bashrc"
    completion.install_block(rc, completion.build_block("echo hi"))

    result = completion.install_block(rc, completion.build_block("echo bye"))

    assert result.warnings == ()


# ---------------------------------------------------------------------------
# `completion install` / `completion uninstall` — CLI
# ---------------------------------------------------------------------------


def test_completion_install_writes_the_bash_block(runner, tmp_path):
    """End to end: the rc file gains a block carrying the baked path."""
    rc = tmp_path / ".bashrc"

    result = runner.invoke(
        main,
        ["completion", "install", "--shell", "bash", "--rc", str(rc),
         "--bin", BIN],
    )

    assert result.exit_code == 0
    text = rc.read_text()
    assert f"[[ -x {BIN_QUOTED} ]] || return 1" in text
    assert f"_PROJECT_GUIDE_COMPLETE=bash_complete {BIN_QUOTED})" in text
    assert str(rc) in result.output


def test_completion_install_is_idempotent(runner, tmp_path):
    """Re-running reports the no-op rather than stacking blocks."""
    rc = tmp_path / ".bashrc"
    args = ["completion", "install", "--shell", "bash", "--rc", str(rc),
            "--bin", BIN]
    runner.invoke(main, args)
    first = rc.read_text()

    result = runner.invoke(main, args)

    assert result.exit_code == 0
    assert rc.read_text() == first
    assert first.count(completion.SENTINEL_START) == 1
    assert "already" in result.output.lower()


def test_completion_install_quiet_prints_nothing_on_success(runner, tmp_path):
    """`--quiet` is for host tools (pyve) shelling out during provisioning."""
    rc = tmp_path / ".bashrc"

    result = runner.invoke(
        main,
        ["completion", "install", "--shell", "bash", "--rc", str(rc),
         "--bin", BIN, "--quiet"],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert rc.exists()


def test_completion_uninstall_removes_the_block(runner, tmp_path):
    """The CLI round-trip, not just the helper's."""
    rc = tmp_path / ".bashrc"
    rc.write_text("export EDITOR=vim\n")
    runner.invoke(
        main,
        ["completion", "install", "--shell", "bash", "--rc", str(rc),
         "--bin", BIN],
    )

    result = runner.invoke(
        main, ["completion", "uninstall", "--shell", "bash", "--rc", str(rc)]
    )

    assert result.exit_code == 0
    assert rc.read_text() == "export EDITOR=vim\n"


def test_completion_uninstall_on_a_missing_rc_file_succeeds(runner, tmp_path):
    """Nothing to do is exit 0 — uninstall must be safe to run blind."""
    rc = tmp_path / "nonexistent" / ".bashrc"

    result = runner.invoke(
        main, ["completion", "uninstall", "--shell", "bash", "--rc", str(rc)]
    )

    assert result.exit_code == 0
    assert not rc.exists()


def test_completion_install_defaults_to_the_home_bashrc(runner, tmp_path, monkeypatch):
    """Without `--rc`, bash resolves to `~/.bashrc`."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    result = runner.invoke(
        main,
        ["completion", "install", "--shell", "bash", "--bin", BIN],
    )

    assert result.exit_code == 0
    assert (tmp_path / ".bashrc").exists()


def test_completion_install_warns_about_a_foreign_block_on_stderr(runner, tmp_path):
    """The warning is diagnostic, so it must not pollute stdout."""
    rc = tmp_path / ".bashrc"
    rc.write_text(FOREIGN_BLOCK)

    result = runner.invoke(
        main,
        ["completion", "install", "--shell", "bash", "--rc", str(rc),
         "--bin", BIN],
    )

    assert result.exit_code == 0
    assert "my own project-guide completion setup" in result.stderr
    assert "my own project-guide completion setup" not in result.stdout


def test_completion_install_bash_writes_no_autoload_file(runner, tmp_path):
    """bash's route is one artifact; the zsh autoload file must not appear."""
    rc = tmp_path / ".bashrc"

    result = runner.invoke(
        main,
        ["completion", "install", "--shell", "bash", "--rc", str(rc),
         "--bin", BIN],
    )

    assert result.exit_code == 0
    assert list(tmp_path.iterdir()) == [rc]


# ---------------------------------------------------------------------------
# Real-shell verification — silent degradation is mandatory
# ---------------------------------------------------------------------------

BASH = shutil.which("bash")


@pytest.mark.skipif(not BASH, reason="bash is not installed")
def test_installed_block_registers_completion_in_a_real_bash(tmp_path):
    """Sourcing the rc file must actually register, on bash 3.2 and 5.x alike.

    This is the portable proof for Amendment 4: on stock macOS bash the
    `-o nosort` attempt fails and the fallback registers; on modern bash the
    first form wins. Either way `complete -p` reports a specification.
    """
    rc = tmp_path / "rc"
    bin_path = tmp_path / "project-guide"
    bin_path.write_text("#!/bin/sh\nexit 0\n")
    bin_path.chmod(0o755)
    rc.write_text(completion.build_block(completion.build_script("bash", str(bin_path))))

    proc = subprocess.run(
        [BASH, "--norc", "--noprofile", "-c",
         f"source {shlex.quote(str(rc))}; complete -p project-guide"],
        capture_output=True, text=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert "_project_guide_completion" in proc.stdout
    assert proc.stderr == ""


# ---------------------------------------------------------------------------
# `completion status` — inspection
# ---------------------------------------------------------------------------


def _install_bash(tmp_path, bin_path=BIN):
    rc = tmp_path / ".bashrc"
    completion.install_block(rc, completion.build_block(
        completion.build_script("bash", bin_path)
    ))
    return rc


def _install_zsh(tmp_path, bin_path=BIN):
    rc = tmp_path / ".zshrc"
    autoload_dir = tmp_path / "completions"
    completion.install_autoload_file(autoload_dir, completion.build_script("zsh", bin_path))
    completion.install_block(rc, completion.build_block(
        completion.build_zsh_bootstrap(autoload_dir)
    ))
    return rc, autoload_dir


def test_status_reports_absent_when_nothing_is_installed(tmp_path):
    """An uninstalled convenience is not a defect — it is simply absent."""
    status = completion.inspect_shell("bash", rc_path=tmp_path / ".bashrc")

    assert status.state is completion.CompletionState.ABSENT
    assert status.bin_path is None


def test_status_reports_installed_when_the_baked_binary_resolves(tmp_path):
    """The happy path: a block whose baked path is executable."""
    binary = tmp_path / "project-guide"
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)
    rc = _install_bash(tmp_path, str(binary))

    status = completion.inspect_shell("bash", rc_path=rc)

    assert status.state is completion.CompletionState.INSTALLED
    assert status.bin_path == str(binary)


def test_status_reports_stale_for_a_baked_path_that_no_longer_resolves(tmp_path):
    """The pyve-toolchain-bump case, and the reason this command exists.

    Both shells degrade silently in this state, which is exactly why the
    failure was invisible in the field.
    """
    rc = _install_bash(tmp_path, str(tmp_path / "gone" / "project-guide"))

    status = completion.inspect_shell("bash", rc_path=rc)

    assert status.state is completion.CompletionState.STALE


@pytest.mark.skipif(
    WINDOWS,
    reason="Windows has no executable bit: os.access(X_OK) is True for any readable file",
)
def test_status_uses_the_same_predicate_the_installed_script_bakes_in(tmp_path):
    """`status` and the script must agree by construction, not by coincidence.

    A path that exists but is not executable fails the script's `[[ -x ]]`
    guard at TAB time, so it must read as stale here too — an `exists()` check
    would disagree with the shell.

    Windows cannot express the distinction (`os.access(…, os.X_OK)` is True for
    anything readable), so the case is unrepresentable rather than broken
    there. The dominant staleness cause — the path being *gone* — is still
    detected on every platform, and `test_status_reports_stale_for_a_baked_path_that_no_longer_resolves`
    covers it.
    """
    binary = tmp_path / "project-guide"
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o644)  # readable, not executable
    rc = _install_bash(tmp_path, str(binary))

    status = completion.inspect_shell("bash", rc_path=rc)

    assert status.state is completion.CompletionState.STALE


def test_status_reports_a_path_dependent_install_without_calling_it_stale(tmp_path):
    """A bare-name fallback bakes no guard, so the dead-path test cannot apply."""
    rc = tmp_path / ".bashrc"
    completion.install_block(rc, completion.build_block(
        completion.build_script("bash", "project-guide")
    ))

    status = completion.inspect_shell("bash", rc_path=rc)

    assert status.state is completion.CompletionState.INSTALLED
    assert status.bin_path is None
    assert any("PATH" in detail for detail in status.details)


def test_status_reports_a_damaged_block_as_a_defect(tmp_path):
    """An unterminated block is actionable, and must not crash the report."""
    rc = tmp_path / ".bashrc"
    rc.write_text(f"{completion.SENTINEL_START}\nhalf a block\n")

    status = completion.inspect_shell("bash", rc_path=rc)

    assert status.state is completion.CompletionState.DAMAGED


def test_status_notes_a_foreign_block(tmp_path):
    """pyve's legacy block is worth surfacing — R.g is what resolves it."""
    rc = tmp_path / ".bashrc"
    rc.write_text(PYVE_LEGACY_BLOCK)

    status = completion.inspect_shell("bash", rc_path=rc)

    assert any("added by pyve" in detail for detail in status.details)


# --- zsh's two artifacts, including the partial states ---


def test_status_zsh_reports_installed_when_both_artifacts_are_present(tmp_path):
    """Both halves present and the baked path good."""
    binary = tmp_path / "project-guide"
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)
    rc, autoload_dir = _install_zsh(tmp_path, str(binary))

    status = completion.inspect_shell("zsh", rc_path=rc, autoload_dir=autoload_dir)

    assert status.state is completion.CompletionState.INSTALLED
    assert status.autoload_path == autoload_dir / "_project-guide"


def test_status_zsh_reports_partial_when_the_autoload_file_is_missing(tmp_path):
    """rc line without its file: the block is inert, and silently so."""
    rc, autoload_dir = _install_zsh(tmp_path)
    (autoload_dir / "_project-guide").unlink()

    status = completion.inspect_shell("zsh", rc_path=rc, autoload_dir=autoload_dir)

    assert status.state is completion.CompletionState.PARTIAL
    assert any("autoload file" in detail for detail in status.details)


def test_status_zsh_reports_partial_when_the_rc_block_is_missing(tmp_path):
    """File without its rc line: nothing puts the directory on `fpath`."""
    rc, autoload_dir = _install_zsh(tmp_path)
    completion.remove_block(rc)

    status = completion.inspect_shell("zsh", rc_path=rc, autoload_dir=autoload_dir)

    assert status.state is completion.CompletionState.PARTIAL
    assert any("rc block" in detail for detail in status.details)


def test_status_zsh_reads_the_autoload_dir_out_of_the_rc_block(tmp_path):
    """The shell obeys the `fpath` line, so the report must read it too.

    Trusting a `--dir` default over what the rc file actually says would report
    on a directory the shell never consults.
    """
    rc, autoload_dir = _install_zsh(tmp_path)

    status = completion.inspect_shell("zsh", rc_path=rc)  # no autoload_dir hint

    assert status.autoload_path == autoload_dir / "_project-guide"
    assert status.state is completion.CompletionState.STALE  # /opt/pg is not real


def test_status_zsh_finds_the_binary_in_the_autoload_file(tmp_path):
    """zsh's baked path lives in the autoload file, not the rc block."""
    binary = tmp_path / "project-guide"
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)
    rc, autoload_dir = _install_zsh(tmp_path, str(binary))

    status = completion.inspect_shell("zsh", rc_path=rc, autoload_dir=autoload_dir)

    assert status.bin_path == str(binary)


# --- CLI ---


def test_completion_status_reports_both_shells_by_default(runner, tmp_path, monkeypatch):
    """The pyve case is a user whose zsh works and whose bash does not.

    Reporting only the current shell would hide exactly that.
    """
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))

    result = runner.invoke(main, ["completion", "status"])

    assert result.exit_code == 0
    assert "bash" in result.output
    assert "zsh" in result.output


def test_completion_status_exits_zero_when_absent(runner, tmp_path, monkeypatch):
    """Absent is not drift — the same rule R.h inherits for `heal`'s silence."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))

    result = runner.invoke(main, ["completion", "status"])

    assert result.exit_code == 0
    assert "absent" in result.output.lower()


def test_completion_status_exits_one_when_stale(runner, tmp_path):
    """A stale install is an actionable defect, so the exit code says so."""
    rc = _install_bash(tmp_path, str(tmp_path / "gone" / "project-guide"))

    result = runner.invoke(main, ["completion", "status", "--shell", "bash", "--rc", str(rc)])

    assert result.exit_code == 1
    assert "stale" in result.output.lower()


def test_completion_status_names_the_remedy_for_a_stale_install(runner, tmp_path):
    """Inspectable means actionable: the report says how to fix it."""
    rc = _install_bash(tmp_path, str(tmp_path / "gone" / "project-guide"))

    result = runner.invoke(main, ["completion", "status", "--shell", "bash", "--rc", str(rc)])

    assert "completion install" in result.output


def test_completion_status_does_not_offer_reinstall_for_a_damaged_block(runner, tmp_path):
    """`install` refuses to parse an unterminated block, so it is not the fix.

    Suggesting it would send the user in a circle: the command fails with the
    same error the report just showed them.
    """
    rc = tmp_path / ".bashrc"
    rc.write_text(f"{completion.SENTINEL_START}\nhalf a block\n")

    result = runner.invoke(main, ["completion", "status", "--shell", "bash", "--rc", str(rc)])
    reinstall = runner.invoke(
        main,
        ["completion", "install", "--shell", "bash", "--rc", str(rc),
         "--bin", BIN],
    )

    assert result.exit_code == 1
    assert "completion install" not in result.output
    assert reinstall.exit_code != 0  # the suggestion would not have worked


def test_completion_status_exits_one_on_a_partial_zsh_install(runner, tmp_path):
    """Partial is the state R.e's two artifacts made possible."""
    rc, autoload_dir = _install_zsh(tmp_path)
    (autoload_dir / "_project-guide").unlink()

    result = runner.invoke(
        main,
        ["completion", "status", "--shell", "zsh", "--rc", str(rc), "--dir", str(autoload_dir)],
    )

    assert result.exit_code == 1
    assert "partial" in result.output.lower()


def test_completion_status_exits_zero_when_installed_and_current(runner, tmp_path):
    """Clean is quiet in the exit code, even though the report still prints."""
    binary = tmp_path / "project-guide"
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)
    rc = _install_bash(tmp_path, str(binary))

    result = runner.invoke(main, ["completion", "status", "--shell", "bash", "--rc", str(rc)])

    assert result.exit_code == 0
    assert "installed" in result.output.lower()


def test_completion_status_refuses_rc_without_a_shell(runner, tmp_path):
    """`--rc` is ambiguous across two shells; refusing beats guessing one."""
    result = runner.invoke(main, ["completion", "status", "--rc", str(tmp_path / ".bashrc")])

    assert result.exit_code != 0
    assert "--shell" in result.output


def test_completion_status_writes_nothing_to_the_filesystem(runner, tmp_path, monkeypatch):
    """A reporting surface must never repair what it reports."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    before = set(tmp_path.rglob("*"))

    runner.invoke(main, ["completion", "status"])

    assert set(tmp_path.rglob("*")) == before


def test_completion_help_lists_status(runner):
    """Discoverable alongside the rest of the group."""
    result = runner.invoke(main, ["completion", "--help"])

    assert "status" in result.output


ZSH = shutil.which("zsh")


def _zsh_registration(rc: Path, *, precompinit: bool) -> str:
    """Return what zsh has registered for `project-guide` after sourcing `rc`.

    `$_comps` is the table `compinit` builds from `fpath`, and it is the
    definitive answer to "will TAB find our completion" — deterministic and
    scriptable, unlike driving a real TAB through a pty.

    `precompinit` simulates the common case the ordering trap lives in: the
    user's rc file already ran `compinit` before our block is appended.
    """
    prelude = "autoload -Uz compinit && compinit -i -d /dev/null; " if precompinit else ""
    proc = subprocess.run(
        [str(ZSH), "-f", "-c",
         f"{prelude}source {shlex.quote(str(rc))}; "
         "print -r -- \"comps=${_comps[project-guide]:-NONE}\""],
        capture_output=True, text=True,
    )
    assert proc.stderr == "", proc.stderr
    return proc.stdout.strip()


@pytest.mark.skipif(not ZSH, reason="zsh is not installed")
def test_zsh_block_registers_when_compinit_already_ran(tmp_path):
    """The ordering trap: an `fpath` entry added after `compinit` is ignored.

    Our block is appended to the *end* of `~/.zshrc`, which for most users is
    after oh-my-zsh or a hand-rolled `compinit`. Adding to `fpath` at that
    point registers nothing — verified directly: `_comps[project-guide]` is
    unset. The block therefore registers explicitly when `compdef` already
    exists, rather than relying on a `compinit` that has been and gone.
    """
    autoload_dir = tmp_path / "completions"
    completion.install_autoload_file(
        autoload_dir, completion.build_script("zsh", BIN)
    )
    rc = tmp_path / ".zshrc"
    completion.install_block(rc, completion.build_block(
        completion.build_zsh_bootstrap(autoload_dir)
    ))

    assert _zsh_registration(rc, precompinit=True) == "comps=_project-guide"


@pytest.mark.skipif(not ZSH, reason="zsh is not installed")
def test_zsh_block_bootstraps_compinit_when_it_never_ran(tmp_path):
    """Field defect 1: without `compinit`, `compdef` does not exist at all."""
    autoload_dir = tmp_path / "completions"
    completion.install_autoload_file(
        autoload_dir, completion.build_script("zsh", BIN)
    )
    rc = tmp_path / ".zshrc"
    completion.install_block(rc, completion.build_block(
        completion.build_zsh_bootstrap(autoload_dir)
    ))

    assert _zsh_registration(rc, precompinit=False) == "comps=_project-guide"


@pytest.mark.skipif(not ZSH, reason="zsh is not installed")
def test_zsh_block_is_inert_when_the_autoload_file_is_gone(tmp_path):
    """Half-uninstalled must be silent, not a broken registration.

    Registering a `compdef` against a function whose file no longer exists
    defers the failure to TAB time, which is exactly the noise the subphase
    forbids. The block tests for its own file first.
    """
    autoload_dir = tmp_path / "completions"
    rc = tmp_path / ".zshrc"
    completion.install_block(rc, completion.build_block(
        completion.build_zsh_bootstrap(autoload_dir)
    ))

    assert _zsh_registration(rc, precompinit=True) == "comps=NONE"


# ---------------------------------------------------------------------------
# zsh autoload file
# ---------------------------------------------------------------------------


def test_install_autoload_file_writes_the_compdef_script(tmp_path):
    """The file is named for the command and keeps its `#compdef` header."""
    autoload_dir = tmp_path / "completions"

    result = completion.install_autoload_file(
        autoload_dir, completion.build_script("zsh", BIN)
    )

    written = autoload_dir / "_project-guide"
    assert result.outcome is completion.RcOutcome.CREATED
    assert written.read_text().startswith("#compdef project-guide")
    assert f"[[ -x {BIN_QUOTED} ]] || return 1" in written.read_text()


def test_install_autoload_file_is_idempotent(tmp_path):
    """Unchanged content is a no-op, so re-running install reports honestly."""
    autoload_dir = tmp_path / "completions"
    script = completion.build_script("zsh", BIN)
    completion.install_autoload_file(autoload_dir, script)

    result = completion.install_autoload_file(autoload_dir, script)

    assert result.outcome is completion.RcOutcome.UNCHANGED


def test_install_autoload_file_refreshes_a_changed_script(tmp_path):
    """A moved binary rewrites the file rather than leaving a stale path."""
    autoload_dir = tmp_path / "completions"
    old_bin = abs_bin("old", "project-guide")
    new_bin = abs_bin("new", "project-guide")
    completion.install_autoload_file(
        autoload_dir, completion.build_script("zsh", old_bin)
    )

    result = completion.install_autoload_file(
        autoload_dir, completion.build_script("zsh", new_bin)
    )

    assert result.outcome is completion.RcOutcome.UPDATED
    assert old_bin not in (autoload_dir / "_project-guide").read_text()
    assert new_bin in (autoload_dir / "_project-guide").read_text()


def test_remove_autoload_file_deletes_it_and_its_empty_owned_dir(tmp_path, monkeypatch):
    """We created the default directory, so we clean it up — but only if empty."""
    autoload_dir = tmp_path / "share" / "project-guide" / "zsh-completions"
    monkeypatch.setattr(completion, "default_autoload_dir", lambda: autoload_dir)
    completion.install_autoload_file(autoload_dir, "#compdef project-guide\n")

    result = completion.remove_autoload_file(autoload_dir)

    assert result.outcome is completion.RcOutcome.REMOVED
    assert not autoload_dir.exists()


def test_remove_autoload_file_keeps_a_user_supplied_dir(tmp_path):
    """`--dir` points at a directory the user owns; emptying it is not ours to do."""
    autoload_dir = tmp_path / "my-completions"
    completion.install_autoload_file(autoload_dir, "#compdef project-guide\n")

    completion.remove_autoload_file(autoload_dir)

    assert autoload_dir.exists()
    assert not (autoload_dir / "_project-guide").exists()


def test_remove_autoload_file_keeps_a_dir_that_still_has_content(tmp_path, monkeypatch):
    """Another tool's completions in our default dir must survive."""
    autoload_dir = tmp_path / "completions"
    monkeypatch.setattr(completion, "default_autoload_dir", lambda: autoload_dir)
    completion.install_autoload_file(autoload_dir, "#compdef project-guide\n")
    (autoload_dir / "_something-else").write_text("#compdef something-else\n")

    completion.remove_autoload_file(autoload_dir)

    assert (autoload_dir / "_something-else").exists()


def test_remove_autoload_file_reports_absent_when_there_is_nothing(tmp_path):
    """Safe to run blind, same as the rc-block half."""
    result = completion.remove_autoload_file(tmp_path / "nope")

    assert result.outcome is completion.RcOutcome.ABSENT


def test_default_autoload_dir_honors_xdg_data_home(tmp_path, monkeypatch):
    """pyve is XDG-aware, and this is the directory project-guide owns."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))

    assert completion.default_autoload_dir() == (
        tmp_path / "xdg" / "project-guide" / "zsh-completions"
    )


def test_default_autoload_dir_falls_back_to_local_share(tmp_path, monkeypatch):
    """Without XDG_DATA_HOME, the conventional `~/.local/share` root."""
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    assert completion.default_autoload_dir() == (
        tmp_path / ".local" / "share" / "project-guide" / "zsh-completions"
    )


# ---------------------------------------------------------------------------
# zsh install / uninstall — CLI, two artifacts
# ---------------------------------------------------------------------------


def test_completion_install_zsh_writes_both_artifacts(runner, tmp_path):
    """The asymmetric half: an autoload file *and* an rc block."""
    rc = tmp_path / ".zshrc"
    autoload_dir = tmp_path / "completions"

    result = runner.invoke(
        main,
        ["completion", "install", "--shell", "zsh", "--rc", str(rc),
         "--dir", str(autoload_dir), "--bin", BIN],
    )

    assert result.exit_code == 0
    assert (autoload_dir / "_project-guide").read_text().startswith("#compdef")
    rc_text = rc.read_text()
    assert str(autoload_dir) in rc_text
    assert "compinit" in rc_text
    assert "#compdef" not in rc_text  # the script lives in the file, not the rc


def test_completion_install_zsh_is_idempotent_across_both_artifacts(runner, tmp_path):
    """Neither artifact is rewritten when both are already current."""
    rc = tmp_path / ".zshrc"
    autoload_dir = tmp_path / "completions"
    args = ["completion", "install", "--shell", "zsh", "--rc", str(rc),
            "--dir", str(autoload_dir), "--bin", BIN]
    runner.invoke(main, args)
    before = ((autoload_dir / "_project-guide").read_text(), rc.read_text())

    result = runner.invoke(main, args)

    assert result.exit_code == 0
    assert ((autoload_dir / "_project-guide").read_text(), rc.read_text()) == before
    assert "already" in result.output.lower()


def test_completion_uninstall_zsh_removes_both_artifacts(runner, tmp_path):
    """And the rc file round-trips byte-for-byte, as in the bash route."""
    rc = tmp_path / ".zshrc"
    autoload_dir = tmp_path / "completions"
    original = "export EDITOR=vim\n"
    rc.write_text(original)
    runner.invoke(
        main,
        ["completion", "install", "--shell", "zsh", "--rc", str(rc),
         "--dir", str(autoload_dir), "--bin", BIN],
    )

    result = runner.invoke(
        main,
        ["completion", "uninstall", "--shell", "zsh", "--rc", str(rc),
         "--dir", str(autoload_dir)],
    )

    assert result.exit_code == 0
    assert rc.read_text() == original
    assert not (autoload_dir / "_project-guide").exists()


@pytest.mark.parametrize("drop", ["file", "rc"])
def test_completion_install_zsh_repairs_a_partial_state(runner, tmp_path, drop):
    """Either artifact can go missing on its own; install restores the pair."""
    rc = tmp_path / ".zshrc"
    autoload_dir = tmp_path / "completions"
    args = ["completion", "install", "--shell", "zsh", "--rc", str(rc),
            "--dir", str(autoload_dir), "--bin", BIN]
    runner.invoke(main, args)
    if drop == "file":
        (autoload_dir / "_project-guide").unlink()
    else:
        rc.write_text("export EDITOR=vim\n")

    result = runner.invoke(main, args)

    assert result.exit_code == 0
    assert (autoload_dir / "_project-guide").exists()
    assert completion.SENTINEL_START in rc.read_text()
    assert "already" not in result.output.lower()


@pytest.mark.parametrize("drop", ["file", "rc"])
def test_completion_uninstall_zsh_handles_a_partial_state(runner, tmp_path, drop):
    """Uninstall removes whatever half survives, without erroring on the other."""
    rc = tmp_path / ".zshrc"
    autoload_dir = tmp_path / "completions"
    runner.invoke(
        main,
        ["completion", "install", "--shell", "zsh", "--rc", str(rc),
         "--dir", str(autoload_dir), "--bin", BIN],
    )
    if drop == "file":
        (autoload_dir / "_project-guide").unlink()
    else:
        rc.write_text("")

    result = runner.invoke(
        main,
        ["completion", "uninstall", "--shell", "zsh", "--rc", str(rc),
         "--dir", str(autoload_dir)],
    )

    assert result.exit_code == 0
    assert not (autoload_dir / "_project-guide").exists()
    assert completion.SENTINEL_START not in rc.read_text()


def test_completion_install_zsh_defaults_to_the_home_zshrc(runner, tmp_path, monkeypatch):
    """Without `--rc`, zsh resolves to `~/.zshrc` — not bash's `~/.bashrc`."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    result = runner.invoke(
        main,
        ["completion", "install", "--shell", "zsh", "--bin", BIN],
    )

    assert result.exit_code == 0
    assert (tmp_path / ".zshrc").exists()
    assert not (tmp_path / ".bashrc").exists()
    assert (tmp_path / "xdg" / "project-guide" / "zsh-completions" / "_project-guide").exists()


def test_completion_install_bash_ignores_the_dir_option(runner, tmp_path):
    """`--dir` is a zsh concept; passing it to bash must not silently mislead."""
    rc = tmp_path / ".bashrc"

    result = runner.invoke(
        main,
        ["completion", "install", "--shell", "bash", "--rc", str(rc),
         "--dir", str(tmp_path / "completions"), "--bin", BIN],
    )

    assert result.exit_code != 0
    assert "--dir" in result.output


@pytest.mark.skipif(not BASH, reason="bash is not installed")
def test_a_stale_install_degrades_silently_in_a_real_bash(tmp_path):
    """Amendment 2, verified on the installed artifact rather than the source.

    Without the inserted `[[ -x ]]` guard, a `--bin` that no longer resolves
    makes `env` print "No such file or directory" on *every* TAB press — a
    worse regression than the missing completion it replaces.
    """
    rc = tmp_path / "rc"
    dead = tmp_path / "gone" / "project-guide"
    rc.write_text(completion.build_block(completion.build_script("bash", str(dead))))

    proc = subprocess.run(
        [BASH, "--norc", "--noprofile", "-c",
         f"source {shlex.quote(str(rc))}; "
         "COMP_WORDS='project-guide '; COMP_CWORD=1; "
         "_project_guide_completion project-guide; echo done"],
        capture_output=True, text=True,
    )

    assert proc.stdout.strip() == "done"
    assert proc.stderr == ""


# ---------------------------------------------------------------------------
# Story R.r — staleness is "would reinstalling change anything?"
#
# R.f defined stale as the dead-path test alone and flagged the gap in the
# same breath; R.h inherited it and re-flagged it. A block generated by an
# older project-guide whose script template has since changed keeps reporting
# `installed` while completing against a template nobody ships any more.
#
# The version stamp is deliberately NOT the predicate. Comparing it to
# __version__ would fire on every release, including the large majority that
# never touch the template — the noise R.h explicitly refused to risk.
# ---------------------------------------------------------------------------


def _executable(tmp_path, name="project-guide"):
    binary = tmp_path / name
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)
    return str(binary)


def _rewrite(path: Path, old: str, new: str) -> None:
    """Edit an installed artifact in place, asserting the edit actually landed."""
    text = path.read_text()
    assert old in text, f"fixture drift: {old!r} not found in {path}"
    path.write_text(text.replace(old, new, 1))


def test_a_drifted_bash_script_reads_as_stale(tmp_path):
    """The gap R.f left open: the callback no longer matches what we generate.

    Edited here rather than mocked, because the point is that the *installed
    text* is the input — that is what the shell sources.
    """
    binary = _executable(tmp_path)
    rc = _install_bash(tmp_path, binary)
    _rewrite(rc, "COMP_WORDS", "COMP_WORDS_OLD_TEMPLATE")

    status = completion.inspect_shell("bash", rc_path=rc)

    assert status.state is completion.CompletionState.STALE
    assert status.bin_path == binary
    assert any("reinstall" in d.lower() or "differs" in d.lower() for d in status.details)


def test_a_drifted_zsh_autoload_file_reads_as_stale(tmp_path):
    """zsh keeps the callback in the autoload file, so that is what must match."""
    binary = _executable(tmp_path)
    rc, autoload_dir = _install_zsh(tmp_path, binary)
    _rewrite(autoload_dir / completion.AUTOLOAD_FILENAME, "#compdef", "#compdef_old")

    status = completion.inspect_shell("zsh", rc_path=rc, autoload_dir=autoload_dir)

    assert status.state is completion.CompletionState.STALE


def test_a_drifted_zsh_bootstrap_reads_as_stale(tmp_path):
    """zsh has two artifacts and either can drift on its own.

    The bootstrap is the half that grew requirement 3 (registering explicitly
    when `compinit` already ran). A block predating that change wires up
    nothing, while its autoload file looks perfect.
    """
    binary = _executable(tmp_path)
    rc, autoload_dir = _install_zsh(tmp_path, binary)
    _rewrite(rc, "$+functions[compdef]", "$+functions[compdef_old]")

    status = completion.inspect_shell("zsh", rc_path=rc, autoload_dir=autoload_dir)

    assert status.state is completion.CompletionState.STALE


def test_a_current_install_is_not_stale(tmp_path):
    """The property that makes the predicate usable at all: silence when current."""
    binary = _executable(tmp_path)
    rc = _install_bash(tmp_path, binary)

    status = completion.inspect_shell("bash", rc_path=rc)

    assert status.state is completion.CompletionState.INSTALLED


def test_a_current_zsh_install_is_not_stale(tmp_path):
    """Both zsh artifacts compare clean, including the `fpath`-recovered directory."""
    binary = _executable(tmp_path)
    rc, autoload_dir = _install_zsh(tmp_path, binary)

    status = completion.inspect_shell("zsh", rc_path=rc, autoload_dir=autoload_dir)

    assert status.state is completion.CompletionState.INSTALLED


def test_a_version_bump_that_leaves_the_template_alone_does_not_warn(tmp_path):
    """The whole reason the stamp is not the predicate.

    Most releases never touch the completion template. If the stamp decided
    staleness, every one of them would warn from the pre-invoke hook, ahead of
    every command, for every user — turning a precise signal into noise.
    """
    binary = _executable(tmp_path)
    rc = _install_bash(tmp_path, binary)
    _rewrite(rc, f"project-guide v{__version__}", "project-guide v0.0.1")

    status = completion.inspect_shell("bash", rc_path=rc)

    assert status.state is completion.CompletionState.INSTALLED


def test_the_stamp_is_reported_diagnostically_when_the_script_did_drift(tmp_path):
    """Not decisional, but worth naming once something else has decided.

    "Your block came from v2.19.0" is the sentence that tells a developer
    which upgrade left it behind.
    """
    binary = _executable(tmp_path)
    rc = _install_bash(tmp_path, binary)
    _rewrite(rc, f"project-guide v{__version__}", "project-guide v2.19.0")
    _rewrite(rc, "COMP_WORDS", "COMP_WORDS_OLD_TEMPLATE")

    status = completion.inspect_shell("bash", rc_path=rc)

    assert status.state is completion.CompletionState.STALE
    assert any("2.19.0" in d for d in status.details)


def test_a_block_from_a_newer_project_guide_is_not_called_stale(tmp_path):
    """Warn less, per the plan's stated failure direction.

    project-guide is routinely installed twice — a pyve toolchain copy and a
    project-local one (the whole subject of Subphase Q-4). When the older
    install inspects a block the newer one wrote, regeneration differs, but
    "stale" is backwards: reinstalling here would *downgrade* it. The stamp
    suppresses the warning without ever being what fires it.
    """
    binary = _executable(tmp_path)
    rc = _install_bash(tmp_path, binary)
    _rewrite(rc, f"project-guide v{__version__}", "project-guide v99.0.0")
    _rewrite(rc, "COMP_WORDS", "COMP_WORDS_FROM_THE_FUTURE")

    status = completion.inspect_shell("bash", rc_path=rc)

    assert status.state is completion.CompletionState.INSTALLED


def test_a_bare_name_install_still_reports_installed(tmp_path):
    """No baked `--bin` means no parameter to regenerate from.

    Guessing one would compare against a script we cannot know was requested,
    so this install keeps reporting `installed` with its PATH note. Warning
    less is the correct failure direction.
    """
    rc = tmp_path / ".bashrc"
    completion.install_block(rc, completion.build_block(
        completion.build_script("bash", "project-guide")
    ))
    _rewrite(rc, "COMP_WORDS", "COMP_WORDS_OLD_TEMPLATE")

    status = completion.inspect_shell("bash", rc_path=rc)

    assert status.state is completion.CompletionState.INSTALLED
    assert status.bin_path is None
    assert any("PATH" in detail for detail in status.details)


def test_the_dead_path_test_still_wins_over_content(tmp_path):
    """A dead binary is the more actionable diagnosis, so it keeps priority.

    Both conditions can hold at once (an old block whose baked path also
    rotted); the message that names the dead path is the one that helps.
    """
    rc = _install_bash(tmp_path, str(tmp_path / "gone" / "project-guide"))
    _rewrite(rc, "COMP_WORDS", "COMP_WORDS_OLD_TEMPLATE")

    status = completion.inspect_shell("bash", rc_path=rc)

    assert status.state is completion.CompletionState.STALE
    assert any("not executable" in d for d in status.details)


def test_partial_and_damaged_states_are_unchanged(tmp_path):
    """The widened predicate runs after the structural states, not instead of them."""
    binary = _executable(tmp_path)
    rc, autoload_dir = _install_zsh(tmp_path, binary)
    (autoload_dir / completion.AUTOLOAD_FILENAME).unlink()

    status = completion.inspect_shell("zsh", rc_path=rc, autoload_dir=autoload_dir)

    assert status.state is completion.CompletionState.PARTIAL

    damaged = tmp_path / "damaged"
    damaged.write_text(completion.SENTINEL_START + "\nno terminator\n")
    assert completion.inspect_shell(
        "bash", rc_path=damaged
    ).state is completion.CompletionState.DAMAGED


def test_inspection_never_writes_to_stderr(tmp_path, capsys):
    """`inspect_shell` runs from the pre-invoke hook, ahead of every command.

    Regenerating a bash script makes Click call `_check_version`, which prints
    "Shell completion is not supported for Bash versions older than 4.4."
    whenever `PATH` finds macOS system bash 3.2. Right at install time, wrong
    here — it would become a line on every invocation, which is the noise this
    story exists to avoid rather than create.
    """
    binary = _executable(tmp_path)
    rc = _install_bash(tmp_path, binary)
    capsys.readouterr()

    completion.inspect_shell("bash", rc_path=rc)

    assert capsys.readouterr().err == ""


def test_the_comparison_script_is_generated_once_per_process(tmp_path):
    """The hook should stay cheap: Click's bash generator shells out."""
    binary = _executable(tmp_path)
    rc = _install_bash(tmp_path, binary)
    completion._script_for_comparison.cache_clear()

    completion.inspect_shell("bash", rc_path=rc)
    completion.inspect_shell("bash", rc_path=rc)

    info = completion._script_for_comparison.cache_info()
    assert info.misses == 1
    assert info.hits >= 1
