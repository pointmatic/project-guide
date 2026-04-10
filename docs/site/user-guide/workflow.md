# Workflow Guide

Learn how to use project-guide effectively in your LLM-assisted development workflow.

## The HITLoop Philosophy

Project-Guide has an opinionated human-in-the-loop (HITLoop) approach -- that is...good software needs humans to gather context from the real world and real experience to apply wisdom and intuition in what makes it valuable.

- **You direct**: Concept, features, architecture, priorities, taste
- **LLM executes**: Planning, coding, testing, documentation
- **You review**: Approve, refine, guide
- **Result**: Production-ready single-purpose projects in 6-12 hours

## Workflow Pattern

### Setup
1. Setup your local repository
2. Install project-guide
3. Initialize project guide

For step-by-step setup instructions, see [Getting Started](../getting-started.md).

### Get in the Mode
Decide the style of development.
- **Go**: Get coding now (change mode to `code_velocity` or `code_test_first`)
- **Ready-Set-Go**: Plan the concept, features, and tech-spec, scaffold the project, then start coding.

### Modes
There are several kinds of modes to choose from. See details in [Modes](modes.md).

**Default**
There are some basic instructions for the LLM to follow. Switch to a more specific mode to take advantage of `project-guide`.

**First Time**
Use when you're starting a new project or adding `project-guide` to an existing project.

- **Plan**: `plan_concept` –> `plan_features` –> `plan_tech_spec` –> `plan_stories`
- **Scaffold**: (new project only) `project_scaffold`

**Build**
Work from a list of stories in `docs/project-guide/stories.md`.
- **Code**: Either `code_velocity` or `code_test_first`
- **Review**: Monitor the output as the LLM works, then look over the results and provide feedback.
- **Repeat**: Continue cycling through code and review until the build is complete.

**Targeted Development**
Work from a specific story in `docs/project-guide/stories.md`.
- **Debug**: Use `debug` mode for a test-first then fix approach.
- **Improve**: Plan a new phase with `plan_phase` which follows a mini Ready-Set-Go sequence.

**Documentation**
- **Brand Descriptions**: Use `document_brand` to develop your marketing messaging.
- **Landing Page**: Use `document_landing` to help other developers understand and use your project.

**Refactor**
- **Plan**: Use `refactor_plan` to update existing planning documents.
- **Document**: Use `refactor_document` to update existing documentation files.

## The HITLoop Cycle

Within any cycle mode, the rhythm is the same:

1. **LLM proposes** a step based on the active mode's instructions
2. **You review** the proposal
3. **You approve** by typing `go`, or redirect with feedback
4. **LLM executes** the approved step
5. **Repeat** until the cycle is complete or you switch modes

The LLM never auto-advances past an approval gate. You stay in control.

## When to Switch Modes

Mode switching is the core of the workflow. Common transitions:

| Situation | Switch to |
|-----------|-----------|
| Finished planning, ready to build | `code_velocity` or `code_test_first` |
| Bug discovered during build | `debug` |
| New feature phase needed | `plan_phase` |
| Existing planning docs need updates | `refactor_plan` |
| Existing documentation needs updates | `refactor_document` |
| Preparing for release | `document_brand` then `document_landing` |

After switching, tell the LLM to re-read `docs/project-guide/go.md`. A fresh chat window is most efficient.

## Customization and Updates

When you customize a file for project-specific needs, lock it with `project-guide override` so future package updates skip it. Run `project-guide update` regularly to pull in workflow improvements for non-locked files. See [Override Management](overrides.md) for details.

## Next Steps

- [Getting Started](../getting-started.md) - Install and initialize
- [Modes](modes.md) - Detailed reference for all 15 modes
- [Commands Reference](commands.md) - All CLI commands
- [Override Management](overrides.md) - Lock customized files
- [Configuration](configuration.md) - `.project-guide.yml` reference
