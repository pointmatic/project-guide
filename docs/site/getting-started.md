# Getting Started

Get up and running with project-guide in minutes.

## 1. Install

Install project-guide using pip or pipx:

```bash
pip install project-guide
```

Or for system-wide access:

```bash
pipx install project-guide
```

## 2. Initialize Your Project

Navigate to your project directory and initialize project-guide:

```bash
cd /path/to/your/project
project-guide init
```

This creates:

- `.project-guide.yml` configuration file in your project root
- `docs/project-guide/` directory with mode templates
- `docs/project-guide/go.md` rendered guide for your current mode

## 3. Start Collaborating with Your LLM

Tell your LLM to read the rendered guide and begin:

```
Read docs/project-guide/go.md
```

The guide walks your LLM through structured development steps based on the active mode.

## 4. Control the Workflow

As the LLM completes each step, when you're ready, type:

```
go
```

You stay in charge -- directing features, flow, and taste -- while the LLM handles the typing.

## 5. Switch Modes

project-guide includes 15 development modes. Switch between them to match your current task:

```bash
project-guide mode code_velocity
project-guide mode debug
```

Each mode renders a fresh `go.md` tailored to that workflow.

## HITLoop Development

This is "HITLoop" (human-in-the-loop) development:

- **You direct**: Features, architecture, priorities
- **LLM executes**: Planning, coding, testing, documentation
- **Pace**: Production-ready backends in 6-12 hours

## Managing Customizations

### Override a Template

When you need to customize a mode template for your project:

```bash
project-guide override templates/modes/debug-mode.md "Custom debugging workflow"
```

This marks the template as overridden, preventing future updates from overwriting your changes.

### Update Non-Overridden Files

Pull the latest workflow improvements:

```bash
project-guide update
```

This updates all non-overridden files to the latest versions.

### Check Status

See which files are current, outdated, or overridden:

```bash
project-guide status
```

## Next Steps

- [Commands Reference](user-guide/commands.md) - Learn all available commands
- [Workflow Guide](user-guide/workflow.md) - Understand the complete workflow
- [Configuration](user-guide/configuration.md) - Customize project-guide behavior
- [Override Management](user-guide/overrides.md) - Master the override system
