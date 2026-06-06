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

"""Cross-repo contract tests (Story Q.l).

These tests pin the three already-holding cross-repo contracts that Pyve
depends on when it hosts project-guide as a globally-shimmed tool in its
toolchain venv (Pyve Story N.aw):

1. **Install-location independence** — per-project state is written to the
   current working directory, never to the package install location.
2. **`--version` output format** — the exact ``project-guide, version X.Y.Z``
   shape Pyve parses.
3. **`.project-guide.yml` marker shape** — the project-root marker filename
   and its cross-repo field subset.

The contracts are documented in ``docs/specs/project-essentials.md``
("Pyve cross-repo contracts") and ``docs/specs/features.md``
("Cross-Repo Contracts"). Changing any of these is a coordinated breaking
change requiring a paired Pyve story — see those docs.
"""

import re
import tomllib
from pathlib import Path

import yaml
from click.testing import CliRunner

import project_guide
from project_guide.cli import main

# Repo root = two levels up from this test file (tests/ -> repo root).
_REPO_ROOT = Path(__file__).resolve().parent.parent


def _package_file_mtimes() -> dict[Path, int]:
    """Snapshot mtimes of every real source file in the installed package.

    Excludes ``__pycache__`` / ``.pyc`` artifacts, which the interpreter may
    (re)write independently of any project-guide command.
    """
    pkg_dir = Path(project_guide.__file__).parent
    return {
        p: p.stat().st_mtime_ns
        for p in pkg_dir.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }


def test_per_project_state_written_to_cwd_not_package_location(tmp_path):
    """Contract 1: init/update/mode write only to the cwd, never the package.

    Pyve hosts a single toolchain-venv install of project-guide and shims it
    onto PATH; each consumer project must keep its state under its own root,
    not bleed back into the shared install location.
    """
    runner = CliRunner()
    before = _package_file_mtimes()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # init writes per-project state to the cwd
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0
        assert Path(".project-guide.yml").exists()
        assert Path("docs/project-guide/go.md").exists()

        # update and mode operate on the cwd project, too
        assert runner.invoke(main, ["update"]).exit_code == 0
        assert runner.invoke(main, ["mode", "code_direct"]).exit_code == 0

    # The package install location is untouched by any of the three commands.
    after = _package_file_mtimes()
    assert before == after


def test_version_output_format_is_cross_repo_contract(tmp_path):
    """Contract 2: ``project-guide --version`` emits ``project-guide, version X.Y.Z``.

    Pyve parses the version number out of this output, and the binary it runs is
    named ``project-guide``. The full contract is pinned in two robust pieces:

    * **Format** — the ``--version`` output matches ``<prog>, version X.Y.Z``.
      The *prog* token is asserted loosely here on purpose: Click's
      ``version_option`` memoizes the program name in a closure ``nonlocal`` on
      the first ``--version`` call in the process, so whichever test invokes
      ``--version`` first pins it for the rest of the session — CliRunner's
      ``prog_name`` cannot be relied on to read back ``project-guide``. The
      version-number shape is what Pyve actually parses, and that is pinned
      exactly.
    * **Program name** — the ``project-guide`` console-script entry point in
      ``pyproject.toml`` is what makes the *shipped* binary print
      ``project-guide, ...``. Asserting that entry point pins the name half of
      the contract at its real source, independent of Click's in-process
      memoization quirk.

    Changing either half (the ``--version`` format or the script name) is a
    coordinated breaking change requiring a paired Pyve story.
    """
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert re.fullmatch(r".+, version \d+\.\d+\.\d+\n?", result.output)

    # Program-name half: the shipped binary is named `project-guide`, wired to
    # the same `main` group this test imports.
    pyproject = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["scripts"]["project-guide"] == "project_guide.cli:main"


def test_project_guide_yml_marker_shape(tmp_path):
    """Contract 3: the project-root marker filename and field subset are stable.

    Pyve locates and reads ``.project-guide.yml`` at the project root and
    relies on a minimum field set. Additional fields may exist; their absence
    is *not* a contract violation, so only the cross-repo subset is asserted.
    """
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0

        marker = Path(".project-guide.yml")
        assert marker.exists()  # exact filename, project root, no extension drift

        data = yaml.safe_load(marker.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        for field in ("version", "installed_version", "target_dir", "current_mode"):
            assert field in data, f"cross-repo field {field!r} missing from marker"
