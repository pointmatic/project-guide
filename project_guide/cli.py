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
import sys
from pathlib import Path

import click

from project_guide.config import Config
from project_guide.exceptions import ConfigError, MetadataError, RenderError, SyncError
from project_guide.metadata import load_metadata
from project_guide.render import render_go_project_guide
from project_guide.sync import (
    apply_guide_update,
    compare_versions,
    get_all_guide_names,
    sync_guides,
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
    """Manage LLM project guides across repositories."""
    _migrate_config_if_needed()


def _get_package_template_dir() -> Path:
    """Get the path to the bundled project-guide templates in the package."""
    with importlib.resources.as_file(
        importlib.resources.files("project_guide.templates").joinpath("project-guide")
    ) as path:
        return Path(path)


def _copy_template_tree(src_dir: Path, dest_dir: Path, force: bool = False) -> int:
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
            click.secho(f"⚠ Skipped {rel_path} (already exists)", fg='yellow')
            continue

        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        click.secho(f"✓ Installed {rel_path}", fg='green')
        count += 1
    return count


@main.command()
@click.option('--target-dir', default='docs/project-guide', help='Target directory for guides')
@click.option('--force', is_flag=True, help='Overwrite existing files')
def init(target_dir: str, force: bool):
    """Initialize project-guide in a new project."""
    config_path = Path(".project-guide.yml")

    # Check if config already exists
    if config_path.exists() and not force:
        click.secho(
            f"Error: {config_path} already exists. Use --force to overwrite.",
            fg='red',
            err=True
        )
        raise click.Abort()

    click.echo(f"Initializing project-guide v{__version__}...")

    # Copy template tree from package to target
    pkg_template_dir = _get_package_template_dir()
    target_path = Path(target_dir)

    try:
        count = _copy_template_tree(pkg_template_dir, target_path, force=force)
    except (OSError, SyncError) as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(2)

    click.secho(f"✓ Created {target_dir}/", fg='green')

    # Load metadata and render go-project-guide.md
    metadata_file = ".metadata.yml"
    metadata_path = target_path / metadata_file
    output_path = target_path / "go-project-guide.md"
    try:
        metadata = load_metadata(metadata_path)
        mode = metadata.get_mode("default")
        render_go_project_guide(target_path, mode, metadata, output_path)
        click.secho(f"✓ Rendered {output_path} (mode: default)", fg='green')
    except (MetadataError, RenderError) as e:
        click.secho(f"Warning: Could not render go-project-guide.md: {e}", fg='yellow')

    # Add rendered output to .gitignore
    _ensure_gitignore_entry(target_dir)

    # Create config file
    config = Config(
        version="2.0",
        installed_version=__version__,
        target_dir=target_dir,
        metadata_file=metadata_file,
        current_mode="default",
    )
    config.save(str(config_path))
    click.secho(f"✓ Created {config_path}", fg='green')

    click.echo(f"\nSuccessfully initialized {count} files.")


def _ensure_gitignore_entry(target_dir: str) -> None:
    """Add go-project-guide.md to .gitignore if not already present."""
    gitignore_path = Path(".gitignore")
    entry = f"{target_dir}/go-project-guide.md"

    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if entry in content:
            return
        if not content.endswith("\n"):
            content += "\n"
        content += f"{entry}\n"
        gitignore_path.write_text(content)
    else:
        gitignore_path.write_text(f"{entry}\n")


@main.command(name="mode")
@click.argument("mode_name", required=False)
def set_mode(mode_name: str | None):
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
    except MetadataError as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(3)

    # No argument: show current mode and list available modes
    if not mode_name:
        click.echo(f"Current mode: {config.current_mode}")
        click.echo()
        click.echo("Available modes:")
        for m in metadata.modes:
            marker = "→" if m.name == config.current_mode else " "
            click.echo(f"  {marker} {m.name:25} {m.info}")
        return

    # Validate mode name
    try:
        mode = metadata.get_mode(mode_name)
    except MetadataError:
        click.secho(f"Error: Unknown mode '{mode_name}'.", fg='red', err=True)
        click.echo("Available modes:")
        for m in metadata.modes:
            click.echo(f"  {m.name:25} {m.info}")
        sys.exit(1)

    # Render go-project-guide.md to target_dir
    target_dir = Path(config.target_dir)
    output_path = target_dir / "go-project-guide.md"
    try:
        render_go_project_guide(target_dir, mode, metadata, output_path)
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


@main.command()
def status():
    """Show status of all guides."""
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

    # Show v1.x migration notice if applicable
    if config.version == "1.0" or config.target_dir == "docs/guides":
        click.secho("Migration notice (v1.x → v2.x):", fg='yellow', bold=True)
        click.secho("  docs/guides/ is deprecated; new features target docs/project-guide/ only.", fg='yellow')
        click.secho("  Run 'project-guide init' to install the v2.x template system.", fg='yellow')
        click.secho("  Use 'project-guide mode refactor_plan' to migrate concept, features, tech-spec.", fg='yellow')
        click.secho("  Use 'project-guide mode refactor_document' to migrate descriptions, landing page, MkDocs.", fg='yellow')
        click.echo()

    # Show version info
    package_version = __version__
    click.echo(f"project-guide v{package_version} (installed: v{config.installed_version})")
    click.echo()

    # Show mode info
    target_dir = Path(config.target_dir)
    metadata_path = target_dir / config.metadata_file
    try:
        metadata = load_metadata(metadata_path)
        mode = metadata.get_mode(config.current_mode)
        click.echo(f"Mode:  {mode.name}")
        click.echo(f"       {mode.info}")
        click.echo(f"Guide: {target_dir / 'go-project-guide.md'}")

        # Show prerequisite status
        if mode.files_exist:
            met = [f for f in mode.files_exist if Path(f).exists()]
            missing_prereqs = [f for f in mode.files_exist if not Path(f).exists()]
            if missing_prereqs:
                click.echo()
                click.secho("Prerequisites:", fg='yellow')
                for f in met:
                    click.secho(f"  ✓ {f}", fg='green')
                for f in missing_prereqs:
                    click.secho(f"  ✗ {f}", fg='yellow')
            else:
                click.echo()
                click.secho("Prerequisites: all met", fg='green')
    except (MetadataError, FileNotFoundError):
        click.echo(f"Mode:  {config.current_mode}")

    click.echo()

    # Check each guide's status
    guide_names = get_all_guide_names()

    current_count = 0
    outdated_count = 0
    overridden_count = 0
    missing_count = 0

    click.echo("Guides status:")
    for guide_name in guide_names:
        target_file = target_dir / guide_name

        # Check if overridden
        if config.is_overridden(guide_name):
            override = config.overrides[guide_name]
            click.secho(
                f"  ⊘ {guide_name:40} v{override.locked_version}  (overridden: \"{override.reason}\")",
                fg='yellow'
            )
            overridden_count += 1
        # Check if file exists
        elif not target_file.exists():
            click.secho(f"  ✗ {guide_name:40} (missing)", fg='red')
            missing_count += 1
        # Check if current version and content matches
        elif config.installed_version and compare_versions(config.installed_version, package_version) == 0:
            # Version is current - check if content matches template
            from project_guide.sync import file_matches_template
            if file_matches_template(target_file, guide_name):
                click.secho(f"  ✓ {guide_name:40} v{package_version}  (current)", fg='green')
                current_count += 1
            else:
                click.secho(
                    f"  ⚠ {guide_name:40} v{package_version}  (modified)",
                    fg='yellow'
                )
                outdated_count += 1
        # Must be outdated version
        else:
            click.secho(
                f"  ⚠ {guide_name:40} v{config.installed_version}  (update available)",
                fg='yellow'
            )
            outdated_count += 1

    # Show summary
    click.echo()
    summary_parts = []
    if overridden_count > 0:
        summary_parts.append(f"{overridden_count} guide{'s' if overridden_count != 1 else ''} overridden")
    if outdated_count > 0:
        summary_parts.append(f"{outdated_count} update{'s' if outdated_count != 1 else ''} available")
    if missing_count > 0:
        summary_parts.append(f"{missing_count} guide{'s' if missing_count != 1 else ''} missing")

    if summary_parts:
        click.echo(", ".join(summary_parts).capitalize())
        if outdated_count > 0 or missing_count > 0:
            click.echo("Run 'project-guide update' to sync.")
    else:
        click.secho("All guides are up to date.", fg='green')


@main.command()
@click.option('--guides', multiple=True, help='Specific guides to update')
@click.option('--dry-run', is_flag=True, help='Show what would be updated without applying')
@click.option('--force', is_flag=True, help='Update even overridden guides (creates backups)')
def update(guides: tuple, dry_run: bool, force: bool):
    """Update guides to latest version."""
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

    # Convert guides tuple to list or None
    guides_list = list(guides) if guides else None

    # Validate specific guides if provided
    if guides_list:
        all_guides = get_all_guide_names()
        for guide in guides_list:
            if guide not in all_guides:
                click.secho(
                    f"Error: Guide '{guide}' not found.",
                    fg='red',
                    err=True
                )
                click.echo(f"Available guides: {', '.join(all_guides)}")
                sys.exit(1)  # General error exit code

    # Run sync
    if dry_run:
        click.echo("Dry-run mode: showing what would be updated...")
        click.echo()

    try:
        updated, skipped, current, missing, modified = sync_guides(config, guides_list, force, dry_run)
    except SyncError as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        sys.exit(2)  # File I/O error exit code

    # Handle modified files - prompt user for each one
    user_approved: list[str] = []
    user_declined: list[str] = []
    user_backed_up: list[str] = []

    if modified and not dry_run:
        click.secho("Modified files detected:", fg='yellow')
        for guide in modified:
            click.secho(f"  ⚠ {guide} has been modified locally.", fg='yellow')
            if click.confirm(f"    Backup and overwrite {guide}?", default=False):
                try:
                    apply_guide_update(guide, config, make_backup=True)
                    user_approved.append(guide)
                except SyncError as e:
                    click.secho(f"  Error updating {guide}: {e}", fg='red', err=True)
            else:
                user_declined.append(guide)
    elif modified and dry_run:
        click.secho("Modified (would prompt: backup and overwrite?):", fg='yellow')
        for guide in modified:
            click.secho(f"  ⚠ {guide}", fg='yellow')

    # Print other results
    if updated:
        action = "Would update (backed up)" if (dry_run and force) else ("Updated (backed up)" if force else ("Would update" if dry_run else "Updated"))
        click.secho(f"{action}:", fg='green')
        for guide in updated:
            click.secho(f"  ✓ {guide}", fg='green')

    if user_approved:
        click.secho("Updated (approved by user):", fg='green')
        for guide in user_approved:
            click.secho(f"  ✓ {guide}", fg='green')

    if missing:
        action = "Would create" if dry_run else "Created"
        click.secho(f"{action} (missing files):", fg='cyan')
        for guide in missing:
            click.secho(f"  + {guide}", fg='cyan')

    if user_declined:
        click.secho("Skipped (user declined):", fg='yellow')
        for guide in user_declined:
            click.secho(f"  ⊘ {guide}", fg='yellow')

    if skipped:
        click.secho("Skipped (overridden):", fg='yellow')
        for guide in skipped:
            override = config.overrides[guide]
            click.secho(f"  ⊘ {guide} - {override.reason}", fg='yellow')

    if current:
        click.echo("Already current:")
        for guide in current:
            click.echo(f"  • {guide}")

    # Update config if not dry-run and any updates were made
    all_updated = updated + user_approved + missing
    if not dry_run and all_updated:
        config.installed_version = __version__
        config.save(str(config_path))

        # Re-render go-project-guide.md if any mode templates or headers were updated
        template_files = [f for f in all_updated if f.startswith("templates/")]
        if template_files:
            target_dir = Path(config.target_dir)
            metadata_path = target_dir / config.metadata_file
            try:
                metadata = load_metadata(metadata_path)
                mode = metadata.get_mode(config.current_mode)
                output_path = target_dir / "go-project-guide.md"
                render_go_project_guide(target_dir, mode, metadata, output_path)
                click.secho("✓ Re-rendered go-project-guide.md", fg='green')
            except (MetadataError, RenderError) as e:
                click.secho(f"Warning: Could not re-render go-project-guide.md: {e}", fg='yellow')

    # Print summary
    click.echo()
    if dry_run:
        total_changes = len(updated) + len(missing)
        if total_changes > 0 or modified:
            parts = []
            if updated:
                parts.append(f"update {len(updated)}")
            if missing:
                parts.append(f"create {len(missing)}")
            if modified:
                parts.append(f"prompt for {len(modified)} modified")
            click.echo(f"Would {', '.join(parts)}.")
            click.echo("Run without --dry-run to apply changes.")
        else:
            click.echo("No updates needed.")
    else:
        total_changes = len(updated) + len(user_approved) + len(missing)
        if total_changes > 0:
            parts = []
            if updated + user_approved:
                n = len(updated) + len(user_approved)
                parts.append(f"updated {n}")
            if missing:
                parts.append(f"created {len(missing)}")
            click.secho(f"✓ Successfully {' and '.join(parts)} guide{'s' if total_changes != 1 else ''}.", fg='green')
            if user_backed_up:
                click.echo(f"  {len(user_backed_up)} backup(s) created.")
        elif user_declined and not skipped and not current:
            click.echo("No guides updated (all modifications declined).")
        elif skipped and not current and not user_declined:
            click.echo("All guides are overridden. Use --force to update anyway.")
        else:
            click.echo("All guides are up to date.")


@main.command()
@click.argument('guide_name')
@click.argument('reason')
def override(guide_name: str, reason: str):
    """Mark a guide as overridden to prevent updates."""
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

    # Verify guide exists
    all_guides = get_all_guide_names()
    if guide_name not in all_guides:
        click.secho(
            f"Error: Guide '{guide_name}' not found.",
            fg='red',
            err=True
        )
        click.echo(f"Available guides: {', '.join(all_guides)}")
        sys.exit(1)  # General error exit code

    # Add override
    config.add_override(guide_name, reason, config.installed_version or __version__)
    config.save(str(config_path))

    click.secho(f"✓ Marked {guide_name} as overridden", fg='green')
    click.echo(f"  Reason: {reason}")


@main.command()
@click.argument('guide_name')
def unoverride(guide_name: str):
    """Remove override status from a guide."""
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

    # Check if guide is overridden
    if not config.is_overridden(guide_name):
        click.secho(
            f"Error: Guide '{guide_name}' is not overridden.",
            fg='red',
            err=True
        )
        raise click.Abort()

    # Remove override
    config.remove_override(guide_name)
    config.save(str(config_path))

    click.secho(f"✓ Removed override from {guide_name}", fg='green')


@main.command()
def overrides():
    """List all overridden guides."""
    try:
        config = Config.load()
    except ConfigError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(3)

    if not config.overrides:
        click.secho("No overridden guides.", fg="yellow")
        return

    click.secho("Overridden guides:\n", fg="cyan", bold=True)

    for guide_name, override in config.overrides.items():
        click.secho(f"{guide_name}", fg="yellow", bold=True)
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
def purge(force):
    """Remove all project-guide files from the current project."""
    try:
        config = Config.load()
    except ConfigError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(3)

    config_path = Path(".project-guide.yml")
    guides_dir = Path(config.target_dir)

    # Show what will be removed
    click.secho("The following will be removed:", fg="yellow", bold=True)
    click.echo(f"  • {config_path}")
    click.echo(f"  • {guides_dir}/ (and all contents)")
    click.echo()

    # Confirm unless --force
    if not force:
        click.confirm(
            click.style("Are you sure you want to purge project-guide?", fg="red", bold=True),
            abort=True
        )

    # Remove guides directory
    try:
        if guides_dir.exists():
            import shutil
            shutil.rmtree(guides_dir)
            click.secho(f"✓ Removed {guides_dir}/", fg="green")
        else:
            click.secho(f"  {guides_dir}/ not found (skipped)", fg="yellow")
    except OSError as e:
        click.secho(f"Error removing {guides_dir}/: {e}", fg="red", err=True)
        sys.exit(2)

    # Remove config file
    try:
        if config_path.exists():
            config_path.unlink()
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
