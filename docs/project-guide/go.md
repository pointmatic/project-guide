# Project-Guide — Calm the chaos of LLM-assisted coding

This document provides step-by-step instructions for an LLM to assist a human developer in a project. 

## How to Use Project-Guide

### For Developers
After installing project-guide (`pip install project-guide`) and running `project-guide init`, instruct your LLM as follows in the chat interface: 

```
Read `docs/project-guide/go.md`
```

After reading, the LLM will respond:
1. (optional) "I need more information..." followed by a list of questions or details needed. 
  - LLM will continue asking until all needed information is clear.
2. "The next step is ___."
3. "Say 'go' when you're ready." 

For efficiency, when you change modes, start a new LLM conversation. 

### For LLMs

**Modes**
This Project-Guide offers a human-in-the-loop workflow for you to follow that can be dynamically reconfigured based on the project `mode`. Each `mode` defines a focused sequence of steps to guide you (the LLM) to help generate artifacts for some facet in the project lifecycle. This document is customized for plan_phase.

**Approval Gate**
When you have completed the steps, pause for the developer to review, correct, redirect, or ask questions about your work.  

**Rules**
- Work through each step methodically, presenting your work for approval before continuing a cycle. 
- When the developer says "go" (or equivalent like "continue", "next", "proceed"), continue with the next action. 
- If the next action is unclear, tell the developer you don't have a clear direction on what to do next, then suggest something. 
- Never auto-advance past an approval gate—always wait for explicit confirmation. 
- After compacting memory, re-read this guide to refresh your context.

---

# plan_phase mode (sequence)

> Generate a feature phase prompt, which includes a mini-concept, features, and technical details


Generate a combined concept/features/tech-spec document for a new phase in an existing project, then add the phase and stories to `docs/specs/stories.md`.

Use this mode when the developer wants to add a significant new capability to a project that already has an established codebase and spec documents.

**Next Action**
Prompt the user to change modes. 

```bash
project-guide mode code_velocity
```

---


## Prerequisites

Before planning a new phase, the following should exist:
- `docs/specs/concept.md`
- `docs/specs/features.md`
- `docs/specs/tech-spec.md`
- `docs/specs/stories.md`

## Steps

1. Read the existing spec documents to understand the current project state.

2. Gather information from the developer about the new phase:
   - phase_name: A short name for the phase (e.g., "Mode System", "API Integration")
   - problem_gap: What capability is missing or what problem this phase solves
   - new_features: What the phase will add (functional requirements)
   - technical_approach: How it will be built (architecture changes, new modules, new dependencies)
   - constraints: Any limitations or compatibility requirements with existing code
   - scope: What this phase will and won't do

3. Generate a phase plan document at `docs/specs/phase-<name>-plan.md` that combines:
   - **Gap analysis**: What exists vs. what's needed
   - **Feature requirements**: What the phase adds (mini features.md)
   - **Technical changes**: New/modified modules, dependencies, config changes (mini tech-spec.md)
   - **Out of scope**: What's deferred to future phases

4. Present the phase plan to the developer for approval.

5. After approval, add a new phase section and stories to `docs/specs/stories.md`:
   - Determine the next phase letter
   - Break the phase into stories following the standard story format
   - Include a spike story if the phase introduces a new integration boundary

6. Present the updated stories to the developer for approval.

