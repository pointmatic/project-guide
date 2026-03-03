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

from pathlib import Path
import sys

import click

from project_guides.version import __version__
from project_guides.config import Config
from project_guides.sync import get_all_guide_names, copy_guide, compare_versions, sync_guides
from project_guides.exceptions import ConfigError, SyncError, GuideNotFoundError


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
        # Check if current version
        elif config.installed_version and compare_versions(config.installed_version, package_version) == 0:
            click.secho(f"  ✓ {guide_name:40} v{package_version}  (current)", fg='green')
            current_count += 1
        # Must be outdated
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
    
    updated, skipped, current = sync_guides(config, guides_list, force, dry_run)
    
    # Print results
    if updated:
        action = "Would update" if dry_run else "Updated"
        click.secho(f"{action}:", fg='green')
        for guide in updated:
            click.secho(f"  ✓ {guide}", fg='green')
    
    if skipped:
        click.secho("Skipped (overridden):", fg='yellow')
        for guide in skipped:
            override = config.overrides[guide]
            click.secho(f"  ⊘ {guide} - {override.reason}", fg='yellow')
    
    if current:
        click.echo("Already current:")
        for guide in current:
            click.echo(f"  • {guide}")
    
    # Update config if not dry-run and updates were made
    if not dry_run and updated:
        config.installed_version = __version__
        config.save(str(config_path))
    
    # Print summary
    click.echo()
    if dry_run:
        if updated:
            click.echo(f"Would update {len(updated)} guide{'s' if len(updated) != 1 else ''}.")
            click.echo("Run without --dry-run to apply changes.")
        else:
            click.echo("No updates needed.")
    else:
        if updated:
            click.secho(f"✓ Updated {len(updated)} guide{'s' if len(updated) != 1 else ''}.", fg='green')
        elif skipped and not current:
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
    
    # Check if any overrides exist
    if not config.overrides:
        click.echo("No overridden guides.")
        return
    
    # List overrides
    click.echo(f"Overridden guides ({len(config.overrides)}):")
    for guide_name, override in sorted(config.overrides.items()):
        click.echo(f"  • {guide_name}")
        click.echo(f"    Reason: {override.reason}")
        click.echo(f"    Locked version: v{override.locked_version}")
        click.echo(f"    Last updated: {override.last_updated}")


if __name__ == "__main__":
    main()
