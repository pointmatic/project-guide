# Phase Plan -- {{ project_name }}

Generate a combined concept/features/tech-spec document for a new phase in an existing project, then add the phase and stories to `docs/specs/stories.md`.

Use this mode when the developer wants to add a significant new capability to a project that already has an established codebase and spec documents.

{% include "modes/_header-sequence.md" %}

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
