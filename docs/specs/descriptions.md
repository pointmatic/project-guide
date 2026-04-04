# descriptions.md — project-guide

Canonical source of truth for all descriptive language used across the project. All consumer files (README.md, docs/index.html, pyproject.toml, features.md) should draw from these definitions.

---

## Name

- project-guide (GitHub and PyPI)

## Tagline

Stay organized in LLM-based coding

## Long Tagline

Stay organized and consistent using LLM workflow guides with project-specific overrides

## One-liner

Stay organized and consistent using LLM guides across multiple coding projects.

### Friendly Brief Description (follows one-liner)

Install project-guide in any repository with `pip install project-guide`, run `project-guide init`, then tell your LLM to "Read `docs/guides/project-guide.md` and start." The guide walks the LLM through planning documents, breaking work into stories, and implementing each story step-by-step. You just say "proceed" after each step. The developer stays in charge—guiding features, flow, and taste—while the LLM handles the typing.

This is "HITLoop" (human-in-the-loop) development: the developer directs, the LLM executes. The pace is "flaming agile"—an entire production-ready backend can be completed in 6-12 hours. When you customize a guide for your project, mark it as overridden so future package updates skip it. When you want the latest workflow improvements, run `project-guide update` to sync all non-overridden guides. 

## Two-clause Technical Description

A Python CLI tool that installs and synchronizes battle-tested LLM workflow guides across projects, supporting version tracking and project-specific overrides to keep documentation consistent while preserving customizations.

## Benefits

- **Centralized Templates** — Maintain workflow guides (project-guide.md, best-practices-guide.md, debug-guide.md, documentation-setup-guide.md) in one place
- **Version Management** — Track guide versions across projects and update to latest versions with a single command
- **Override Support** — Lock specific guides when they contain project-specific customizations, preventing accidental overwrites
- **Backup Protection** — Automatic `.bak` file creation when updating overridden guides with `--force` flag
- **CLI Interface** — Seven intuitive commands: init, status, update, override, unoverride, overrides, purge
- **Zero Configuration** — Works with sensible defaults (docs/guides directory, no config required for basic use)
- **Cross-Platform** — Runs on macOS, Linux, and Windows with Python 3.11+
- **Well Tested** — 82% test coverage with 53 comprehensive tests ensuring reliability
- **Lightweight** — Minimal dependencies (click, pyyaml, packaging) for fast installation
- **Safe Operations** — Never overwrites customized guides without explicit consent, idempotent commands

## Technical Description

Project-Guide is a Python CLI tool that solves the problem of keeping LLM workflow documentation synchronized with an opinionated source of truthacross multiple projects. Just install the PyPI package with `pip` in any repository and start planning and coding with the LLM. It packages canonical versions of development guides (project-guide.md, best-practices-guide.md, debug-guide.md, documentation-setup-guide.md, and more) and provides commands to install, update, and manage them in a `docs/guides` directory in the repo. The tool tracks which package versions were installed for each guide, allows a project to lock specific guides when customized, and provides clear status reporting. It uses a simple YAML configuration file (`.project-guide.yml`) to store project-specific settings and override metadata. The package is distributed via PyPI and can be installed with `pip` locally or `pipx` for system-wide CLI access.

## Keywords

`llm`, `human-in-the-loop`, `hitloop`, `documentation`, `workflow`, `guides`, `templates`, `python`, `cli`, `version-management`, `synchronization`, `project-management`, `development-tools`, `best-practices`, `override-support`, `yaml-config`, `cross-platform`

---

## Quick Start

Essential steps for getting started with project-guide:

1. **Install**: `pip install project-guide` (or `pipx install project-guide` for system-wide CLI)
2. **Initialize**: Navigate to your project directory and run `project-guide init`
3. **Start**: Tell your LLM: "Read `docs/guides/project-guide.md` and start."
4. **Collaborate**: Say "proceed" after each step as the LLM walks through planning, stories, and implementation
5. **Customize**: Mark guides as overridden when you customize them: `project-guide override <guide-name>`
6. **Update**: Pull latest workflow improvements: `project-guide update`
7. **Check Status**: See which guides are current, outdated, or overridden: `project-guide status`

---

## Feature Cards

Short blurbs for landing pages and feature grids. Each card has a title and a one-to-two sentence description.

### Core Capabilities

| # | Title | Description |
|---|-------|-------------|
| 1 | Battle-Tested Workflows | Crafted guides walk your LLM from project concept through production release—planning docs, stories breakdown, step-by-step implementation. |
| 2 | Centralized Guide Templates | Maintain LLM workflow guides in one package and distribute them across all your projects with a single command. |
| 3 | Smart Version Tracking | Track which guide versions are installed in each project and update to the latest versions automatically. |
| 4 | Project-Specific Overrides | Lock customized guides to prevent accidental overwrites while still syncing other guides to latest versions. |
| 5 | Sync Latest Improvements | Pull the newest workflow refinements into all non-overridden guides across projects with one command. |

### Operational Benefits

| # | Title | Description |
|---|-------|-------------|
| 6 | Zero Configuration | Works out of the box with sensible defaults—guides go in `docs/guides`, no config file needed for basic usage. |
| 7 | Clear Status Reporting | See at a glance which guides are current, outdated, overridden, or missing with color-coded status output. |
| 8 | Automatic Backups | When updating overridden guides with --force, automatic .bak files preserve your customizations. |
| 9 | Safe Operations | Idempotent commands and explicit consent requirements ensure you never lose project-specific customizations. |
| 10 | Lightweight & Fast | Minimal dependencies (click, pyyaml, packaging) mean fast installation and no bloat. |
| 11 | Cross-Platform | Runs on macOS, Linux, and Windows with Python 3.11+ for consistent workflows everywhere. |
| 12 | Well Tested | 82% test coverage with 53 comprehensive tests ensuring reliability and stability. |

### Development Philosophy

| # | Title | Description |
|---|-------|-------------|
| 13 | HITLoop Development | You direct features, flow, and taste. The LLM handles the typing. Human-in-the-loop collaboration at its best. |
| 14 | Flaming Agile Pace | Complete an entire production-ready backend in 6-12 hours with structured, methodical LLM collaboration. |
| 15 | Structured Workflow | Guides enforce a proven methodology: planning documents, story breakdown, step-by-step implementation, approval gates. |


---

## Usage Notes

| File | Which descriptions to use |
|------|--------------------------|
| `README.md` line 8 | Two-clause Technical Description (shortened to one sentence) |
| `README.md` line 12 | Friendly Brief Description (first sentence) |
| `docs/site/index.html` hero `<h1>` | Tagline |
| `docs/site/index.html` hero subtitle | Long Tagline |
| `docs/site/index.html` feature grid | Feature Cards |
| `pyproject.toml` description | Long Tagline |
| `docs/specs/features.md` line 11 | Two-clause Technical Description |
| GitHub Repository description | One-liner + ": " + Long Tagline |
| GitHub Repository topics | Keywords (without backticks) |
