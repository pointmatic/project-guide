# Override Management

Learn how to effectively manage guide overrides to balance customization with receiving updates.

## Understanding Overrides

An override tells project-guide: "I've customized this guide—don't update it automatically."

### Why Overrides Matter

- **Preserve customizations**: Your project-specific changes won't be overwritten
- **Selective updates**: Update some guides while keeping others locked
- **Version tracking**: Know which version you customized from

## Override Lifecycle

### 1. Customize a Guide

Edit the guide file to add project-specific content:

```bash
vim docs/guides/project-guide.md
# Add your customizations
```

### 2. Mark as Overridden

Tell project-guide not to update this guide:

```bash
project-guide override project-guide.md --reason "Added team workflow steps"
```

### 3. Continue Updating Others

Other guides still receive updates:

```bash
project-guide update
# Only non-overridden guides are updated
```

### 4. Review New Versions (Optional)

Periodically check what's new:

```bash
# Force update creates .bak backup
project-guide update --force

# Compare versions
diff docs/guides/project-guide.md docs/guides/project-guide.md.bak
```

### 5. Decide: Keep or Adopt

Either keep your override or adopt the new version:

```bash
# Keep override (restore from backup)
mv docs/guides/project-guide.md.bak docs/guides/project-guide.md

# Or adopt new version (remove override)
project-guide unoverride project-guide.md
rm docs/guides/project-guide.md.bak
```

## Override Strategies

### Strategy 1: Override Heavily Customized Guides

**Use case**: Guides with significant project-specific content

```bash
# Customize for your project
vim docs/guides/project-guide.md
# Add company-specific sections, remove irrelevant parts

# Lock it
project-guide override project-guide.md \
  --reason "Customized for company workflow and security requirements"
```

**Pros**: Preserves all customizations
**Cons**: Misses workflow improvements

### Strategy 2: Minimal Overrides, Frequent Reviews

**Use case**: Want to receive most updates

```bash
# Only override when absolutely necessary
# Periodically review new versions
project-guide update --force
diff docs/guides/*.md docs/guides/*.md.bak

# Merge improvements manually
```

**Pros**: Receives workflow improvements
**Cons**: Requires manual merging

### Strategy 3: Hybrid Approach

**Use case**: Balance customization and updates

```bash
# Override guides with project-specific content
project-guide override project-guide.md

# Keep general guides up-to-date
# (best-practices-guide.md, debug-guide.md, etc.)
project-guide update
```

**Pros**: Best of both worlds
**Cons**: Requires thoughtful decisions

## Best Practices

### 1. Document Override Reasons

Always use `--reason`:

```bash
project-guide override project-guide.md \
  --reason "Added sections for: internal APIs, security review process, deployment checklist"
```

This helps future you (and teammates) understand why.

### 2. Review Overrides Periodically

Set a reminder to review overrides:

```bash
# Monthly or quarterly
project-guide overrides
# Review each override: still needed?
```

### 3. Keep Override List Short

Only override when necessary:
- ✅ Project-specific workflow steps
- ✅ Company security requirements
- ✅ Custom tool integrations
- ❌ Minor wording preferences
- ❌ Formatting changes
- ❌ Typo fixes (contribute upstream instead)

### 4. Use Version Control

Track override decisions in git:

```bash
# After overriding
git add .project-guide.yml docs/guides/
git commit -m "Override project-guide.md: added internal deployment steps"
```

### 5. Team Communication

For team projects:
- Document overrides in README or CONTRIBUTING.md
- Discuss override decisions in team meetings
- Share override reasons in commit messages

## Common Scenarios

### Scenario 1: Adding Project-Specific Steps

**Problem**: Need to add steps specific to your project

**Solution**:
```bash
# Edit guide
vim docs/guides/project-guide.md
# Add section: "## Our Project Setup"

# Override
project-guide override project-guide.md \
  --reason "Added project-specific setup steps"
```

### Scenario 2: Removing Irrelevant Sections

**Problem**: Guide includes sections that don't apply

**Solution**:
```bash
# Edit guide
vim docs/guides/project-guide.md
# Remove sections that don't apply

# Override
project-guide override project-guide.md \
  --reason "Removed sections not applicable to our stack"
```

### Scenario 3: Integrating Internal Tools

**Problem**: Need to reference internal tools/systems

**Solution**:
```bash
# Edit guide
vim docs/guides/project-guide.md
# Add references to internal CI/CD, code review tools

# Override
project-guide override project-guide.md \
  --reason "Integrated with internal tools: Jenkins, Gerrit, Artifactory"
```

### Scenario 4: Accidentally Overrode

**Problem**: Marked guide as overridden by mistake

**Solution**:
```bash
# Remove override
project-guide unoverride project-guide.md

# Update to latest
project-guide update
```

### Scenario 5: Want to See New Version

**Problem**: Guide is overridden but want to see what's new

**Solution**:
```bash
# Force update (creates backup)
project-guide update --force

# Compare
diff docs/guides/project-guide.md docs/guides/project-guide.md.bak

# Decide what to do
# Option A: Keep override
mv docs/guides/project-guide.md.bak docs/guides/project-guide.md

# Option B: Merge manually
# (edit project-guide.md to incorporate new improvements)

# Option C: Adopt new version
project-guide unoverride project-guide.md
rm docs/guides/project-guide.md.bak
```

## Override Metadata

Overrides are stored in `.project-guide.yml`:

```yaml
overrides:
  project-guide.md:
    version: "1.1.0"
    reason: "Customized for our team workflow"
  debug-guide.md:
    version: "1.1.2"
    reason: "Added project-specific debugging steps"
```

### Fields

- `version`: Package version when guide was overridden
- `reason`: Why the guide was overridden (optional but recommended)

## Advanced: Selective Merging

For advanced users who want to merge improvements:

```bash
# 1. Force update to get latest
project-guide update --force

# 2. Use three-way merge
# Original: version when you overrode
# Yours: your customized version (now .bak)
# Theirs: new version (now current)

# 3. Manually merge
vim docs/guides/project-guide.md
# Incorporate improvements while keeping customizations

# 4. Keep override
# (already overridden, no action needed)
```

## Next Steps

- [Commands Reference](commands.md) - Detailed command documentation
- [Workflow Guide](workflow.md) - See overrides in action
- [Configuration](../getting-started/configuration.md) - Understand configuration
