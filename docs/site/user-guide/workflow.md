# Workflow Guide

Learn how to use project-guide effectively in your LLM-assisted development workflow.

## The HITLoop Workflow

project-guide supports "HITLoop" (human-in-the-loop) development where:
- **You direct**: Features, architecture, priorities, taste
- **LLM executes**: Planning, coding, testing, documentation
- **Result**: Production-ready projects in 6-12 hours

## Initial Setup

### 1. Install project-guide

```bash
pip install project-guide
```

### 2. Initialize Your Project

```bash
cd /path/to/your/project
project-guide init
```

This creates:
- `docs/guides/` with all workflow guides
- `.project-guide.yml` configuration

### 3. Start the LLM Workflow

Tell your LLM:

```
Read `docs/guides/project-guide.md` and start.
```

The guide walks the LLM through:
1. Creating planning documents (features.md, tech-spec.md, stories.md)
2. Breaking work into stories and tasks
3. Implementing each story step-by-step

### 4. Guide Each Step

As the LLM completes steps, say:

```
proceed
```

You stay in control, approving each step before moving forward.

## Common Workflows

### Starting a New Project

```bash
# 1. Create project directory
mkdir my-project && cd my-project

# 2. Initialize git
git init

# 3. Install project-guide
pip install project-guide

# 4. Initialize guides
project-guide init

# 5. Start LLM collaboration
# Tell LLM: "Read `docs/guides/project-guide.md` and start."
```

### Adding Guides to Existing Project

```bash
# Navigate to project
cd existing-project

# Initialize project-guide
project-guide init

# Check status
project-guide status
```

### Updating Guides Across Projects

```bash
# Update project-guide package
pip install --upgrade project-guide

# Update guides in each project
cd project1
project-guide update

cd ../project2
project-guide update
```

### Customizing a Guide

```bash
# 1. Edit the guide file
vim docs/guides/project-guide.md

# 2. Mark as overridden
project-guide override project-guide.md --reason "Added team-specific workflow"

# 3. Verify override
project-guide status
```

### Syncing Latest Improvements

```bash
# Check which guides are outdated
project-guide status

# Update non-overridden guides
project-guide update

# Review changes
git diff docs/guides/
```

## Multi-Project Management

### Keeping Guides in Sync

When working on multiple projects:

1. **Update package globally** (if using pipx):
   ```bash
   pipx upgrade project-guide
   ```

2. **Update each project**:
   ```bash
   for project in project1 project2 project3; do
     cd $project
     project-guide update
     cd ..
   done
   ```

3. **Review changes**:
   ```bash
   git diff docs/guides/
   ```

### Managing Project-Specific Customizations

For guides customized per project:

```bash
# Project A: Custom project-guide
cd projectA
project-guide override project-guide.md

# Project B: Custom debug-guide
cd ../projectB
project-guide override debug-guide.md

# Both: Update non-overridden guides
project-guide update
```

## Override Management

### When to Override

Override a guide when:
- You've customized it for your project's specific needs
- The guide contains project-specific instructions
- You want to prevent updates from overwriting changes

### When NOT to Override

Don't override if:
- You want to receive workflow improvements
- The customization is minor (consider contributing upstream instead)
- You're just experimenting (test changes first)

### Reviewing Overridden Guides

Periodically review overridden guides:

```bash
# List all overrides
project-guide overrides

# Check what's new in latest version
project-guide update --force  # Creates .bak files
diff docs/guides/project-guide.md docs/guides/project-guide.md.bak

# Decide: keep override or adopt new version
```

## Best Practices

### 1. Version Control

Always commit guides to version control:

```bash
git add docs/guides/ .project-guide.yml
git commit -m "Initialize project-guide"
```

### 2. Document Overrides

Use the `--reason` flag when overriding:

```bash
project-guide override project-guide.md \
  --reason "Added company-specific security requirements"
```

### 3. Regular Updates

Update guides regularly to get improvements:

```bash
# Weekly or monthly
project-guide update
git diff docs/guides/
git commit -m "Update project-guide to latest"
```

### 4. Review Before Committing

Always review guide updates before committing:

```bash
project-guide update
git diff docs/guides/
# Review changes, then commit
```

### 5. Team Coordination

For team projects:
- Document which guides are overridden and why
- Share override decisions with the team
- Consider contributing improvements back to project-guide

## Troubleshooting

### Guides Not Updating

Check if guides are overridden:

```bash
project-guide status
project-guide overrides
```

### Accidental Override

Remove override to allow updates:

```bash
project-guide unoverride <guide-name>
project-guide update
```

### Lost Customizations

If you updated with `--force`, restore from backup:

```bash
mv docs/guides/project-guide.md.bak docs/guides/project-guide.md
project-guide override project-guide.md
```

## Next Steps

- [Commands Reference](commands.md) - Detailed command documentation
- [Override Management](overrides.md) - Master the override system
- [Configuration](../getting-started/configuration.md) - Customize behavior
