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

import importlib.resources
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click

from project_guide.actions import ActionType, perform_archive
from project_guide.config import Config
from project_guide.exceptions import (
    ActionError,
    ConfigError,
    MetadataError,
    RenderError,
    SchemaVersionError,
    SyncError,
)
from project_guide.metadata import ModeDefinition, _apply_metadata_overrides, load_metadata
from project_guide.render import render_go_project_guide
from project_guide.runtime import (
    _detect_project_name_from_pyproject,
    _resolve_setting,
    should_skip_input,
)
from project_guide.stories import (
    _read_done_stories,
    _read_stories_summary,
    derive_bundle_commit_message,
    derive_commit_message,
    parse_committed_ids_from_subject,
)
from project_guide.sync import (
    file_matches_template,
    get_all_file_names,
    sync_files,
)
from project_guide.version import __version__


def _migrate_config_if_needed() -> None:
    """Rename .project-guides.yml to .project-guide.yml if the old file exists."""
    old_path = Path(".project-guides.yml")
    new_path = Path(".project-guide.yml")
    if old_path.exists() and not new_path.exists():
        old_path.rename(new_path)
        click.secho(f"Migrated {old_path} → {new_path}", fg='yellow')


# Recursion guard env var: set to "1" while heal is running so any nested
# `project-guide` subprocess invocations don't re-enter the auto-hook.
_HEAL_GUARD_ENV = "PROJECT_GUIDE_HEALING"


class HealGroup(click.Group):
    """Top-level group that invokes the auto-heal hook before every command.

    The hook fires for every invocation — including ``--help`` and
    ``--version`` — by overriding :meth:`Group.main` (which runs before
    ``make_context``, where eager flags would otherwise short-circuit).
    The hook is silent in the steady state and only prompts when there is
    actual drift; declining the prompt does not block the original
    subcommand. The recursion guard env var prevents nested invocations
    from re-entering.
    """

    def main(self, *args, **kwargs):
        _run_pre_invoke_hook()
        return super().main(*args, **kwargs)


@click.group(cls=HealGroup)
@click.version_option(version=__version__)
def main():
    """Manage LLM project guide across repositories."""
    _migrate_config_if_needed()


def _get_package_template_dir() -> Path:
    """Get the path to the bundled project-guide templates in the package."""
    with importlib.resources.as_file(
        importlib.resources.files("project_guide.templates").joinpath("project-guide")
    ) as path:
        return Path(path)


def _copy_template_tree(
    src_dir: Path, dest_dir: Path, force: bool = False, quiet: bool = False
) -> int:
    """
    Copy a template directory tree to the target, preserving structure.
    Returns the number of files copied.
    """
    count = 0
    for src_file in sorted(src_dir.rglob("*")):
        if not src_file.is_file():
            continue
        rel_path = src_file.relative_to(src_dir)
        dest_file = dest_dir / rel_path

        if dest_file.exists() and not force:
            if not quiet:
                click.secho(f"⚠ Skipped {rel_path} (already exists)", fg='yellow')
            continue

        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        if not quiet:
            click.secho(f"✓ Installed {rel_path}", fg='green')
        count += 1
    return count


@main.command()
@click.option('--target-dir', default='docs/project-guide', help='Target directory for the guide')
@click.option('--force', is_flag=True, help='Overwrite existing files')
@click.option(
    '--no-input',
    'no_input',
    is_flag=True,
    default=False,
    help=(
        'Do not read from stdin; use defaults where sensible. Fail loudly '
        'if any prompt has no default. (Also auto-enabled by CI=1 or '
        'non-TTY stdin.)'
    ),
)
@click.option(
    '--test-first',
    'test_first',
    is_flag=True,
    default=False,
    help='Prefer test-driven development; planning modes will suggest code_test_first.',
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    default=False,
    help=(
        'Machine-friendly output: on success, emit nothing to stdout. '
        'Errors and important warnings go to stderr (always shown). '
        'Compose with --no-input for unattended embedding.'
    ),
)
@click.option(
    '--project-name',
    'project_name',
    default=None,
    help=(
        "Project name used in generated artifacts (e.g., stories.md header). "
        "Resolution: CLI flag → PROJECT_GUIDE_PROJECT_NAME env var → "
        "pyproject.toml [project].name → current directory name."
    ),
)
def init(
    target_dir: str,
    force: bool,
    no_input: bool,
    test_first: bool,
    quiet: bool,
    project_name: str | None,
):
    """Initialize project-guide in a new project."""
    config_path = Path(".project-guide.yml")

    # Compute once, up front, as the single source of truth for any prompt
    # or skip-input-suppressed output in this command. P.o consumes it to
    # suppress the "intentionally untracked" stderr notice under --no-input.
    skip_input = should_skip_input(no_input)

    # Resolve test_first via the four-level chain: CLI flag → env var → default.
    # Config is not yet loaded at init time, so the config level is skipped.
    resolved_test_first = _resolve_setting(
        "test_first",
        test_first or None,
        "PROJECT_GUIDE_TEST_FIRST",
        "test_first",
        None,
        False,
    )

    # Resolve project_name with a four-level fallback chain:
    #   CLI flag → PROJECT_GUIDE_PROJECT_NAME env → pyproject.toml → cwd.name.
    # The pyproject and cwd legs sit beyond what _resolve_setting covers (no
    # config at init time) so they are consulted inline.
    pyproject_name = _detect_project_name_from_pyproject()
    resolved_project_name = _resolve_setting(
        "project_name",
        project_name,
        "PROJECT_GUIDE_PROJECT_NAME",
        "project_name",
        None,
        pyproject_name or Path.cwd().name,
    )

    # Idempotency: if the project is already initialized and --force was not
    # given, exit 0 silently with an informational message. This makes
    # `project-guide init` safe to run unattended (e.g., as a pyve post-hook)
    # without aborting on re-run.
    if config_path.exists() and not force:
        if not quiet:
            click.echo(
                f"project-guide already initialized at {target_dir}/ "
                f"(use --force to reinitialize)."
            )
        return

    # --force on an existing config: back up the current .project-guide.yml
    # before we overwrite it. This is the single destructive-overwrite site,
    # so the backup is idempotent (one per refresh) and covers every entry
    # point, not just the schema-mismatch recovery flow.
    config_backup_path: Path | None = None
    if config_path.exists() and force:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        config_backup_path = Path(f"{config_path}.bak.{timestamp}")
        shutil.copy2(config_path, config_backup_path)

    if not quiet:
        click.echo(f"Initializing project-guide v{__version__}...")

    # Copy template tree from package to target
    pkg_template_dir = _get_package_template_dir()
    target_path = Path(target_dir)

    try:
        count = _copy_template_tree(pkg_template_dir, target_path, force=force, quiet=quiet)
    except (OSError, SyncError) as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(2)

    if not quiet:
        click.secho(f"✓ Created {target_dir}/", fg='green')

    # Detect pyve (non-fatal; failure stores None)
    detected_pyve_version: str | None = None
    try:
        pyve_result = subprocess.run(
            ['pyve', '--version'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if pyve_result.returncode == 0:
            detected_pyve_version = pyve_result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        detected_pyve_version = None

    # Load metadata and render go.md
    metadata_file = ".metadata.yml"
    metadata_path = target_path / metadata_file
    output_path = target_path / "go.md"
    try:
        metadata = load_metadata(metadata_path)
        mode = metadata.get_mode("default")
        render_go_project_guide(
            target_path, mode, metadata, output_path,
            test_first=bool(resolved_test_first),
            pyve_installed=detected_pyve_version is not None,
            pyve_version=detected_pyve_version,
        )
        if not quiet:
            click.secho(f"✓ Rendered {output_path} (mode: default)", fg='green')
    except (MetadataError, RenderError) as e:
        click.secho(f"Warning: Could not render go.md: {e}", fg='yellow', err=True)

    # Add rendered output to .gitignore
    _ensure_gitignore_entry(target_dir)

    # Create config file
    config = Config(
        version="2.0",
        installed_version=__version__,
        target_dir=target_dir,
        metadata_file=metadata_file,
        current_mode="default",
        test_first=bool(resolved_test_first),
        pyve_version=detected_pyve_version,
        project_name=str(resolved_project_name),
    )
    config.save(str(config_path))
    if not quiet:
        click.secho(f"✓ Created {config_path}", fg='green')
        click.echo(f"\nSuccessfully initialized {count} files.")

    if config_backup_path is not None:
        click.secho(
            f"Previous config backed up to {config_backup_path}. "
            f"Delete once you've verified the new config.",
            fg='yellow',
            err=True,
        )

    # Story P.o: go.md is intentionally untracked-but-unignored. IDE-integrated
    # LLMs still see it (no gitignore rule), but it stays out of the index so
    # branch switches don't trip on it. Surface the policy at install time so
    # fresh installs don't land in the historical "tracked from accident" state.
    if not quiet and not skip_input:
        click.secho(
            f"Note: {output_path} is intentionally untracked. Do not 'git add' it.",
            fg='yellow',
            err=True,
        )


_GITIGNORE_HEADER = "# project-guide"


def _build_project_guide_block(target_dir: str) -> str:
    """Build the canonical project-guide gitignore block.

    Policy (Story P.d, tightened in P.j, reshaped in P.l): everything under
    ``target_dir`` is gitignored except ``go.md``. ``go.md`` must remain
    tracked because IDE-integrated LLMs (Cursor, parts of the VS Code fork
    ecosystem, several LSP-based search backends) typically hide gitignored
    files from the LLM's @-mention / fuzzy-search view.

    P.l (v2.7.1) abandons the cleaner ``<target>/**`` + ``!<target>/go.md``
    shape because several of those same IDEs implement a subset of
    ``.gitignore`` semantics that does not honor re-include negation —
    they apply the broad ``**`` rule, hide ``go.md``, and defeat the
    visibility constraint the policy is trying to enforce. The new form
    lists every top-level entry under ``target_dir`` explicitly so no
    negation is required. The list is enumerated from the bundled template
    tree at write time, so future additions to the install footprint are
    picked up automatically.

    The trailing ``<target>/**/*.bak.*`` rule defensively ignores backup
    files that ``apply_file_update`` writes next to top-level synced files
    (subdirectory backups are already covered by the per-directory entries).
    """
    pkg_root = _get_package_template_dir()
    entries: list[str] = [_GITIGNORE_HEADER]
    for child in sorted(pkg_root.iterdir(), key=lambda p: p.name):
        if child.name == "go.md":
            continue
        suffix = "/" if child.is_dir() else ""
        entries.append(f"/{target_dir}/{child.name}{suffix}")
    entries.append(f"/{target_dir}/**/*.bak.*")
    return "\n".join(entries) + "\n"


def _is_recognized_block_line(line: str, target_dir: str) -> bool:
    """Return True when ``line`` is one we plausibly wrote in any past version.

    A block whose every non-empty line satisfies this predicate is treated
    as ours and rewritten cleanly to the current canonical form; a block
    containing anything that fails this predicate is left untouched with a
    warning. Recognized forms (newest first):

    - **v2.7.1+ explicit-list form (Story P.l):** any line starting with
      ``/<target>/``. The leading slash anchors at repo root; we never
      write unanchored lines, and there is nothing else we plausibly
      generate under that anchor.
    - **v2.6.1 form (Story P.j):** ``<target>/**`` and ``!<target>/go.md``.
    - **v2.6.0 form (Story P.d):** the v2.6.1 lines plus ``<target>/**/*.bak.*``.
    - **pre-P.d form:** ``<target>/**/*.bak.*`` only.
    - **Legacy variants:** ``<target>/go.md`` (incorrectly gitignored, if
      it ever appeared in the wild).
    """
    if line.startswith(f"/{target_dir}/"):
        return True
    return line in {
        f"{target_dir}/**",
        f"!{target_dir}/go.md",
        f"{target_dir}/**/*.bak.*",
        f"{target_dir}/go.md",
    }


def _ensure_gitignore_entry(target_dir: str) -> None:
    """Add or refresh the project-guide block in .gitignore.

    Idempotent: only rewrites the file when the current block differs from
    the canonical form. Foreign content under a ``# project-guide`` header
    is left alone with a stderr warning so the developer can resolve manually.
    """
    gitignore_path = Path(".gitignore")
    canonical = _build_project_guide_block(target_dir)

    if not gitignore_path.exists():
        gitignore_path.write_text(canonical)
        return

    content = gitignore_path.read_text()
    lines = content.splitlines()

    try:
        header_idx = lines.index(_GITIGNORE_HEADER)
    except ValueError:
        # No prior block — append, separated by a blank line.
        prefix = content
        if prefix and not prefix.endswith("\n"):
            prefix += "\n"
        if prefix and not prefix.endswith("\n\n"):
            prefix += "\n"
        gitignore_path.write_text(prefix + canonical)
        return

    # Extract the block body: lines after the header until a blank line or
    # another comment header. This matches how humans usually delimit
    # gitignore sections.
    block_end = header_idx + 1
    while block_end < len(lines):
        line_stripped = lines[block_end].strip()
        if not line_stripped or line_stripped.startswith("#"):
            break
        block_end += 1

    block_body = [lines[i].strip() for i in range(header_idx + 1, block_end)]
    foreign = [bl for bl in block_body if bl and not _is_recognized_block_line(bl, target_dir)]

    if foreign:
        click.secho(
            f"⚠ Existing `{_GITIGNORE_HEADER}` block in .gitignore contains "
            "unrecognized entries; leaving it untouched. Edit manually to "
            "adopt the new track-only-go.md policy.",
            fg='yellow',
            err=True,
        )
        return

    # All-recognized block: replace cleanly with the canonical form.
    new_block_lines = canonical.rstrip("\n").split("\n")
    new_lines = lines[:header_idx] + new_block_lines + lines[block_end:]
    new_content = "\n".join(new_lines)
    if not new_content.endswith("\n"):
        new_content += "\n"

    if new_content == content:
        return  # already canonical

    gitignore_path.write_text(new_content)


_MODE_CATEGORIES: dict[str, str] = {
    "default": "Getting Started",
    # Project Planning — one-time-per-project work; the four spec documents
    # that establish the project before any code lands.
    "plan_concept": "Project Planning",
    "plan_features": "Project Planning",
    "plan_tech_spec": "Project Planning",
    "plan_stories": "Project Planning",
    # Scaffold — the one-time bridge from Project Planning to Coding.
    "scaffold_project": "Scaffold",
    # Coding — the cycle modes for implementing stories.
    "code_direct": "Coding",
    "code_test_first": "Coding",
    # Debugging — bug-fix cycle.
    "debug": "Debugging",
    # Documentation — README, brand, landing page.
    "document_brand": "Documentation",
    "document_landing": "Documentation",
    # Refactoring — update existing planning / documentation artifacts.
    "refactor_plan": "Refactoring",
    "refactor_document": "Refactoring",
    # Release Planning — repeated per release; phase planning, production
    # phase planning (post-1.0 mandatory), and end-of-phase archive.
    "plan_phase": "Release Planning",
    "plan_production_phase": "Release Planning",
    "archive_stories": "Release Planning",
}

_CATEGORY_ORDER = [
    "Getting Started",
    "Project Planning",
    "Scaffold",
    "Coding",
    "Debugging",
    "Documentation",
    "Refactoring",
    "Release Planning",
    "Other",
]


def _mode_category(mode_name: str) -> str:
    return _MODE_CATEGORIES.get(mode_name, "Other")


def _print_mode_listing(
    modes: list[ModeDefinition], current_mode: str, verbose: bool, numbered: bool
) -> list[ModeDefinition]:
    """Print grouped, annotated mode listing.

    Each mode is marked with → (current), ✓ (prerequisites met), or ✗ (unmet).
    When ``numbered`` is True, a selection number is shown beside each entry.
    Returns the flat ordered list of modes for menu indexing.
    """
    groups: dict[str, list] = {}
    for m in modes:
        groups.setdefault(_mode_category(m.name), []).append(m)

    flat: list = []
    for cat in _CATEGORY_ORDER:
        if cat not in groups:
            continue
        click.secho(f"  {cat}", bold=True)
        for m in groups[cat]:
            flat.append(m)
            n = len(flat)

            missing = [f for f in m.files_exist if not Path(f).exists()]
            available = len(missing) == 0

            if m.name == current_mode:
                marker = click.style("→", fg='cyan', bold=True)
                name_part = click.style(f"{m.name:25}", fg='black', bg='cyan', bold=True)
            elif available:
                marker = click.style("✓", fg='green')
                name_part = click.style(f"{m.name:25}")
            else:
                marker = click.style("✗", fg='yellow')
                name_part = click.style(f"{m.name:25}", dim=True)

            num_str = f"{n:2}  " if numbered else "    "
            info_part = click.style(m.info, dim=True)
            click.echo(f"  {marker} {num_str}{name_part}  {info_part}")

            if verbose and missing:
                for f in missing:
                    click.secho(f"              ✗ {f}", fg='yellow', dim=True)
        click.echo()

    return flat


def _prompt_mode_selection(flat_modes: list[ModeDefinition], max_attempts: int = 3) -> str | None:
    """Prompt the user to select a mode by number.

    Returns the chosen mode name, or None if the user cancelled (empty input).
    Exits with code 1 after ``max_attempts`` invalid entries.
    """
    max_n = len(flat_modes)
    for attempt in range(max_attempts):
        try:
            raw = click.prompt(
                f"Select mode [1-{max_n}, Enter to cancel]",
                default="",
                show_default=False,
                prompt_suffix=": ",
            )
        except (click.Abort, EOFError):
            return None

        if not raw.strip():
            return None

        try:
            selection = int(raw.strip())
            if 1 <= selection <= max_n:
                return flat_modes[selection - 1].name
        except ValueError:
            pass

        remaining = max_attempts - attempt - 1
        if remaining > 0:
            click.secho(
                f"  Invalid selection. Enter a number 1–{max_n}, or press Enter to cancel."
                f" ({remaining} attempt{'s' if remaining != 1 else ''} remaining)",
                fg='yellow',
            )

    click.secho("Too many invalid attempts.", fg='red', err=True)
    sys.exit(1)


def _complete_mode_names(ctx, param, incomplete):
    """Shell completion for mode names. Reads metadata at completion time.

    Returns an empty list on any error so completion never crashes the user's shell.
    """
    try:
        config_path = Path(".project-guide.yml")
        if not config_path.exists():
            return []
        config = Config.load(str(config_path))
        metadata_path = Path(config.target_dir) / config.metadata_file
        metadata = load_metadata(metadata_path)
        return [name for name in metadata.list_mode_names() if name.startswith(incomplete)]
    except Exception:
        return []


@main.command(name="mode")
@click.argument("mode_name", required=False, shell_complete=_complete_mode_names)
@click.option('--verbose', '-v', is_flag=True, help='Show unmet prerequisite files for each mode.')
@click.option(
    '--no-input', 'no_input',
    is_flag=True, default=False,
    help='Skip interactive menu; print annotated list and exit. (Also auto-enabled by CI=1 or non-TTY stdin.)',
)
def set_mode(mode_name: str | None, verbose: bool, no_input: bool):
    """Set or show the active development mode.

    Three invocation paths:

    \b
      project-guide mode <name>     # set the mode and re-render go.md
      project-guide mode --no-input # print the annotated mode list and exit
      project-guide mode            # interactive numbered menu (TTY only)

    Modes are grouped by lifecycle section in the listing: Getting Started,
    Project Planning, Scaffold, Coding, Debugging, Documentation,
    Refactoring, Release Planning. The current mode is marked with → in
    the listing; modes whose prerequisite files exist are marked ✓; modes
    whose prerequisites are unmet are marked ✗.

    Each mode change re-renders `docs/project-guide/go.md` from the
    bundled mode template plus the project's metadata. With --verbose,
    the listing also shows which prerequisite files are missing per mode.

    The --no-input behavior is the discovery / automation path. It is
    auto-enabled when CI=1 is set in the environment or when stdin is
    not a TTY (the embedded-invocation case used by pyve and similar
    wrappers).
    """
    config_path = Path(".project-guide.yml")

    if not config_path.exists():
        click.secho(
            "Error: No .project-guide.yml found. Run 'project-guide init' first.",
            fg='red',
            err=True
        )
        raise click.Abort()

    try:
        config = Config.load(str(config_path))
    except ConfigError as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(3)

    # Load metadata
    metadata_path = Path(config.target_dir) / config.metadata_file
    try:
        metadata = load_metadata(metadata_path)
        _apply_metadata_overrides(metadata, config.metadata_overrides)
    except MetadataError as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(3)

    # No argument: show annotated listing; offer interactive menu on TTY
    if not mode_name:
        skip_input = should_skip_input(no_input)

        click.echo(f"Current mode: {config.current_mode}")
        click.echo()
        flat = _print_mode_listing(
            metadata.modes,
            current_mode=config.current_mode,
            verbose=verbose,
            numbered=not skip_input,
        )

        if skip_input:
            return  # non-interactive: listing only, exit 0

        # Interactive menu
        mode_name = _prompt_mode_selection(flat)
        if mode_name is None:
            return  # user cancelled

    # Validate mode name
    try:
        mode = metadata.get_mode(mode_name)
    except MetadataError:
        click.secho(f"Error: Unknown mode '{mode_name}'.", fg='red', err=True)
        click.echo("Available modes:")
        for m in metadata.modes:
            click.echo(f"  {m.name:25} {m.info}")
        sys.exit(1)

    # Render go.md to target_dir
    target_dir = Path(config.target_dir)
    output_path = target_dir / "go.md"
    try:
        render_go_project_guide(
            target_dir, mode, metadata, output_path,
            test_first=config.test_first,
            pyve_installed=config.pyve_version is not None,
            pyve_version=config.pyve_version,
        )
    except RenderError as e:
        click.secho(f"Error rendering: {e}", fg='red', err=True)
        click.secho("  Run 'project-guide status' to check for missing files.", fg='yellow', err=True)
        click.secho("  Run 'project-guide update' to restore missing templates.", fg='yellow', err=True)
        sys.exit(2)

    # Update config
    config.current_mode = mode.name
    config.save(str(config_path))

    click.secho(f"✓ Mode set: {mode.name}", fg='green')
    click.echo(f"  {mode.info}")
    click.echo(f"  Guide: {output_path}")

    # Show prerequisite warnings
    missing_prereqs = [f for f in mode.files_exist if not Path(f).exists()]
    if missing_prereqs:
        click.echo()
        click.secho("  Prerequisites not yet met:", fg='yellow')
        for f in missing_prereqs:
            click.secho(f"    ✗ {f}", fg='yellow')


@main.command(name="archive-stories")
def archive_stories_cmd():
    """Archive docs/specs/stories.md and re-render a fresh one.

    Wraps the deterministic archive action declared on the `archive_stories`
    mode: moves the current stories.md to
    `<spec_artifacts_path>/.archive/stories-vX.Y.Z.md` (version derived from
    the latest story in the file) and re-renders a fresh stories.md from the
    bundled artifact template, preserving the `## Future` section verbatim.

    This command is intended to be run by the LLM after the developer has
    approved the archive in `project-guide mode archive_stories`.
    """
    config_path = Path(".project-guide.yml")
    if not config_path.exists():
        click.secho(
            "Error: No .project-guide.yml found. Run 'project-guide init' first.",
            fg='red',
            err=True,
        )
        raise click.Abort()

    try:
        config = Config.load(str(config_path))
    except ConfigError as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(3)

    target_dir = Path(config.target_dir)
    metadata_path = target_dir / config.metadata_file
    try:
        metadata = load_metadata(metadata_path)
        _apply_metadata_overrides(metadata, config.metadata_overrides)
        mode = metadata.get_mode("archive_stories")
    except MetadataError as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(3)

    # Find the artifact with action: archive. The schema allows multiple
    # archive artifacts in principle; we only support one for now and error
    # if there are more.
    archive_artifacts = [a for a in mode.artifacts if a.action is ActionType.ARCHIVE]
    if not archive_artifacts:
        click.secho(
            "Error: archive_stories mode has no artifact with action: archive.",
            fg='red',
            err=True,
        )
        sys.exit(3)
    if len(archive_artifacts) > 1:
        click.secho(
            "Error: archive_stories mode declares multiple archive artifacts; "
            "only one is supported.",
            fg='red',
            err=True,
        )
        sys.exit(3)

    artifact = archive_artifacts[0]
    if not artifact.file:
        click.secho(
            "Error: archive_stories artifact must specify a 'file' target.",
            fg='red',
            err=True,
        )
        sys.exit(3)

    source = Path(artifact.file)

    # Drift warning: if the developer renamed the directory without updating
    # the config, the archive still uses the config-persisted project_name.
    # We warn instead of failing — the archive is still correct per the config.
    if config.project_name and Path.cwd().name != config.project_name:
        click.secho(
            f"⚠ cwd name '{Path.cwd().name}' differs from config "
            f"project_name '{config.project_name}' — archive will use the "
            f"config value",
            fg='yellow',
            err=True,
        )

    # Resolve the bundled stories.md artifact template. We deliberately use
    # the package-bundled copy rather than the project's installed template
    # directory so that the archive re-render is not affected by any
    # project-local overrides or modifications.
    template_ref = importlib.resources.files("project_guide.templates").joinpath(
        "project-guide/templates/artifacts/stories.md"
    )
    with importlib.resources.as_file(template_ref) as template_path:
        template = Path(template_path)
        # Merge config.project_name into the context so a fresh stories.md
        # header renders with the project's name even when the old
        # stories.md did not expose it via its own header.
        context = {**dict(metadata.common), "project_name": config.project_name}
        try:
            result = perform_archive(source, template, context)
        except ActionError as e:
            click.secho(f"Error: {e}", fg='red', err=True)
            sys.exit(2)

    click.secho("✓ Archived stories.md", fg='green', bold=True)
    click.echo(f"  From:        {source}")
    click.echo(f"  To:          {result.archived_to}")
    click.echo(f"  Version:     {result.version}")
    click.echo(f"  Last phase:  {result.phase_letter}")
    future_status = "carried from source" if result.future_carried else "template default"
    click.echo(f"  Future:      {future_status}")

    if mode.next_mode:
        click.echo()
        click.secho(
            f"  Next: run `project-guide mode {mode.next_mode}` to plan the next phase.",
            dim=True,
        )


_SEMVER_RE = __import__("re").compile(
    r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$"
)


def _bump_pyproject_version(pyproject_path: Path, new_version: str) -> bool:
    """Update `version = "..."` under `[project]` in pyproject.toml.

    Returns True if the file was changed (or already at the target version).
    Raises FileNotFoundError if the file is missing, or click.ClickException
    if the version line cannot be located.
    """
    import re

    if not pyproject_path.exists():
        raise FileNotFoundError(str(pyproject_path))
    text = pyproject_path.read_text(encoding="utf-8")
    # Match the [project] section, then the first version = "..." line within it.
    # We don't try to parse TOML — the regex preserves formatting exactly.
    pattern = re.compile(
        r'(?ms)^(\[project\][^\[]*?\bversion\s*=\s*)"[^"]+"',
    )
    new_text, n = pattern.subn(rf'\1"{new_version}"', text, count=1)
    if n == 0:
        raise click.ClickException(
            f"Could not locate `version = \"...\"` under `[project]` in {pyproject_path}"
        )
    if new_text != text:
        pyproject_path.write_text(new_text, encoding="utf-8")
    return True


def _find_version_file(project_name: str) -> Path | None:
    """Auto-detect a `__version__ = "..."` source file.

    Tries common locations in order:
      <project_name>/version.py
      <project_name>/_version.py
      <project_name>/__init__.py
      src/<project_name>/version.py
      src/<project_name>/_version.py
      src/<project_name>/__init__.py

    Project names are normalized (replace `-` with `_`). Returns None if
    none of the candidates exist or contain `__version__`.
    """
    import re

    safe = project_name.replace("-", "_")
    candidates = [
        Path(safe) / "version.py",
        Path(safe) / "_version.py",
        Path(safe) / "__init__.py",
        Path("src") / safe / "version.py",
        Path("src") / safe / "_version.py",
        Path("src") / safe / "__init__.py",
    ]
    for candidate in candidates:
        if not candidate.exists():
            continue
        content = candidate.read_text(encoding="utf-8")
        if re.search(r'^__version__\s*=\s*["\'][^"\']+["\']', content, re.MULTILINE):
            return candidate
    return None


def _bump_version_file(version_file: Path, new_version: str) -> bool:
    """Update `__version__ = "..."` in a Python source file.

    Returns True if the file was changed (or already at the target version).
    Raises click.ClickException if `__version__` cannot be located.
    """
    import re

    text = version_file.read_text(encoding="utf-8")
    pattern = re.compile(
        r'^(__version__\s*=\s*)["\'][^"\']+["\']',
        re.MULTILINE,
    )
    new_text, n = pattern.subn(rf'\1"{new_version}"', text, count=1)
    if n == 0:
        raise click.ClickException(
            f"Could not locate `__version__ = \"...\"` in {version_file}"
        )
    if new_text != text:
        version_file.write_text(new_text, encoding="utf-8")
    return True


def _bump_changelog(changelog_path: Path, new_version: str) -> str:
    """Insert a `## [VERSION] - YYYY-MM-DD` heading below `## [Unreleased]`.

    If a section heading for `[VERSION]` already exists, update its date to
    today and leave its body untouched (idempotent on repeated runs).

    Returns one of: "inserted", "updated-date", "no-unreleased-section".
    Raises FileNotFoundError if the file is missing.
    """
    import re

    if not changelog_path.exists():
        raise FileNotFoundError(str(changelog_path))
    text = changelog_path.read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")

    # Idempotent path: section already exists; update its date.
    existing_pattern = re.compile(
        rf'^(## \[{re.escape(new_version)}\])\s*-\s*\d{{4}}-\d{{2}}-\d{{2}}',
        re.MULTILINE,
    )
    new_text, n = existing_pattern.subn(rf"\1 - {today}", text, count=1)
    if n > 0:
        if new_text != text:
            changelog_path.write_text(new_text, encoding="utf-8")
        return "updated-date"

    # Insertion path: place the new section heading below `## [Unreleased]`.
    insert_pattern = re.compile(r'^(## \[Unreleased\][^\n]*\n)', re.MULTILINE)
    insert_match = insert_pattern.search(text)
    if not insert_match:
        return "no-unreleased-section"
    new_section = f"\n## [{new_version}] - {today}\n"
    insertion_idx = insert_match.end()
    new_text = text[:insertion_idx] + new_section + text[insertion_idx:]
    changelog_path.write_text(new_text, encoding="utf-8")
    return "inserted"


@main.command(name="bump-version")
@click.argument("version", required=False)
@click.option(
    '--no-input', 'no_input',
    is_flag=True, default=False,
    help='Skip interactive prompts; fail loudly if defaults are missing. (Also auto-enabled by CI=1 or non-TTY stdin.)',
)
@click.option(
    '--quiet', 'quiet',
    is_flag=True, default=False,
    help='Suppress success-path stdout. Errors and warnings still emit on stderr.',
)
def bump_version(version: str | None, no_input: bool, quiet: bool):
    """Bump the package version in pyproject.toml, version source, and CHANGELOG.md.

    Writes the supplied X.Y.Z to:

    \b
      - pyproject.toml `[project] version` field
      - The package's `__version__` source file (auto-detected from
        `<package>/version.py`, `<package>/_version.py`, `<package>/__init__.py`,
        and the `src/<package>/...` variants)
      - A new `## [VERSION] - YYYY-MM-DD` entry in CHANGELOG.md, inserted
        directly below `## [Unreleased]`. Idempotent if the section already
        exists (date is updated, body is preserved).

    Use this at end-of-phase when shipping a bundled release per the
    Version Cadence rule documented in `docs/specs/stories.md` (added in
    Story O.o, v2.5.13). The version magnitude (patch / minor / major) is
    determined by the cadence rule and `plan_production_phase`'s
    breaking-change negotiation; this command is purely the mechanical
    write.
    """
    skip_input = should_skip_input(no_input)

    # Resolve the version arg per the --no-input contract: if missing under
    # --no-input, fail loud with the canonical error message.
    if version is None:
        if skip_input:
            click.secho(
                "Error: bump-version requires a VERSION argument when "
                "--no-input is set (or stdin is non-TTY). "
                "Pass the target version as a positional, e.g. "
                "`project-guide bump-version 1.0.0`.",
                fg='red',
                err=True,
            )
            sys.exit(2)
        version = click.prompt("Target version (X.Y.Z)", type=str).strip()

    if not _SEMVER_RE.match(version):
        click.secho(
            f"Error: '{version}' is not a valid semver string "
            "(expected X.Y.Z, optionally with -prerelease or +build).",
            fg='red',
            err=True,
        )
        sys.exit(2)

    # Resolve project name for version-file auto-detection.
    config_path = Path(".project-guide.yml")
    project_name: str | None = None
    if config_path.exists():
        try:
            config = Config.load(str(config_path))
            project_name = config.project_name
        except ConfigError:
            pass
    if project_name is None:
        project_name = _detect_project_name_from_pyproject() or Path.cwd().name

    pyproject_path = Path("pyproject.toml")
    changelog_path = Path("CHANGELOG.md")

    # Update pyproject.toml (required).
    try:
        _bump_pyproject_version(pyproject_path, version)
    except FileNotFoundError:
        click.secho(
            f"Error: {pyproject_path} not found. bump-version requires a "
            "Python pyproject.toml in the current directory.",
            fg='red',
            err=True,
        )
        sys.exit(2)
    except click.ClickException as e:
        click.secho(f"Error: {e.message}", fg='red', err=True)
        sys.exit(2)

    # Update version source file (auto-detected; warn but don't fail if missing).
    version_file = _find_version_file(project_name)
    if version_file is not None:
        try:
            _bump_version_file(version_file, version)
        except click.ClickException as e:
            click.secho(f"Error: {e.message}", fg='red', err=True)
            sys.exit(2)
    else:
        click.secho(
            f"⚠ No __version__ source file auto-detected for project "
            f"'{project_name}'. Skipped version-file update; pyproject.toml "
            "and CHANGELOG.md updated. If your project keeps __version__ in "
            "a non-standard location, edit it manually.",
            fg='yellow',
            err=True,
        )

    # Update CHANGELOG.md (required).
    try:
        result = _bump_changelog(changelog_path, version)
    except FileNotFoundError:
        click.secho(
            f"Error: {changelog_path} not found. bump-version requires a "
            "CHANGELOG.md in the current directory.",
            fg='red',
            err=True,
        )
        sys.exit(2)

    if result == "no-unreleased-section":
        click.secho(
            f"⚠ {changelog_path} has no `## [Unreleased]` section. "
            f"pyproject.toml and version source updated, but no changelog "
            f"entry was added. Add a `## [{version}] - <date>` heading "
            "manually, or seed `## [Unreleased]` and re-run.",
            fg='yellow',
            err=True,
        )

    # Quiet mode: suppress success-path stdout. Errors and warnings (above)
    # already emit to stderr regardless.
    if not quiet:
        click.secho(f"✓ Bumped version to {version}", fg='green', bold=True)
        click.echo(f"  pyproject.toml: {pyproject_path}")
        if version_file is not None:
            click.echo(f"  __version__:    {version_file}")
        if result == "inserted":
            click.echo(f"  CHANGELOG.md:   inserted ## [{version}]")
        elif result == "updated-date":
            click.echo(f"  CHANGELOG.md:   updated date on existing ## [{version}]")


@main.command()
@click.option('--verbose', '-v', is_flag=True, help='Show full per-file list')
def status(verbose):
    """Show project-guide status."""
    config_path = Path(".project-guide.yml")

    # Check if config exists
    if not config_path.exists():
        click.secho(
            "Error: No .project-guide.yml found. Run 'project-guide init' first.",
            fg='red',
            err=True
        )
        raise click.Abort()

    # Load config
    try:
        config = Config.load(str(config_path))
    except ConfigError as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(3)  # Configuration error exit code

    # Show v1.x migration notice if applicable. The version-based detection
    # is handled upstream by SchemaVersionError in Config.load; the target_dir
    # legacy path remains reachable for configs that never changed their layout.
    if config.target_dir == "docs/guides":
        click.secho("Migration notice (v1.x → v2.x):", fg='yellow', bold=True)
        click.secho("  docs/guides/ is deprecated; new features target docs/project-guide/ only.", fg='yellow')
        click.secho("  Run 'project-guide init' to install the v2.x template system.", fg='yellow')
        click.secho("  Use 'project-guide mode refactor_plan' to migrate concept, features, tech-spec.", fg='yellow')
        click.secho("  Use 'project-guide mode refactor_document' to migrate descriptions, landing page, MkDocs.", fg='yellow')
        click.echo()

    # --- Header ---
    target_dir = Path(config.target_dir)
    click.secho(f"project-guide v{__version__}", bold=True)
    if config.installed_version and config.installed_version != __version__:
        click.secho(f"  installed: v{config.installed_version}", fg='yellow')

    # --- Mode section ---
    click.echo()
    metadata_path = target_dir / config.metadata_file
    spec_artifacts_path = "docs/specs"  # default; overridden by metadata if available
    try:
        metadata = load_metadata(metadata_path)
        _apply_metadata_overrides(metadata, config.metadata_overrides)
        spec_artifacts_path = metadata.common.get('spec_artifacts_path', spec_artifacts_path)
        mode = metadata.get_mode(config.current_mode)
        click.echo(
            click.style("Mode: ", bold=True)
            + click.style(mode.name, fg='cyan', bold=True)
            + click.style(f" — {mode.info}", dim=True)
        )

        # Prerequisites — only show when the mode has them
        if mode.files_exist:
            missing_prereqs = [f for f in mode.files_exist if not Path(f).exists()]
            if missing_prereqs:
                met = [f for f in mode.files_exist if Path(f).exists()]
                click.secho("  Prerequisites:", fg='yellow')
                for f in met:
                    click.secho(f"    ✓ {f}", fg='green')
                for f in missing_prereqs:
                    click.secho(f"    ✗ {f}", fg='red')
            else:
                click.echo("  Prerequisites: " + click.style("all met", fg='green'))
    except (MetadataError, FileNotFoundError):
        click.echo(click.style("Mode: ", bold=True) + config.current_mode)
    click.secho("  Run 'project-guide mode' to see available modes.", dim=True)

    # --- Guide section ---
    click.echo()
    guide_path = str(target_dir / 'go.md')
    click.echo(
        click.style("Guide: ", bold=True)
        + click.style(guide_path, fg='cyan')
    )
    click.secho(f"  Tell your LLM: Read {guide_path}", dim=True)

    # --- Stories section ---
    stories = _read_stories_summary(spec_artifacts_path)
    if stories is not None:
        click.echo()
        summary_line = (
            f"{stories.total} total"
            f" — {stories.done} done"
            f", {stories.in_progress} in progress"
            f", {stories.planned} planned"
        )
        click.echo(click.style("Stories: ", bold=True) + summary_line)
        if stories.next_story:
            click.secho(f"  Next: {stories.next_story}", dim=True)
        if verbose and stories.phases:
            for phase in stories.phases:
                click.secho(
                    f"  Phase {phase.letter}: {phase.name}"
                    f"  ({phase.done}/{phase.total} done)",
                    dim=True,
                )

    # --- Files section ---
    click.echo()
    all_files = get_all_file_names()

    current_count = 0
    overridden_count = 0
    needs_update_count = 0
    missing_count = 0
    problem_lines: list[tuple[str, str, str]] = []  # (file_name, detail, color)

    for file_name in all_files:
        target_file = target_dir / file_name

        if config.is_overridden(file_name):
            overridden_count += 1
            override = config.overrides[file_name]
            problem_lines.append((
                file_name,
                f"(overridden: \"{override.reason}\")",
                "yellow",
            ))
        elif not target_file.exists():
            missing_count += 1
            problem_lines.append((file_name, "(missing)", "red"))
        elif file_matches_template(target_file, file_name):
            current_count += 1
        else:
            needs_update_count += 1
            problem_lines.append((file_name, "(needs updating)", "yellow"))

    # Build colored summary parts
    parts = []
    if current_count > 0:
        parts.append(click.style(f"{current_count} current", fg='green'))
    if needs_update_count > 0:
        parts.append(click.style(f"{needs_update_count} need updating", fg='yellow'))
    if missing_count > 0:
        parts.append(click.style(f"{missing_count} missing", fg='red'))
    if overridden_count > 0:
        parts.append(click.style(f"{overridden_count} overridden", fg='yellow'))

    summary = ", ".join(parts) if parts else "no tracked files"

    click.echo(click.style("Files: ", bold=True) + summary)
    if problem_lines:
        if verbose:
            for file_name, detail, color in problem_lines:
                click.secho(f"  ✗ {file_name:40} {detail}", fg=color)
        click.secho("  Run 'project-guide update' to sync.", dim=True)
    elif verbose:
        for file_name in all_files:
            click.secho(f"  ✓ {file_name}", fg='green')

    # --- Pyve-managed-hosting footer (Story Q.m) ---
    # Reads the cached detection from config; no runtime re-run of `pyve
    # --version` (cross-repo invariant (b) in project-essentials.md).
    if config.pyve_version is not None:
        click.echo()
        click.secho(
            f"Managed by pyve v{_pyve_version_token(config.pyve_version)} "
            "(detected at init time).",
            dim=True,
        )


@main.command()
@click.option('--files', multiple=True, help='Specific files to update')
@click.option('--dry-run', is_flag=True, help='Show what would be updated without applying')
@click.option('--force', is_flag=True, help='Update even overridden files (creates backups)')
@click.option(
    '--no-input',
    'no_input',
    is_flag=True,
    default=False,
    help=(
        'Do not read from stdin; apply safe defaults. '
        '(Also auto-enabled by CI=1 or non-TTY stdin.)'
    ),
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    default=False,
    help=(
        'Machine-friendly output: on success, emit nothing to stdout. '
        'Errors and important warnings go to stderr (always shown). '
        'Compose with --no-input for unattended embedding.'
    ),
)
def update(files: tuple, dry_run: bool, force: bool, no_input: bool, quiet: bool):
    """Update files to latest version."""
    skip_input = should_skip_input(no_input)  # noqa: F841  (reserved for future prompts)

    config_path = Path(".project-guide.yml")

    # Check if config exists
    if not config_path.exists():
        click.secho(
            "Error: No .project-guide.yml found. Run 'project-guide init' first.",
            fg='red',
            err=True
        )
        raise click.Abort()

    # Load config. SchemaVersionError is handled specially: on an "older"
    # mismatch we direct the user at init --force (which backs up the existing
    # config at the destructive overwrite site); on a "newer" mismatch we
    # tell the user to upgrade the package.
    try:
        config = Config.load(str(config_path))
    except SchemaVersionError as e:
        if e.direction == "older":
            click.secho(f"Schema mismatch: {e}", fg='red', err=True)
            click.secho(
                "Run 'project-guide init --force' to refresh "
                "(your existing .project-guide.yml will be backed up).",
                fg='yellow',
                err=True,
            )
        else:
            click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(1)
    except ConfigError as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(3)  # Configuration error exit code

    # Convert files tuple to list or None
    files_list = list(files) if files else None

    # Validate specific files if provided
    if files_list:
        all_files = get_all_file_names()
        for f in files_list:
            if f not in all_files:
                click.secho(
                    f"Error: File '{f}' not found.",
                    fg='red',
                    err=True
                )
                click.echo(f"Available files: {', '.join(all_files)}", err=True)
                sys.exit(1)  # General error exit code

    # Run sync
    if dry_run and not quiet:
        click.echo("Dry-run mode: showing what would be updated...")
        click.echo()

    try:
        updated, skipped, current, missing = sync_files(config, files_list, force, dry_run)
    except SyncError as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(2)  # File I/O error exit code

    # Print results (per-file lines suppressed when --quiet)
    if not quiet:
        if updated:
            action = "Would update (backed up)" if dry_run else "Updated (backed up)"
            click.secho(f"{action}:", fg='green')
            for f in updated:
                click.secho(f"  ✓ {f}", fg='green')

        if missing:
            action = "Would create" if dry_run else "Created"
            click.secho(f"{action} (missing files):", fg='cyan')
            for f in missing:
                click.secho(f"  + {f}", fg='cyan')

        if current:
            click.echo("Already current:")
            for f in current:
                click.echo(f"  • {f}")

    # Overridden-file warnings (stderr — visible even when --quiet silences stdout)
    if skipped:
        click.secho("Skipped (overridden):", fg='yellow', err=True)
        for f in skipped:
            override = config.overrides[f]
            click.secho(f"  ⊘ {f} - {override.reason}", fg='yellow', err=True)

    # Update config if not dry-run and any updates were made
    all_updated = updated + missing
    if not dry_run and all_updated:
        config.installed_version = __version__
        config.save(str(config_path))

    # Re-render go.md if any templates were updated OR if go.md is missing.
    # go.md is rendered output, not a tracked file, so deleting it must still
    # cause update to restore it even when no templates changed this run.
    target_dir_path = Path(config.target_dir)
    output_path = target_dir_path / "go.md"
    template_files = [f for f in all_updated if f.startswith("templates/")]
    if not dry_run and (template_files or not output_path.exists()):
        metadata_path = target_dir_path / config.metadata_file
        try:
            metadata = load_metadata(metadata_path)
            _apply_metadata_overrides(metadata, config.metadata_overrides)
            mode = metadata.get_mode(config.current_mode)
            render_go_project_guide(
                target_dir_path, mode, metadata, output_path,
                test_first=config.test_first,
                pyve_installed=config.pyve_version is not None,
                pyve_version=config.pyve_version,
            )
            if not quiet:
                click.secho("✓ Re-rendered go.md", fg='green')
        except (MetadataError, RenderError) as e:
            click.secho(f"Warning: Could not re-render go.md: {e}", fg='yellow', err=True)

    # An effectively no-op run where every available file is locked by an override.
    blocked_by_overrides = bool(skipped) and not (current or updated or missing)

    # Summary: stdout when interactive, suppressed under --quiet except for the
    # override-blocked hint, which surfaces on stderr so embedders still learn
    # why nothing changed.
    if not quiet:
        click.echo()
        if dry_run:
            total_changes = len(updated) + len(missing)
            if total_changes > 0:
                parts = []
                if updated:
                    parts.append(f"update {len(updated)}")
                if missing:
                    parts.append(f"create {len(missing)}")
                click.echo(f"Would {', '.join(parts)}.")
                click.echo("Run without --dry-run to apply changes.")
            elif blocked_by_overrides:
                click.echo("All files are overridden. Use --force to update anyway.")
            else:
                click.echo("No updates needed.")
        else:
            total_changes = len(updated) + len(missing)
            if total_changes > 0:
                parts = []
                if updated:
                    parts.append(f"updated {len(updated)}")
                if missing:
                    parts.append(f"created {len(missing)}")
                click.secho(
                    f"✓ Successfully {' and '.join(parts)} file{'s' if total_changes != 1 else ''}.",
                    fg='green',
                )
            elif blocked_by_overrides:
                click.echo("All files are overridden. Use --force to update anyway.")
            else:
                click.echo("All files are up to date.")
    elif blocked_by_overrides:
        click.echo(
            "All files are overridden. Use --force to update anyway.",
            err=True,
        )


def _apply_heal(config: Config, config_path: Path) -> None:
    """Apply pending template syncs and re-render go.md.

    Sets the recursion guard env var before doing any writes so nested
    subprocess invocations do not re-enter the hook. Raises ``SyncError``
    on I/O failure; ``MetadataError`` and ``RenderError`` from the re-render
    step are caught and surfaced as a stderr warning (the heal itself
    succeeded; only the cosmetic re-render failed).
    """
    os.environ[_HEAL_GUARD_ENV] = "1"

    applied_updated, _skipped, _current, applied_missing = sync_files(config)

    if applied_updated or applied_missing:
        config.installed_version = __version__
        config.save(str(config_path))

    target_dir_path = Path(config.target_dir)
    output_path = target_dir_path / "go.md"
    metadata_path = target_dir_path / config.metadata_file
    try:
        metadata = load_metadata(metadata_path)
        _apply_metadata_overrides(metadata, config.metadata_overrides)
        mode = metadata.get_mode(config.current_mode)
        render_go_project_guide(
            target_dir_path, mode, metadata, output_path,
            test_first=config.test_first,
            pyve_installed=config.pyve_version is not None,
            pyve_version=config.pyve_version,
        )
    except (MetadataError, RenderError) as e:
        click.secho(f"Warning: Could not re-render go.md: {e}", fg='yellow', err=True)


def _warn_if_go_md_tracked(config: Config) -> None:
    """Warn (stderr, non-fatal) when ``<target_dir>/go.md`` is tracked in git.

    Story P.o reframes ``go.md`` as untracked-but-unignored: IDE-integrated
    LLMs still see it (because it's not gitignored), but it stays out of the
    consumer's index so branch switches and merges don't trip over it.
    Consumers upgrading from v2.6.x–v2.7.x have it tracked from historical
    accident; the warning surfaces the issue with a copyable migration
    command and the consumer decides when to apply it. The command is never
    auto-run from inside ``project-guide`` — same wrapper-initiates-git-ops
    constraint that bounded the P.k ``git-push`` wrapper.

    Silent when ``go.md`` is untracked (the steady state), when the cwd is
    not a git repository, under the recursion guard env var, under
    ``--no-input``, or when ``git`` is unavailable.
    """
    if os.environ.get(_HEAL_GUARD_ENV) == "1":
        return
    if should_skip_input():
        return

    go_md_path = f"{config.target_dir}/go.md"
    try:
        repo_check = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return
    if repo_check.returncode != 0:
        return

    try:
        ls_files = subprocess.run(
            ["git", "ls-files", "--error-unmatch", go_md_path],
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return
    if ls_files.returncode != 0:
        return

    click.secho(
        f"Warning: {go_md_path} is tracked. The current policy is "
        "untracked-by-default — run "
        f"`git rm --cached {go_md_path} && git commit` once to migrate.",
        fg='yellow',
        err=True,
    )


def _pyve_version_token(pyve_version: str) -> str:
    """Extract the bare version number from the cached ``pyve_version`` string.

    ``pyve_version`` stores the raw ``pyve --version`` stdout (e.g.
    ``"pyve version 2.6.2"``). Return the first whitespace-separated token that
    starts with a digit (``"2.6.2"``); fall back to the whole string when no
    such token exists, so callers always get something printable.
    """
    for token in pyve_version.split():
        if token and token[0].isdigit():
            return token
    return pyve_version


def _running_install_path() -> Path:
    """Filesystem location of the running ``project_guide`` package.

    Factored out as a tiny helper so tests can monkeypatch it to simulate a
    project-local install without standing up a real venv.
    """
    return Path(__file__).resolve().parent


def _warn_if_local_install_under_pyve(config: Config) -> None:
    """Warn (stderr, non-fatal) when a project-local install coexists with pyve.

    Story Q.m: under pyve's toolchain-venv hosting (Pyve Story N.aw) pyve
    manages a single global project-guide install. If a project also carries a
    *local* pip install (e.g. under ``<cwd>/.venv/`` or
    ``<cwd>/.pyve/envs/<name>/``), ``which project-guide`` resolves to whichever
    is first on ``PATH`` and behavior diverges silently with version drift. The
    warning surfaces the footgun with a copyable ``pip uninstall`` command; the
    user removes it on their own schedule — never auto-run, same
    wrapper-initiates-side-effects discipline as the P.o ``go.md`` warning.

    Detection: the running package lives under ``Path.cwd()`` **and** inside a
    ``site-packages`` directory (a real installed copy). The ``site-packages``
    guard deliberately excludes an editable source checkout (whose ``__file__``
    is the source tree directly under cwd, as in project-guide's own dogfood
    repo) — that is a development setup, not the footgun this warns about.

    Silent when pyve was not detected at init time, when no qualifying local
    install is present (the steady state), under the recursion guard env var,
    or under ``--no-input`` / CI / non-TTY stdin — mirroring
    :func:`_warn_if_go_md_tracked`.
    """
    if os.environ.get(_HEAL_GUARD_ENV) == "1":
        return
    if should_skip_input():
        return
    if config.pyve_version is None:
        return

    install_path = _running_install_path()
    cwd = Path.cwd().resolve()
    if not install_path.is_relative_to(cwd):
        return
    if "site-packages" not in install_path.parts:
        return  # editable source checkout, not a pip-installed local copy

    click.secho(
        f"⚠ Local project-guide install detected at {install_path}.\n"
        "  Pyve is configured to manage project-guide globally.\n"
        "  Remove the local install with: pip uninstall project-guide",
        fg='yellow',
        err=True,
    )


def _run_pre_invoke_hook() -> None:
    """Group-level hook: heal first, then let the requested subcommand run.

    Silent in the steady state. Only prompts when there is actual drift.
    Declining the prompt is not a blocker — the original subcommand still
    runs (refusing the heal is the user's choice).

    Inherits the ``--no-input`` contract via :func:`should_skip_input`: under
    skip-input mode (``PROJECT_GUIDE_NO_INPUT``, ``CI=1``, or non-TTY stdin)
    the prompt is replaced with auto-yes plus a one-line stderr notice. The
    hook cannot see a per-subcommand ``--no-input`` flag (subcommand args
    have not been parsed yet), so it relies on the env / TTY signals.

    Skipped entirely when:
      - The recursion guard env var is set (a parent invocation already healed).
      - ``.project-guide.yml`` is absent (let ``init`` bootstrap; ``heal``
        would error otherwise, and that error belongs to the subcommand).
      - The config fails to load (schema mismatch, parse error) — the
        subcommand will surface the error with its own guidance.
      - ``sync_files`` raises ``SyncError`` — same reasoning.
    """
    if os.environ.get(_HEAL_GUARD_ENV) == "1":
        return

    config_path = Path(".project-guide.yml")
    if not config_path.exists():
        return

    try:
        config = Config.load(str(config_path))
    except (SchemaVersionError, ConfigError):
        return

    _warn_if_go_md_tracked(config)
    _warn_if_local_install_under_pyve(config)

    try:
        updated, _skipped, _current, missing = sync_files(config, dry_run=True)
    except SyncError:
        return

    drift_count = len(updated) + len(missing)
    if drift_count == 0:
        return  # silent steady state

    plural = "s" if drift_count != 1 else ""

    if should_skip_input():
        click.secho(
            f"Auto-healing {drift_count} template{plural} under --no-input.",
            err=True,
        )
    else:
        click.secho(
            f"{drift_count} template{plural} missing or stale.",
            err=True,
        )
        if not click.confirm("Update?", default=True):
            return  # decline does not block the subcommand

    try:
        _apply_heal(config, config_path)
    except SyncError as e:
        click.secho(f"Warning: heal failed: {e}", fg='yellow', err=True)


@main.command()
@click.option(
    '--no-input',
    'no_input',
    is_flag=True,
    default=False,
    help=(
        'Do not read from stdin; replace the [Y/n] prompt with auto-yes when '
        'drift is detected, and emit a one-line stderr notice. '
        '(Also auto-enabled by PROJECT_GUIDE_NO_INPUT, CI=1, or non-TTY stdin.)'
    ),
)
def heal(no_input: bool):
    """Repair the install: create missing templates and refresh stale ones.

    Detects drift between the installed template tree and the bundled package
    templates. Silent when there is nothing to do (exit 0, no stdout). When
    drift is detected, prints a one-line summary to stderr and prompts to
    apply the fix; declining exits 1 without writing.

    Under --no-input (or PROJECT_GUIDE_NO_INPUT / CI=1 / non-TTY stdin) the
    prompt is replaced with auto-yes and the summary becomes a non-suppressible
    stderr notice (`Auto-healing N templates under --no-input.`) so CI logs
    and embedding callers have a visible signal of the writes.

    Missing `.project-guide.yml` is a hard error — `heal` cannot bootstrap a
    project that has never been initialized; run `project-guide init` first.
    """
    skip_input = should_skip_input(no_input)
    config_path = Path(".project-guide.yml")

    if not config_path.exists():
        click.secho(
            "Missing .project-guide.yml — run 'project-guide init' to bootstrap the project.",
            fg='red',
            err=True,
        )
        sys.exit(1)

    # Mirror update's SchemaVersionError handling so the recovery guidance is
    # identical regardless of which entry point hit the mismatch.
    try:
        config = Config.load(str(config_path))
    except SchemaVersionError as e:
        if e.direction == "older":
            click.secho(f"Schema mismatch: {e}", fg='red', err=True)
            click.secho(
                "Run 'project-guide init --force' to refresh "
                "(your existing .project-guide.yml will be backed up).",
                fg='yellow',
                err=True,
            )
        else:
            click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(1)
    except ConfigError as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(3)

    _warn_if_go_md_tracked(config)
    _warn_if_local_install_under_pyve(config)

    # Drift detection via dry-run sync; overrides are intentionally not drift.
    try:
        updated, _skipped, _current, missing = sync_files(config, dry_run=True)
    except SyncError as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(2)

    drift_count = len(updated) + len(missing)
    if drift_count == 0:
        return  # silent success — required for the auto-hook

    plural = "s" if drift_count != 1 else ""

    if skip_input:
        click.secho(
            f"Auto-healing {drift_count} template{plural} under --no-input.",
            err=True,
        )
    else:
        click.secho(
            f"{drift_count} template{plural} missing or stale.",
            err=True,
        )
        if not click.confirm("Update?", default=True):
            sys.exit(1)

    try:
        _apply_heal(config, config_path)
    except SyncError as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(2)


def _get_committed_story_ids() -> tuple[set[str], dict[str, list[str]]]:
    """Scan git log and return committed story IDs plus a duplicates map.

    Runs ``git log --pretty=%s`` and parses each subject via
    :func:`parse_committed_ids_from_subject` (Story P.u), which recognizes
    single-story subjects, the legacy ``Story <id>:`` form (P.s), and
    bundled subjects like ``H.a, H.b, H.c InputSource ...`` or
    ``H.a: v0.10.0, H.b: v0.11.0 sample ...``.

    Returns ``(committed_ids, duplicates)`` where:

    - ``committed_ids`` is the set of every bare story ID that appeared in
      at least one commit subject.
    - ``duplicates`` maps each ID seen in 2+ subjects to the ordered list of
      offending subject lines, used by ``git-push``'s duplicate-warning
      prompt. Empty when no IDs repeat.

    Returns ``(set(), {})`` when git is unavailable, the cwd is not a git
    repository, or the repo has no commits — the wrapper treats all of those
    as "nothing committed yet" rather than erroring on its own.
    """
    try:
        result = subprocess.run(
            ["git", "log", "--pretty=%s"],
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return set(), {}

    if result.returncode != 0:
        return set(), {}

    occurrences: dict[str, list[str]] = {}
    for line in result.stdout.splitlines():
        for sid in parse_committed_ids_from_subject(line):
            occurrences.setdefault(sid, []).append(line)

    committed = set(occurrences.keys())
    duplicates = {sid: subs for sid, subs in occurrences.items() if len(subs) > 1}
    return committed, duplicates


def _resolve_spec_artifacts_path() -> str:
    """Resolve the spec artifacts directory (where stories.md lives).

    Prefers the project-guide metadata's ``common.spec_artifacts_path`` when
    config + metadata both load cleanly; falls back to the conventional
    ``docs/specs`` so the wrapper still works in projects that have not yet
    run ``project-guide init`` (or in this project itself before metadata
    is rendered).
    """
    default = "docs/specs"
    config_path = Path(".project-guide.yml")
    if not config_path.exists():
        return default
    try:
        config = Config.load(str(config_path))
        metadata_path = Path(config.target_dir) / config.metadata_file
        metadata = load_metadata(metadata_path)
        _apply_metadata_overrides(metadata, config.metadata_overrides)
        return metadata.common.get("spec_artifacts_path", default)
    except (ConfigError, SchemaVersionError, MetadataError, FileNotFoundError):
        return default


@main.command(name="git-push")
@click.argument("branch_name", required=False)
@click.option(
    '--no-input',
    'no_input',
    is_flag=True,
    default=False,
    help=(
        'Do not read from stdin; auto-decline both the duplicate-story-ID '
        'warning and the bundle-offer prompt (so CI never silently bundles '
        'or papers over a history anomaly). Also auto-enabled by CI=1 or '
        'non-TTY stdin.'
    ),
)
def git_push(branch_name: str | None, no_input: bool):
    """Wrap gitbetter's `git-push` with the most-recently-completed story ID.

    \b
    Derives the commit message from `[Done]` story headings in
    `docs/specs/stories.md`, verifies the stories have not already been
    committed, then shells out to gitbetter's `git-push` to perform the
    actual push. Optional `BRANCH_NAME` passes through to gitbetter for
    branch-aware push flows.

    \b
    [Done] stories whose body contains no `- [ ]` / `- [x]` checklist items
    are treated as decorative group-overview headers (Story P.v) and filtered
    out of the uncommitted-detection flow — headers do not produce commits.

    \b
    Single uncommitted [Done] story: derives `<id>: <title>` and pushes.
    Multiple uncommitted [Done] stories: proposes a bundled subject
    `<id1>[: <ver1>], <id2>[: <ver2>], ... <title1> + <title2> + ...`
    and asks `[Y/n]`. Decline → exit 1 with the manual-resolution hint.

    \b
    Out-of-sequence detection (Story P.v): if an uncommitted [Done] story
    precedes a committed [Done] story in stories.md document order, the
    wrapper exits 1 with a message naming every offender. This is an
    unambiguous error path; --no-input does not auto-yes it.

    \b
    Exit 0 (success):
      - Push completed successfully
      - Nothing real to commit — every commit-worthy [Done] story is in git log
        (Story P.v; previously exit 1)

    \b
    Hard errors (exit 1):
      - No `[Done]` story in stories.md
      - Out-of-sequence [Done] stories detected (Story P.v)
      - Multiple uncommitted `[Done]` stories and bundle offer declined
        (or --no-input)
      - Duplicate story ID found in git log and continuation declined
        (or --no-input)
      - `git-push` not on PATH (install gitbetter:
        `brew install pointmatic/tap/gitbetter`)

    \b
    Heading-to-message transformation (single story):
      Input:  ### Story G.a: v1.2.3 New command `foo` with "Hello" [Done]
      Output: G.a: v1.2.3 New command 'foo' with 'Hello'
    Backticks and double quotes become single quotes; single quotes pass
    through; the colon after the story ID is preserved.

    This is a developer-lane convenience command. The LLM still does not
    initiate commits — the approval-gate discipline rule remains in force.
    """
    skip_input = should_skip_input(no_input)
    spec_artifacts_path = _resolve_spec_artifacts_path()
    done_stories = _read_done_stories(spec_artifacts_path)
    stories_md_display = f"{spec_artifacts_path}/stories.md"

    if done_stories is None:
        click.secho(
            f"Error: {stories_md_display} not found.",
            fg='red',
            err=True,
        )
        sys.exit(1)

    if not done_stories:
        click.secho(
            f"No completed story found in {stories_md_display}.",
            fg='red',
            err=True,
        )
        sys.exit(1)

    committed, duplicates = _get_committed_story_ids()

    if duplicates and not _prompt_continue_on_duplicate_ids(duplicates, skip_input):
        sys.exit(1)

    # P.v: filter header stories (zero-checklist body) out of the commit-units
    # set. Headers are decorative groupings of sub-numbered children and never
    # produce a commit on their own.
    commit_units = [s for s in done_stories if not s.is_header]
    headers = [s for s in done_stories if s.is_header]

    # P.v: out-of-sequence detection on the post-filter commit-units list.
    # The committed prefix → uncommitted suffix invariant must hold; any
    # uncommitted story that precedes a committed story in document order is
    # an unambiguous error (no prompt, ignores --no-input).
    offenders = _check_out_of_sequence(commit_units, committed)
    if offenders:
        _emit_out_of_sequence_error(offenders, commit_units, committed)
        sys.exit(1)

    uncommitted = [s for s in commit_units if s.story_id not in committed]

    if not uncommitted:
        # P.v: nothing real to commit. Exit 0 — the repo is in the desired
        # state. The "no [Done] story at all" path (caught above) keeps its
        # exit-1 stories.md-authoring-problem semantics.
        last = commit_units[-1] if commit_units else None
        if last is not None:
            click.echo(
                "Nothing to commit — every real [Done] story is already in git log.",
                err=True,
            )
            if headers:
                header_ids = ", ".join(h.story_id for h in headers)
                click.echo(
                    f"([Done] header{'s' if len(headers) > 1 else ''} present "
                    f"with no commit obligation: {header_ids}.)",
                    err=True,
                )
        else:
            click.echo(
                "Nothing to commit — only [Done] header stories present.",
                err=True,
            )
        sys.exit(0)

    if len(uncommitted) > 1:
        message = derive_bundle_commit_message(uncommitted)
        if not _prompt_use_bundle_message(message, skip_input):
            ids = ", ".join(s.story_id for s in uncommitted)
            click.secho(
                f"Multiple uncommitted [Done] stories: {ids}. "
                f"Use 'git-push' directly to commit them one at a time with explicit messages.",
                fg='red',
                err=True,
            )
            sys.exit(1)
    else:
        message = derive_commit_message(uncommitted[0])

    git_push_path = shutil.which("git-push")
    if git_push_path is None:
        click.secho(
            "git-push not found on PATH. "
            "Install gitbetter: brew install pointmatic/tap/gitbetter",
            fg='red',
            err=True,
        )
        sys.exit(1)

    argv = [git_push_path, message]
    if branch_name:
        argv.append(branch_name)

    # No capture_output: gitbetter is fully interactive — let it inherit
    # stdin/stdout/stderr. Propagate its exit code unchanged so the reject
    # / recovery menu's real semantics reach the developer.
    result = subprocess.run(argv, check=False)
    sys.exit(result.returncode)


def _prompt_continue_on_duplicate_ids(
    duplicates: dict[str, list[str]],
    skip_input: bool,
) -> bool:
    """Warn about duplicate story IDs in git log; return True to proceed.

    Always emits the warning to stderr (the anomaly is worth surfacing even
    in non-interactive flows). Under ``skip_input`` the prompt is replaced
    with auto-no and we return ``False`` so CI never papers over real
    history irregularities. Interactive default is ``Y``.
    """
    click.secho(
        "Warning: duplicate story ID(s) found in git log:",
        fg='yellow',
        err=True,
    )
    for sid, subjects in sorted(duplicates.items()):
        click.secho(f"  {sid}:", fg='yellow', err=True)
        for subject in subjects:
            click.secho(f"    - {subject}", fg='yellow', err=True)

    if skip_input:
        click.secho(
            "Aborting under --no-input. Re-run interactively to confirm.",
            fg='red',
            err=True,
        )
        return False

    return click.confirm("Continue?", default=True, err=True)


def _prompt_use_bundle_message(message: str, skip_input: bool) -> bool:
    """Propose the bundled commit subject; return True to accept.

    Under ``skip_input`` returns ``False`` (no prompt) so the caller falls
    through to the existing "use git-push directly" error path — bundling
    changes the *shape* of the commit and is a developer decision, not a
    CI default.
    """
    if skip_input:
        return False

    click.echo("Proposed bundled commit subject:", err=True)
    click.echo(f"  {message}", err=True)
    return click.confirm("Use this message?", default=True, err=True)


def _check_out_of_sequence(
    commit_units: list,
    committed: set[str],
) -> list[tuple[str, list[str]]]:
    """Return out-of-sequence offenders as ``[(offender_id, [later_committed_ids]), ...]``.

    Operates on the post-header-filter ``[Done]`` story list in document
    order. The invariant: committed-prefix → uncommitted-suffix. An
    uncommitted story whose index is less than the index of the last
    committed story is out-of-sequence; for each such offender, the
    returned list of ``later_committed_ids`` names the committed stories
    that prove the gap.

    Returns an empty list when the partition is clean.
    """
    last_committed_idx = -1
    for i, s in enumerate(commit_units):
        if s.story_id in committed:
            last_committed_idx = i
    if last_committed_idx < 0:
        return []

    offenders: list[tuple[str, list[str]]] = []
    for i, s in enumerate(commit_units):
        if i >= last_committed_idx:
            break
        if s.story_id in committed:
            continue
        later_committed = [
            commit_units[j].story_id
            for j in range(i + 1, len(commit_units))
            if commit_units[j].story_id in committed
        ]
        offenders.append((s.story_id, later_committed))
    return offenders


def _emit_out_of_sequence_error(
    offenders: list[tuple[str, list[str]]],
    commit_units: list,
    committed: set[str],
) -> None:
    """Print the out-of-sequence error block to stderr.

    Lists every offender with its later-committed context, plus the
    uncommitted stories that *would* be eligible for normal flow once the
    out-of-sequence ones are resolved (full picture for the developer).
    """
    click.secho(
        "Out-of-sequence [Done] stories detected:",
        fg='red',
        err=True,
    )
    for offender_id, later_committed in offenders:
        click.secho(
            f"  {offender_id} is uncommitted, but later stories are already committed:",
            fg='red',
            err=True,
        )
        for lid in later_committed:
            click.secho(f"    - {lid}", fg='red', err=True)

    offender_ids = {oid for oid, _ in offenders}
    eligible_tail = [
        s.story_id
        for s in commit_units
        if s.story_id not in committed and s.story_id not in offender_ids
    ]
    if eligible_tail:
        click.echo("", err=True)
        click.secho(
            "Uncommitted [Done] stories in proper sequence (eligible for normal "
            "flow once the above are resolved):",
            fg='yellow',
            err=True,
        )
        for sid in eligible_tail:
            click.secho(f"  - {sid}", fg='yellow', err=True)

    click.echo("", err=True)
    click.secho(
        "Commit out-of-sequence stories manually with raw git-push, or "
        "investigate the history gap.",
        fg='red',
        err=True,
    )


@main.command()
@click.argument('file_name')
@click.argument('reason')
def override(file_name: str, reason: str):
    """Mark a file as overridden to prevent updates."""
    config_path = Path(".project-guide.yml")

    # Check if config exists
    if not config_path.exists():
        click.secho(
            "Error: No .project-guide.yml found. Run 'project-guide init' first.",
            fg='red',
            err=True
        )
        raise click.Abort()

    # Load config
    try:
        config = Config.load(str(config_path))
    except ConfigError as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(3)  # Configuration error exit code

    # Verify file exists
    all_files = get_all_file_names()
    if file_name not in all_files:
        click.secho(
            f"Error: File '{file_name}' not found.",
            fg='red',
            err=True
        )
        click.echo(f"Available files: {', '.join(all_files)}", err=True)
        sys.exit(1)  # General error exit code

    # Add override
    config.add_override(file_name, reason, config.installed_version or __version__)
    config.save(str(config_path))

    click.secho(f"✓ Marked {file_name} as overridden", fg='green')
    click.echo(f"  Reason: {reason}")


@main.command()
@click.argument('file_name')
def unoverride(file_name: str):
    """Remove override status from a file."""
    config_path = Path(".project-guide.yml")

    # Check if config exists
    if not config_path.exists():
        click.secho(
            "Error: No .project-guide.yml found. Run 'project-guide init' first.",
            fg='red',
            err=True
        )
        raise click.Abort()

    # Load config
    try:
        config = Config.load(str(config_path))
    except ConfigError as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(3)  # Configuration error exit code

    # Check if file is overridden
    if not config.is_overridden(file_name):
        click.secho(
            f"Error: File '{file_name}' is not overridden.",
            fg='red',
            err=True
        )
        raise click.Abort()

    # Remove override
    config.remove_override(file_name)
    config.save(str(config_path))

    click.secho(f"✓ Removed override from {file_name}", fg='green')


@main.command()
def overrides():
    """List all overridden files."""
    try:
        config = Config.load()
    except ConfigError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(3)

    if not config.overrides:
        click.secho("No overridden files.", fg="yellow")
        return

    click.secho("Overridden files:\n", fg="cyan", bold=True)

    for file_name, override in config.overrides.items():
        click.secho(f"{file_name}", fg="yellow", bold=True)
        click.secho(f"  Reason: {override.reason}", fg="white")
        click.secho(f"  Since: v{override.locked_version}", fg="white")
        click.secho(f"  Last updated: {override.last_updated}", fg="white")
        click.echo()


@main.command()
@click.option(
    "--force",
    is_flag=True,
    help="Skip confirmation prompt",
)
@click.option(
    '--no-input',
    'no_input',
    is_flag=True,
    default=False,
    help=(
        'Do not read from stdin; proceed without confirming. '
        '(Also auto-enabled by CI=1 or non-TTY stdin.)'
    ),
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    default=False,
    help=(
        'Machine-friendly output: on success, emit nothing to stdout. '
        'Errors and important warnings go to stderr (always shown). '
        'Compose with --no-input for unattended embedding.'
    ),
)
def purge(force, no_input, quiet):
    """Remove all project-guide files from the current project."""
    skip_input = should_skip_input(no_input)

    try:
        config = Config.load()
    except ConfigError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(3)

    config_path = Path(".project-guide.yml")
    target_dir = Path(config.target_dir)

    # Show what will be removed (suppressed when --quiet)
    if not quiet:
        click.secho("The following will be removed:", fg="yellow", bold=True)
        click.echo(f"  • {config_path}")
        click.echo(f"  • {target_dir}/ (and all contents)")
        click.echo()

    # Confirm unless --force or non-interactive mode
    if not force and not skip_input:
        click.confirm(
            click.style("Are you sure you want to purge project-guide?", fg="red", bold=True),
            abort=True
        )

    # Remove target directory
    try:
        if target_dir.exists():
            import shutil
            shutil.rmtree(target_dir)
            if not quiet:
                click.secho(f"✓ Removed {target_dir}/", fg="green")
        else:
            click.secho(f"  {target_dir}/ not found (skipped)", fg="yellow", err=True)
    except OSError as e:
        click.secho(f"Error removing {target_dir}/: {e}", fg="red", err=True)
        sys.exit(2)

    # Remove config file
    try:
        if config_path.exists():
            config_path.unlink()
            if not quiet:
                click.secho(f"✓ Removed {config_path}", fg="green")
        else:
            click.secho(f"  {config_path} not found (skipped)", fg="yellow", err=True)
    except OSError as e:
        click.secho(f"Error removing {config_path}: {e}", fg="red", err=True)
        sys.exit(2)

    if not quiet:
        click.echo()
        click.secho("project-guide has been purged from this project.", fg="green", bold=True)


if __name__ == "__main__":
    main()
