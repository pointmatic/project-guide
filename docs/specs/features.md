# features.md — project-guides (Python)

This document defines **what** the `project-guides` project does — requirements, inputs, outputs, behavior — without specifying **how** it is implemented. This is the source of truth for scope.

For implementation details, see `tech-spec.md`. For the implementation plan, see the stories document (to be created).

---

## Project Goal

`project-guides` is a Python CLI tool that installs and synchronizes battle-tested LLM workflow guides across projects, supporting version tracking and project-specific overrides to keep documentation consistent while preserving customizations.

### Core Requirements

1. **Template Distribution**: Package and distribute canonical versions of LLM workflow guides (project-guide.md, best-practices-guide.md, debug-guide.md, documentation-setup-guide.md)
2. **Project Initialization**: Install guide templates into new projects with a single command
3. **Synchronization**: Update guides across projects to the latest canonical versions
4. **Override Management**: Allow projects to lock specific guides when they contain project-specific customizations
5. **Version Tracking**: Track which package version each project uses and which guides have been modified

### Operational Requirements

1. **CLI Interface**: Provide intuitive commands for init, update, status, override management
2. **Configuration**: Store project-specific settings in `.project-guides.yml` file
3. **Safety**: Never overwrite overridden guides without explicit user consent
4. **Transparency**: Show clear status of which guides are in sync, out of sync, or overridden
5. **Idempotency**: Running the same command multiple times produces the same result

### Quality Requirements

1. **Reliability**: Never corrupt or lose project-specific guide customizations
2. **Clarity**: Provide clear error messages and status output
3. **Minimal Dependencies**: Keep the package lightweight with few external dependencies
4. **Cross-Platform**: Work on macOS, Linux, and Windows

### Usability Requirements

1. **Primary Users**: Developers managing multiple Python projects with LLM assistance
2. **Installation**: Available via `pip install project-guides` or `pipx install project-guides`
3. **Zero Config**: Works with sensible defaults, no configuration required for basic use
4. **Documentation**: Clear README with examples for all commands

### Non-goals

1. **Not a project scaffolding tool** — only manages guide documentation, not project structure
2. **Not a template engine** — guides are static markdown files, not rendered templates
3. **Not a git tool** — does not manage version control, only file synchronization
4. **Not language-specific** — focuses on Python projects but guides are language-agnostic

---

## Inputs

### Command Line Arguments

**`project-guides init`**
- No required arguments
- Optional: `--target-dir` (default: `docs/guides`)
- Optional: `--force` (overwrite existing files)

**`project-guides update`**
- Optional: `--guides` (list of specific guides to update)
- Optional: `--dry-run` (show what would change without applying)
- Optional: `--force` (update even overridden guides, creates backups)
- Optional: `--interactive` (prompt for each guide)

**`project-guides status`**
- No arguments

**`project-guides override`**
- Required: `--guide` (guide filename)
- Required: `--reason` (explanation for override)

**`project-guides unoverride`**
- Required: `--guide` (guide filename)

**`project-guides overrides`**
- No arguments

### Configuration File

**`.project-guides.yml`** (created in project root):
```yaml
version: "1.0"
installed_version: "0.2.1"
target_dir: "docs/guides"
overrides:
  debug-guide.md:
    reason: "Custom case study"
    locked_version: "0.2.0"
    last_updated: "2026-03-03"
```

---

## Outputs

### File Structure

**After `project-guides init`:**
```
project-root/
├── .project-guides.yml          # Configuration file
└── docs/
    └── guides/
        ├── README.md
        ├── project-guide.md
        ├── best-practices-guide.md
        ├── debug-guide.md
        └── documentation-setup-guide.md
```

### Console Output

**`project-guides init`:**
```
Initializing project-guides v0.2.1...
✓ Created docs/guides/
✓ Installed project-guide.md
✓ Installed best-practices-guide.md
✓ Installed debug-guide.md
✓ Installed documentation-setup-guide.md
✓ Installed README.md
✓ Created .project-guides.yml

Successfully initialized 5 guides.
```

**`project-guides update`:**
```
Checking for updates...
✓ project-guide.md: Updated (0.2.0 → 0.2.1)
✓ best-practices-guide.md: Already up to date
⊘ debug-guide.md: Skipped (override: "Custom case study")
✓ documentation-setup-guide.md: Updated (0.2.0 → 0.2.1)

3 guides updated, 1 skipped, 1 already current
```

**`project-guides status`:**
```
project-guides v0.2.1 (installed: v0.2.0)

Guides status:
  ✓ project-guide.md          v0.2.1  (current)
  ✓ best-practices-guide.md   v0.2.1  (current)
  ⊘ debug-guide.md            v0.2.0  (overridden: "Custom case study")
  ⚠ documentation-setup-guide.md v0.2.0  (update available)

1 guide overridden, 1 update available
Run 'project-guides update' to sync.
```

---

## Functional Requirements

### FR-1: Template Distribution

The package must bundle canonical versions of all LLM workflow guides:
- `project-guide.md` — Core workflow for LLM-assisted project creation
- `best-practices-guide.md` — Diagnostic patterns for project quality audits
- `debug-guide.md` — Test-driven debugging methodology
- `documentation-setup-guide.md` — GitHub Pages setup workflow
- `README.md` — Directory overview

**Acceptance Criteria:**
- Templates are included in the package distribution
- Templates are accessible via Python package data
- Templates can be copied to arbitrary target directories

### FR-2: Project Initialization

`project-guides init` must install all guide templates into a new project.

**Behavior:**
1. Check if `.project-guides.yml` already exists
2. If exists and `--force` not set, prompt user to confirm overwrite
3. Create target directory if it doesn't exist (default: `docs/guides`)
4. Copy all guide templates to target directory
5. Create `.project-guides.yml` with current package version and default settings
6. Report success with list of installed guides

**Edge Cases:**
- Target directory already exists → use it, don't error
- Guides already exist → error unless `--force` is set
- `.project-guides.yml` exists → error unless `--force` is set
- No write permissions → error with clear message

### FR-3: Guide Synchronization

`project-guides update` must update guides to the latest package version.

**Behavior:**
1. Read `.project-guides.yml` to get current version and overrides
2. Compare installed version to package version
3. For each guide:
   - If overridden → skip (unless `--force` is set)
   - If current → skip
   - If outdated → update
4. Update `.project-guides.yml` with new package version
5. Report which guides were updated, skipped, or already current

**Edge Cases:**
- No `.project-guides.yml` → error, suggest running `init` first
- Guide file missing → recreate it (unless overridden)
- Guide modified but not overridden → warn and offer to override or update
- `--dry-run` → show changes without applying
- `--force` → update overridden guides, create `.bak` backups

### FR-4: Override Management

`project-guides override` must register a guide as project-specific.

**Behavior:**
1. Check if guide exists in target directory
2. Add override entry to `.project-guides.yml` with:
   - Guide filename
   - Reason for override
   - Current package version (locked version)
   - Current date
3. Report success

**Edge Cases:**
- Guide doesn't exist → error
- Guide already overridden → update reason and date
- No `.project-guides.yml` → error, suggest running `init` first

`project-guides unoverride` must remove an override.

**Behavior:**
1. Remove override entry from `.project-guides.yml`
2. Report success and suggest running `update` to sync

### FR-5: Status Reporting

`project-guides status` must show current state of all guides.

**Behavior:**
1. Read `.project-guides.yml`
2. Compare installed version to package version
3. For each guide, show:
   - Name
   - Current version
   - Status: current, outdated, overridden
   - Override reason (if applicable)
4. Show summary: X guides current, Y outdated, Z overridden

**Edge Cases:**
- No `.project-guides.yml` → error, suggest running `init` first
- Guide file missing → show as "missing"

### FR-6: Override Listing

`project-guides overrides` must list all overridden guides.

**Behavior:**
1. Read `.project-guides.yml`
2. List all overridden guides with:
   - Guide name
   - Reason
   - Locked version
   - Last updated date
3. Show count of overrides

---

## Configuration

### Configuration Precedence

1. Command-line flags (highest priority)
2. `.project-guides.yml` in project root
3. Package defaults (lowest priority)

### `.project-guides.yml` Schema

```yaml
version: "1.0"                    # Config schema version
installed_version: "0.2.1"        # Package version when last synced
target_dir: "docs/guides"         # Where guides are installed

overrides:
  <guide_filename>:
    reason: <string>              # Why this guide is overridden
    locked_version: <version>     # Package version when locked
    last_updated: <date>          # ISO 8601 date
```

---

## Testing Requirements

### Unit Tests

- Template loading and copying
- Configuration file parsing and writing
- Version comparison logic
- Override registration and removal
- Status reporting logic

### Integration Tests

- Full `init` workflow in temporary directory
- Full `update` workflow with version changes
- Override workflow (add, list, remove)
- Error handling for missing files and permissions

### Acceptance Tests

- Install guides in new project
- Update guides across version bump
- Override a guide and verify it's not updated
- Remove override and verify guide updates
- Status command shows correct state

**Minimum Coverage**: 85% code coverage

---

## Security and Compliance Notes

1. **File Safety**: Never overwrite files without explicit user consent (via `--force` or override removal)
2. **Backup Creation**: When `--force` is used, create `.bak` backups of overridden files
3. **Path Validation**: Validate target directory paths to prevent directory traversal attacks
4. **No Secrets**: Package contains only documentation templates, no sensitive data

---

## Performance Notes

1. **File I/O**: All operations are file-based, performance is not a concern
2. **No Network**: Package operates entirely offline after installation
3. **Minimal Memory**: Templates are small text files (<100KB total)

---

## Acceptance Criteria

The project is complete when:

1. ✅ All guide templates are bundled and installable
2. ✅ `project-guides init` creates guides and config in new projects
3. ✅ `project-guides update` syncs guides to latest version
4. ✅ `project-guides override` locks guides from updates
5. ✅ `project-guides status` shows accurate state
6. ✅ All commands have clear help text and error messages
7. ✅ Package is published to PyPI
8. ✅ README includes installation and usage examples
9. ✅ Test coverage is ≥85%
10. ✅ Works on macOS, Linux, and Windows
