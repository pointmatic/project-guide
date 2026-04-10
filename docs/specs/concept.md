# concept.md — project-guide (Python)

This document defines why the `project-guide` project exists.
- **Problem space**: problem statement, why, pain points, target users, value criteria
- **Solution space**: solution statement, goals, scope, constraints
- **Value mapping**: Pain point to solution mapping

For requirements and behavior (what), see `features.md`. For implementation details (how), see `tech-spec.md`. For a breakdown of the implementation plan (step-by-step tasks), see `stories.md`.

## Problem Space

### Problem Statement
Developing software with LLM assistance is powerful but chaotic. Without a framework, each project becomes a unique snowflake of ad-hoc prompts, lost context, and inconsistent practices. The many learnings from project-to-project are difficult to apply systematically.

**Why this problem exists:**
It is too early in the AI revolution for proven practices to emerge. Developers are left to choose between competing philosophies, each with significant trade-offs:

| Philosophy | Description | Advantages | Disadvantages |
|-|-|-|-|
| **Vibe-coding** | Give the AI a high-level description and let it figure out the details. | Empowers non-technical people, fast iteration and experimentation, can help clarify requirements | Can lead to unexpected results or unmaintainable code, often results in an 80%-90% solution requiring significant cleanup |
| **Agentic coding** | Give a herd of AI agents a problem and let them work autonomously. | Can build complex systems, can be better than an average programmer | Difficult for a developer to cognitively manage so much generated code, many report "AI slop" (strange problems harder to track down than writing it differently), code becomes a burden if AI decisions don't align with product value |
| **HITLoop (Human-In-The-Loop)** | Collaborate closely with the AI to accelerate ideation, experimentation, and generation, but supervise all activities to redirect when the AI is off course or when a better idea emerges. | Product decisions are made on-the-fly as they emerge, developer gains familiarity with the codebase, opportunities to redirect early | Slower than agentic or vibe-coding, requires active involvement, can be tempting to disengage during generation |

### Pain Points
1. **Repetitive**: AI-assisted coding has many repetitive actions and prompts.
2. **Error-prone**: Copy-pasting prompts from a scratch-pad is error-prone and time-consuming.
3. **AI decisions**: Turning over high-level decision-making to the LLM is risky and unreliable.
4. **AI forgetting**: Managing the context window is difficult and leads to cyclical forgetting.
5. **Best practices**: Most software best practices are known generally but not codified for AI-assisted development.
6. **Documentation**: Key decisions and trade-offs are easily lost in LLM chat history.
7. **AI opacity**: Tracking LLM plans and progress is opaque; styles and formats change across versions and models.
8. **Consistency**: Applying best practices and lessons learned consistently is practically impossible without a framework.

## Solution Space
`project_guide` is a Python CLI tool that provides a framework for HITLoop AI-assisted software development. The developer operates at a higher level of abstraction, focusing on strategic decisions while the framework handles the repetitive tasks of document generation and coding workflow management. **The LLM never commits code.**

### Solution Statement
A mode-driven template system that dynamically renders a single entry-point document (`go.md`) for the LLM to read. Each mode defines a focused workflow (planning, coding, debugging, refactoring) with its own steps, prerequisites, and completion criteria. The developer switches modes via the CLI, and the LLM reads the re-rendered entry point to begin collaborating in the new context.

### Goals
1. Reduce repetitive prompting by codifying workflows into reusable mode templates
2. Keep the developer in the loop for all strategic decisions (HITLoop philosophy)
3. Provide a standardized documentation pipeline: concept, features, tech-spec, stories
4. Enable consistent best practices across all projects via versioned, updatable templates
5. Make the LLM's work transparent and accountable through structured artifacts

### Scope
- **CLI tool**: `project-guide init`, `mode`, `status`, `update`, `override`, `unoverride`, `overrides`, `purge`
- **15 modes**: `default`, `project_scaffold`, `plan_concept`, `plan_features`, `plan_tech_spec`, `plan_stories`, `plan_phase`, `code_velocity`, `code_test_first`, `debug`, `document_brand`, `document_landing`, `refactor_plan`, `refactor_document`, and a future `code_production`
- **Jinja2 rendering**: mode templates + header partials rendered into a single entry-point document
- **Hash-based file sync**: content-hash comparison determines file freshness, not version numbers
- **Override system**: lock files from updates when they contain project-specific customizations

### Constraints
1. Pure Python, minimal dependencies (click, jinja2, pyyaml, packaging)
2. Works on macOS, Linux, and Windows
3. No network access after installation
4. No LLM API calls — the framework provides structure, the LLM fills in content conversationally
5. The LLM never commits code; the developer owns all git operations

## Value Mapping

| Pain Point | Solution |
|-|-|
| **Repetitive** | Standardized mode templates eliminate repetitive prompting; a single `go.md` entry point replaces ad-hoc context setup |
| **Error-prone** | Dynamically rendered entry point means no copy-pasting; mode switching is a single CLI command |
| **AI decisions** | HITLoop workflow keeps developer close to the work; approval gates prevent autonomous AI decisions |
| **AI forgetting** | Focused modes reduce token burden; re-reading `go.md` after context compaction restores full context |
| **Best practices** | Each mode embeds focused best practices; versioned templates distribute improvements across all projects |
| **Documentation** | Structured artifact pipeline (concept → features → tech-spec → stories) ensures documentation is comprehensive with minimal effort |
| **AI opacity** | Planning is transparent and permanent in four spec documents; story-driven implementation inverts control from the LLM's internal plan to a developer-owned document |
| **Consistency** | Templated approach ensures consistency; hash-based sync keeps templates current without forcing unnecessary updates |
