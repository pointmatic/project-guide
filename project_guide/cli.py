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
import shutil
import subprocess
import sys
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
from project_guide.runtime import _resolve_setting, should_skip_input
from project_guide.stories import _read_stories_summary
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


@click.group()
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
    help='Suppress per-file progress output; errors and summary are always shown.',
)
def init(target_dir: str, force: bool, no_input: bool, test_first: bool, quiet: bool):
    """Initialize project-guide in a new project."""
    config_path = Path(".project-guide.yml")

    # Compute once, up front, so any future prompt site in this command has
    # a single source of truth. Today `init` has no interactive prompts, so
    # this value is plumbed through but not consulted — that's intentional:
    # the contract needs to exist *before* the first prompt is added.
    skip_input = should_skip_input(no_input)  # noqa: F841  (reserved for future prompts)

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

    # Idempotency: if the project is already initialized and --force was not
    # given, exit 0 silently with an informational message. This makes
    # `project-guide init` safe to run unattended (e.g., as a pyve post-hook)
    # without aborting on re-run.
    if config_path.exists() and not force:
        click.echo(
            f"project-guide already initialized at {target_dir}/ "
            f"(use --force to reinitialize)."
        )
        return

    click.echo(f"Initializing project-guide v{__version__}...")

    # Copy template tree from package to target
    pkg_template_dir = _get_package_template_dir()
    target_path = Path(target_dir)

    try:
        count = _copy_template_tree(pkg_template_dir, target_path, force=force, quiet=quiet)
    except (OSError, SyncError) as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(2)

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
        click.secho(f"✓ Rendered {output_path} (mode: default)", fg='green')
    except (MetadataError, RenderError) as e:
        click.secho(f"Warning: Could not render go.md: {e}", fg='yellow')

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
    )
    config.save(str(config_path))
    click.secho(f"✓ Created {config_path}", fg='green')

    click.echo(f"\nSuccessfully initialized {count} files.")


def _ensure_gitignore_entry(target_dir: str) -> None:
    """Add project-guide entries to .gitignore if not already present."""
    gitignore_path = Path(".gitignore")
    entries = [
        f"{target_dir}/**/*.bak.*",
    ]

    if gitignore_path.exists():
        content = gitignore_path.read_text()
        missing = [e for e in entries if e not in content]
        if not missing:
            return
        if not content.endswith("\n"):
            content += "\n"
        content += "\n# project-guide\n"
        for entry in missing:
            content += f"{entry}\n"
        gitignore_path.write_text(content)
    else:
        lines = "# project-guide\n"
        for entry in entries:
            lines += f"{entry}\n"
        gitignore_path.write_text(lines)


_MODE_CATEGORIES: dict[str, str] = {
    "default": "Getting Started",
    "plan_concept": "Planning",
    "plan_features": "Planning",
    "plan_tech_spec": "Planning",
    "plan_stories": "Planning",
    "archive_stories": "Post-Release",
    "plan_phase": "Post-Release",
    "scaffold_project": "Scaffold",
    "document_brand": "Documentation",
    "document_landing": "Documentation",
    "code_direct": "Coding",
    "code_test_first": "Coding",
    "debug": "Debugging",
    "refactor_plan": "Refactoring",
    "refactor_document": "Refactoring",
}

_CATEGORY_ORDER = [
    "Getting Started",
    "Planning",
    "Coding",
    "Post-Release",
    "Scaffold",
    "Documentation",
    "Debugging",
    "Refactoring",
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
    """Set or show the active development mode."""
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

    # Resolve the bundled stories.md artifact template. We deliberately use
    # the package-bundled copy rather than the project's installed template
    # directory so that the archive re-render is not affected by any
    # project-local overrides or modifications.
    template_ref = importlib.resources.files("project_guide.templates").joinpath(
        "project-guide/templates/artifacts/stories.md"
    )
    with importlib.resources.as_file(template_ref) as template_path:
        template = Path(template_path)
        try:
            result = perform_archive(source, template, dict(metadata.common))
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
    help='Suppress per-file progress output; errors and summary are always shown.',
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
    # mismatch we back up the stale config and point the user at init --force;
    # on a "newer" mismatch we tell the user to upgrade the package.
    try:
        config = Config.load(str(config_path))
    except SchemaVersionError as e:
        if e.direction == "older":
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_path = Path(f"{config_path}.bak.{timestamp}")
            shutil.copy2(config_path, backup_path)
            click.secho(f"Schema mismatch: {e}", fg='red', err=True)
            click.secho(f"Config backed up to {backup_path}.", fg='yellow', err=True)
            click.secho(
                f"Run 'project-guide init --force' to refresh, then manually merge "
                f"customizations from {backup_path}.",
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
                click.echo(f"Available files: {', '.join(all_files)}")
                sys.exit(1)  # General error exit code

    # Run sync
    if dry_run:
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

    # Overridden-file warnings are always shown (explicit warnings, never suppressed)
    if skipped:
        click.secho("Skipped (overridden):", fg='yellow')
        for f in skipped:
            override = config.overrides[f]
            click.secho(f"  ⊘ {f} - {override.reason}", fg='yellow')

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
            click.secho("✓ Re-rendered go.md", fg='green')
        except (MetadataError, RenderError) as e:
            click.secho(f"Warning: Could not re-render go.md: {e}", fg='yellow')

    # Print summary
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
            click.secho(f"✓ Successfully {' and '.join(parts)} file{'s' if total_changes != 1 else ''}.", fg='green')
        elif skipped and not current:
            click.echo("All files are overridden. Use --force to update anyway.")
        else:
            click.echo("All files are up to date.")


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
        click.echo(f"Available files: {', '.join(all_files)}")
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
    help='Suppress per-file progress output; errors and summary are always shown.',
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
            click.secho(f"  {target_dir}/ not found (skipped)", fg="yellow")
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
            click.secho(f"  {config_path} not found (skipped)", fg="yellow")
    except OSError as e:
        click.secho(f"Error removing {config_path}: {e}", fg="red", err=True)
        sys.exit(2)

    click.echo()
    click.secho("project-guide has been purged from this project.", fg="green", bold=True)


if __name__ == "__main__":
    main()
