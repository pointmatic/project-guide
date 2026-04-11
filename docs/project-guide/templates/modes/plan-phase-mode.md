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

   `docs/specs/stories.md` may be in one of two shapes:

   a. **Populated** — contains one or more `## Phase <Letter>:` sections from prior phases. Use the highest existing phase letter as the basis for the next one (see step 5).

   b. **Empty (post-archive)** — `archive_stories` was just run and `stories.md` contains only the header and a `## Future` section, no phases. In this case, look in `docs/specs/.archive/` for files named `stories-vX.Y.Z.md`. Read the one with the highest version and find its highest `## Phase <Letter>:` heading — that is the basis for the next phase letter. Phase letters **continue across the archive boundary**; they do not reset.

   If neither `stories.md` nor `.archive/` contains any phases, this is a fresh project — start at `A`.

2. Gather information from the developer about the new phase:
   - phase_name: A short name for the phase (e.g., "Mode System", "API Integration")
   - problem_gap: What capability is missing or what problem this phase solves
   - new_features: What the phase will add (functional requirements)
   - technical_approach: How it will be built (architecture changes, new modules, new dependencies)
   - constraints: Any limitations or compatibility requirements with existing code
   - scope: What this phase will and won't do

3. Generate a phase plan document at `docs/specs/phase-<letter>-<name>-plan.md` that combines:
   - **Gap analysis**: What exists vs. what's needed
   - **Feature requirements**: What the phase adds (mini features.md)
   - **Technical changes**: New/modified modules, dependencies, config changes (mini tech-spec.md)
   - **Out of scope**: What's deferred to future phases

4. Present the phase plan to the developer for approval.

5. After approval, add a new phase section and stories to `docs/specs/stories.md`:
   - **Determine the next phase letter** by applying the algorithm from step 1:
     - If `stories.md` had existing phases, the next letter is the successor of the highest one (e.g., `K` → `L`).
     - If `stories.md` was empty but `.archive/` had a `stories-vX.Y.Z.md`, read the latest archived file, find its highest phase letter, and take its successor (e.g., archived Phase `J` → next phase `K`).
     - If neither had phases, start at `A`.
   - The successor follows the base-26-no-zero scheme (`Z` → `AA`, `ZZ` → `AAA`). See the Phase and Story ID Scheme below for details.
   - If `stories.md` was empty, **insert the new phase as the first phase** in the file (after the header and `---`, before any `## Future` section). Otherwise append after the highest existing phase but before `## Future`.
   - Break the phase into stories following the standard story format.
   - Include a spike story if the phase introduces a new integration boundary.

6. Present the updated stories to the developer for approval.

{% include "modes/_phase-letters.md" %}
