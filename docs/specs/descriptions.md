# descriptions.md — project-guide

Canonical source of truth for all descriptive language used across the project. All consumer files (README.md, docs/index.html, pyproject.toml, features.md) should draw from these definitions.

---

## Name

- project-guide (GitHub and PyPI)

## Tagline

Calm the chaos

## Long Tagline

Calm the chaos of LLM-assisted coding 

## One-liner

Stay organized and in control with adaptive LLM workflow prompts

### Friendly Brief Description (follows one-liner)

Install project-guide in any repository with `pip install project-guide`, run `project-guide init`, then tell your LLM to "Read `@project-guide.md` (works in many coding tools), or give itthe full path at`docs/project-guide/go-project-guide.md`." The `go-project-guide` prompt provides the LLM with a structured workflow. You just say "go" and the LLM handles each step, pausing for you to review code, test, and commit changes. You stay in charge—guiding features, flow, and taste while the LLM handles the typing.

This is "HITLoop" (human-in-the-loop) development: you direct, the LLM executes. The pace is "flaming agile"—an entire production-ready backend can be completed in 6-12 hours. When you customize a prompt for your project, mark it as overridden so future package updates skip it. When you want the latest workflow improvements, run `project-guide update` to sync all non-overridden prompts. 

## Two-clause Technical Description

A Python CLI tool that installs, swaps, and synchronizes battle-tested LLM workflow prompts across projects, supporting version tracking and project-specific overrides to keep documentation consistent while preserving customizations.

## Benefits

- **Battle-Tested Workflows** - Crafted workflow prompts from concept through production release in one place
- **Adaptive** — Switch project between plan, code, and debug modes to get the right instructions for each task
- **Version Management** — Track and update all prompt docs in a project with a single command
- **Customization Lock** - Lock customized prompts to prevent update overwrites
- **Gentle Force Updates** — Automatic `.bak` files created if you `--force` update a custom prompt document
- **CLI Interface** — Eight intuitive commands for all operations
- **Zero Configuration** — Works with sensible defaults out of the box
- **Cross-Platform** — Runs on macOS, Linux, and Windows with Python 3.11+
- **Well Tested** — Comprehensive test coverage for reliability
- **Lightweight** — Minimal dependencies (click, pyyaml, packaging) for fast installation

## Technical Description

Project-Guide is a Python CLI tool that solves the problem of keeping LLM workflow documentation synchronized with an opinionated source of truthacross multiple projects. Just install the PyPI package with `pip` in any repository and start planning and coding with the LLM. It packages canonical versions of LLM prompts and provides commands to install, update, and manage them in a `docs/project-guide` directory in any project repo. 

The tool tracks which package versions were installed for each guide, allows a project to lock specific guides when customized, and provides clear status reporting. It uses a simple YAML configuration file (`.project-guide.yml`) to store project-specific settings and override metadata. The package is distributed via PyPI and can be installed with `pip` locally or `pipx` for system-wide CLI access.

## Keywords

`llm`, `coding`, `human-in-the-loop`, `hitloop`, `documentation`, `workflow`, `guide`, `templates`, `python`, `cli`, `version-management`, `synchronization`, `project-management`, `development-tools`, `best-practices`, `override-support`, `yaml-config`, `cross-platform`

---

## Quick Start

Essential steps for getting started with project-guide:

1. **Install**: `pip install project-guide` (or `pipx install project-guide` for system-wide CLI)
2. **Initialize**: Navigate to your project directory and run `project-guide init`
3. **Start**: Tell your LLM: "Read `docs/project-guide/go-project-guide.md`."
4. **Collaborate**: Say "go" after each step as the LLM walks through planning, stories, and implementation
5. **Customize**: Mark a prompt document as overridden if you customize it: `project-guide override <filename>`
6. **Update**: Pull latest workflow improvements: `project-guide update`
7. **Check Status**: See which guides are current, outdated, or overridden: `project-guide status`

---

## Feature Cards

Short blurbs for landing pages and feature grids. Each card has a title and a one-to-two sentence description.

### Core Capabilities

| # | Title | Description |
|---|-------|-------------|
| 1 | Battle-Tested Workflows | Crafted workflow prompts from concept through production release in one place |
| 2 | Adaptive Guidance | Switch project between plan, code, and debug modes to get the right instructions for each task |
| 3 | Version Management | Track and update all prompt docs in a project with a single command |
| 4 | Custom Prompt Lock | Lock a customized LLM prompt in any project to prevent future updates for that prompt document |
| 5 | CLI Interface | Eight intuitive commands for all operations |
| 6 | Zero Configuration | Works out of the box with sensible defaults |

### Operational Benefits

| # | Title | Description |
|---|-------|-------------|
| 7 | Clear Status Reporting | See at a glance which prompt documents are current, outdated, overridden, or missing with color-coded status output |
| 8 | Gentle 'Forced' Updates | Automatic `.bak` files created if you `--force` update a custom prompt document |
| 9 | Safe Operations | Idempotent commands and explicit consent requirements protect your project-specific customizations |
| 10 | Lightweight | Minimal dependencies (click, pyyaml, packaging) mean fast installation and no bloat |
| 11 | Cross-Platform | Runs on macOS, Linux, and Windows with Python 3.11+ for consistent workflows everywhere |
| 12 | Well Tested | Comprehensive test coverage minimum of 75% ensures reliability |

### Development Philosophy

| # | Title | Description |
|---|-------|-------------|
| 13 | HITLoop Development | You direct features, flow, and taste. The LLM handles the typing. Human-in-the-loop collaboration at its best |
| 14 | Flaming Agile Pace | Complete an entire production-ready backend in 6-12 hours with structured, methodical LLM collaboration |
| 15 | Structured Workflow | The workflow enforces a focused methodology: planning, coding, debugging, etc. with approval gates for your review |

---

## Usage Notes

| File | Which descriptions to use |
|------|--------------------------|
| `README.md` line 9 | Two-clause Technical Description |
| `README.md` line 17 | Benefits (inline) |
| `docs/index.html` hero `<h1>` | One-liner |
| `docs/index.html` hero `<p>` | Friendly Brief Description |
| `docs/index.html` feature grid | Feature Cards |
| `pyproject.toml` description | One-liner |
| (GitHub Repository) | Tagline + ": "+ One-liner |
