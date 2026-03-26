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

import sys
from pathlib import Path

import click

from project_guides.config import Config
from project_guides.exceptions import ConfigError, SyncError
from project_guides.sync import (
    apply_guide_update,
    compare_versions,
    copy_guide,
    get_all_guide_names,
    sync_guides,
)
from project_guides.version import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """Manage LLM project guides across repositories."""
    pass


@main.command()
@click.option('--target-dir', default='docs/guides', help='Target directory for guides')
@click.option('--force', is_flag=True, help='Overwrite existing files')
def init(target_dir: str, force: bool):
    """Initialize guides in a new project."""
    config_path = Path(".project-guides.yml")

    # Check if config already exists
    if config_path.exists() and not force:
        click.secho(
            f"Error: {config_path} already exists. Use --force to overwrite.",
            fg='red',
            err=True
        )
        raise click.Abort()

    # Create target directory
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    # Get all guide names
    guide_names = get_all_guide_names()

    # Copy all templates
    click.echo(f"Initializing project-guides v{__version__}...")
    click.secho(f"✓ Created {target_dir}/", fg='green')

    for guide_name in guide_names:
        try:
            copy_guide(guide_name, target_path, force=force)
            click.secho(f"✓ Installed {guide_name}", fg='green')
        except FileExistsError:
            if not force:
                click.secho(f"⚠ Skipped {guide_name} (already exists)", fg='yellow')
        except SyncError as e:
            click.secho(f"Error: {e}", fg='red', err=True)
            sys.exit(2)  # File I/O error exit code

    # Create config file
    config = Config(
        version="1.0",
        installed_version=__version__,
        target_dir=target_dir
    )
    config.save(str(config_path))
    click.secho(f"✓ Created {config_path}", fg='green')

    click.echo(f"\nSuccessfully initialized {len(guide_names)} guides.")


@main.command()
def status():
    """Show status of all guides."""
    config_path = Path(".project-guides.yml")

    # Check if config exists
    if not config_path.exists():
        click.secho(
            "Error: No .project-guides.yml found. Run 'project-guides init' first.",
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

    # Show version info
    package_version = __version__
    click.echo(f"project-guides v{package_version} (installed: v{config.installed_version})")
    click.echo()

    # Check each guide's status
    guide_names = get_all_guide_names()
    target_dir = Path(config.target_dir)

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
            from project_guides.sync import file_matches_template
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
            click.echo("Run 'project-guides update' to sync.")
    else:
        click.secho("All guides are up to date.", fg='green')


@main.command()
@click.option('--guides', multiple=True, help='Specific guides to update')
@click.option('--dry-run', is_flag=True, help='Show what would be updated without applying')
@click.option('--force', is_flag=True, help='Update even overridden guides (creates backups)')
def update(guides: tuple, dry_run: bool, force: bool):
    """Update guides to latest version."""
    config_path = Path(".project-guides.yml")

    # Check if config exists
    if not config_path.exists():
        click.secho(
            "Error: No .project-guides.yml found. Run 'project-guides init' first.",
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
    user_approved = []
    user_declined = []
    user_backed_up = []

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
    config_path = Path(".project-guides.yml")

    # Check if config exists
    if not config_path.exists():
        click.secho(
            "Error: No .project-guides.yml found. Run 'project-guides init' first.",
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
    config_path = Path(".project-guides.yml")

    # Check if config exists
    if not config_path.exists():
        click.secho(
            "Error: No .project-guides.yml found. Run 'project-guides init' first.",
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
    """Remove all project-guides files from the current project."""
    try:
        config = Config.load()
    except ConfigError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(3)

    config_path = Path(".project-guides.yml")
    guides_dir = Path(config.target_dir)

    # Show what will be removed
    click.secho("The following will be removed:", fg="yellow", bold=True)
    click.echo(f"  • {config_path}")
    click.echo(f"  • {guides_dir}/ (and all contents)")
    click.echo()

    # Confirm unless --force
    if not force:
        click.confirm(
            click.style("Are you sure you want to purge project-guides?", fg="red", bold=True),
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
    click.secho("project-guides has been purged from this project.", fg="green", bold=True)


if __name__ == "__main__":
    main()
