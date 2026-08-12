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
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from project_guide import completion
from project_guide.cli import main
from project_guide.exceptions import CompletionError


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


# ---------------------------------------------------------------------------
# Script generation
# ---------------------------------------------------------------------------


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
        completion.postprocess_script("", shell="fish", bin_path="/opt/pg/project-guide")


# ---------------------------------------------------------------------------
# Post-processing — zsh
# ---------------------------------------------------------------------------


def test_postprocess_zsh_replaces_path_guard_with_executable_test():
    """The `$+commands` PATH guard becomes a filesystem test on the baked path."""
    script = completion.generate_script("zsh")

    result = completion.postprocess_script(script, shell="zsh", bin_path="/opt/pg/project-guide")

    assert "$+commands" not in result
    assert "    [[ -x /opt/pg/project-guide ]] || return 1" in result


def test_postprocess_zsh_substitutes_bin_path_in_callback():
    """The completion callback invokes the absolute path, not the bare name."""
    script = completion.generate_script("zsh")

    result = completion.postprocess_script(script, shell="zsh", bin_path="/opt/pg/project-guide")

    assert "_PROJECT_GUIDE_COMPLETE=zsh_complete /opt/pg/project-guide)" in result
    assert "_PROJECT_GUIDE_COMPLETE=zsh_complete project-guide" not in result


def test_postprocess_zsh_preserves_the_typed_command_name():
    """`#compdef` and `compdef` register against the name the user types.

    A blanket substitution of the command name would break both — the spike's
    central caution about naive rewriting.
    """
    script = completion.generate_script("zsh")

    result = completion.postprocess_script(script, shell="zsh", bin_path="/opt/pg/project-guide")

    assert result.startswith("#compdef project-guide")
    assert "compdef _project_guide_completion project-guide" in result


def test_postprocess_zsh_preserves_surrounding_blank_lines():
    """Rewrites are line-local; the script's shape is otherwise untouched."""
    script = completion.generate_script("zsh")

    result = completion.postprocess_script(script, shell="zsh", bin_path="/opt/pg/project-guide")

    assert len(result.splitlines()) == len(script.splitlines())


# ---------------------------------------------------------------------------
# Post-processing — bash
# ---------------------------------------------------------------------------


def test_postprocess_bash_substitutes_bin_path_for_positional_arg():
    """`$1` (the PATH-resolved command word) becomes the baked path."""
    script = completion.generate_script("bash")

    result = completion.postprocess_script(script, shell="bash", bin_path="/opt/pg/project-guide")

    assert "_PROJECT_GUIDE_COMPLETE=bash_complete /opt/pg/project-guide)" in result
    assert "_PROJECT_GUIDE_COMPLETE=bash_complete $1" not in result


def test_postprocess_bash_inserts_executable_guard_above_the_callback():
    """R.b Amendment 2: bash ships no guard, so a stale path would print on every TAB."""
    script = completion.generate_script("bash")

    result = completion.postprocess_script(script, shell="bash", bin_path="/opt/pg/project-guide")

    lines = result.splitlines()
    callback_index = next(i for i, line in enumerate(lines) if "bash_complete" in line)
    assert lines[callback_index - 1] == "    [[ -x /opt/pg/project-guide ]] || return 1"


def test_postprocess_bash_keeps_registration_line_intact():
    """The `complete -F … project-guide` registration still targets the typed name."""
    script = completion.generate_script("bash")

    result = completion.postprocess_script(script, shell="bash", bin_path="/opt/pg/project-guide")

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
            "# nothing here Click would recognize\n", shell=shell, bin_path="/opt/pg/project-guide"
        )


def test_postprocess_raises_when_the_zsh_guard_pattern_is_missing():
    """The zsh PATH guard is equally load-bearing and equally asserted."""
    script = completion.generate_script("zsh")
    without_guard = script.replace("(( ! $+commands[project-guide] )) && return 1\n", "")

    with pytest.raises(CompletionError, match="guard"):
        completion.postprocess_script(
            without_guard, shell="zsh", bin_path="/opt/pg/project-guide"
        )


# ---------------------------------------------------------------------------
# build_script — the absolute-path gate (R.b Amendment 3)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("shell", ["zsh", "bash"])
def test_build_script_post_processes_an_absolute_bin_path(shell):
    """An absolute `--bin` is the post-processed branch."""
    result = completion.build_script(shell, "/opt/pg/project-guide")

    assert "/opt/pg/project-guide" in result


@pytest.mark.parametrize("shell", ["zsh", "bash"])
def test_build_script_emits_click_output_verbatim_for_a_bare_name(shell):
    """The baked guard is a filesystem test, so a bare name must not be baked in.

    R.b Amendment 3 — the bare-name `PATH` fallback keeps Click's historical
    behavior rather than emitting `[[ -x project-guide ]]`, which would test a
    file relative to `$PWD`.
    """
    result = completion.build_script(shell, "project-guide")

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

    assert completion.resolve_bin("/opt/pg/project-guide") == "/opt/pg/project-guide"


def test_resolve_bin_expands_a_tilde(monkeypatch):
    """pyve passes `~/.local/bin/project-guide`; the script needs it expanded."""
    monkeypatch.setenv("HOME", "/home/dev")

    assert completion.resolve_bin("~/.local/bin/project-guide") == (
        os.path.join("/home/dev", ".local/bin/project-guide")
    )


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
    result = runner.invoke(main, ["completion", "show", "--shell", "zsh", "--bin", "/opt/pg/project-guide"])

    assert result.exit_code == 0
    assert result.output.startswith("#compdef project-guide")
    assert "_PROJECT_GUIDE_COMPLETE=zsh_complete /opt/pg/project-guide)" in result.output


def test_completion_show_prints_the_bash_script(runner):
    """The bash route emits the guarded, path-substituted script."""
    result = runner.invoke(main, ["completion", "show", "--shell", "bash", "--bin", "/opt/pg/project-guide"])

    assert result.exit_code == 0
    assert "[[ -x /opt/pg/project-guide ]] || return 1" in result.output


def test_completion_show_stdout_is_only_the_script(runner):
    """`eval "$(project-guide completion show)"` must not swallow chatter."""
    result = runner.invoke(main, ["completion", "show", "--shell", "bash", "--bin", "/opt/pg/project-guide"])

    assert result.output.rstrip("\n").endswith("_project_guide_completion_setup;")


def test_completion_show_auto_detects_the_shell(runner, monkeypatch):
    """No `--shell` means `auto`, which reads `$SHELL`."""
    monkeypatch.setenv("SHELL", "/bin/zsh")

    result = runner.invoke(main, ["completion", "show", "--bin", "/opt/pg/project-guide"])

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
            ["completion", "show", "--shell", "zsh", "--bin", "/opt/pg/project-guide"],
            input="n\n",
        )

        assert result.exit_code == 0
        assert result.stdout.startswith("#compdef project-guide")
        assert "Update?" not in result.stdout
        assert "Update?" in result.stderr


def test_completion_show_stdout_is_pure_when_the_heal_hook_auto_heals(runner, tmp_path, monkeypatch):
    """Same guarantee on the --no-input branch, whose notice is non-suppressible."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        assert runner.invoke(main, ["init"]).exit_code == 0
        Path("docs/project-guide/README.md").unlink()
        monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)

        result = runner.invoke(
            main, ["completion", "show", "--shell", "bash", "--bin", "/opt/pg/project-guide"]
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
            main, ["completion", "show", "--shell", "zsh", "--bin", "/opt/pg/project-guide"]
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
