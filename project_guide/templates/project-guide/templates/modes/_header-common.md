This document provides step-by-step instructions for an LLM to assist a human developer in a project. 

## How to Use Project-Guide

### For Developers
{% if pyve_installed %}Pyve manages project-guide for you. From your project root, run `project-guide init` to scaffold the docs, then instruct your LLM as follows in the chat interface: {% else %}After installing project-guide (`pip install project-guide`) and running `project-guide init`, instruct your LLM as follows in the chat interface: {% endif %}

```
Read `{{ target_dir }}/go.md`
```

After reading, the LLM will respond:
1. **First line, always:** "Mode: {{ mode_name }}." (so the developer can verify the active mode at a glance).
2. (optional) "I need more information..." followed by a list of questions or details needed.
  - LLM will continue asking until all needed information is clear.
3. "The next step is ___."
4. "Say 'go' when you're ready." 

For efficiency, when you change modes, start a new LLM conversation. 

### For LLMs

**Modes**
This Project-Guide offers a human-in-the-loop workflow for you to follow that can be dynamically reconfigured based on the project `mode`. Each `mode` defines a focused {{ sequence_or_cycle }} of steps to guide you (the LLM) to help generate artifacts for some facet in the project lifecycle. This document is customized for {{ mode_name }}.

**Approval Gate**
When you have completed the steps, pause for the developer to review, correct, redirect, or ask questions about your work.  

**Rules**
- Work through each step methodically, presenting your work for approval before continuing a cycle. 
- When the developer says "go" (or equivalent like "continue", "next", "proceed"), continue with the next action. 
- If the next action is unclear, tell the developer you don't have a clear direction on what to do next, then suggest something. 
- **Step references include the step's name on first mention in a response.** Naked references like "Step 2" mean nothing to a developer who isn't authoring the mode template. On first mention in a response, pair the number with the step's name in parens — e.g., "Cycle Step 1 (read stories) done; per Step 2 (announce next story), …". Subsequent references in the same response can use the bare number after context is established.
- Never auto-advance past an approval gate—always wait for explicit confirmation. 
- At approval gates, present the completed work and wait. Do **not** propose follow-up actions outside the current mode step — in particular, do not prompt for git operations (commits, pushes, PRs, branch creation), CI runs, or deploys unless the current step explicitly calls for them. The developer initiates these on their own schedule.
- **Scope of authority — structural changes to `stories.md`.** This mode may append new stories under an **existing** `## Phase <Letter>:` heading and edit existing story bodies (status flips, task checkboxes, body prose), but may **not** create new `## Phase` headings, re-theme existing phases, or move stories between phases. Phase creation — the phase heading, its theme paragraph, and the bundle of stories it owns — is the exclusive job of `plan_phase` (or `plan_production_phase` post-1.0). If the current mode's work surfaces scope that feels architecturally distinct from the current phase's theme, **recommend** at the approval gate that the developer run `plan_phase` to draft a new phase; do not unilaterally start one. The developer may agree, redirect, or ask you to draft a phase proposal for their review — still as a recommendation, not an executed action. Subphase headings (`## Subphase <Letter>-N:`) under an existing `## Phase <Letter>:` heading are structural sub-groupings, not new phases; they are created under the same authority that created the phase and may be added by subsequent `plan_production_phase` invocations under that same phase (see `_phase-letters.md` § "Subphases").
- **Sequential, story-by-story documentation.** Every chunk of LLM-produced work that lands in the repo — code, tests, docs, templates — is captured as a single story in `docs/specs/stories.md` under the existing phase, in the order performed. One coherent unit of work → one story → one developer commit. Don't accumulate unrecorded work across multiple turns; don't merge two distinct units into one story for tidiness; don't skip the story because the change feels small. If the work is worth doing in the repo, it is worth a story heading in `stories.md`.
- **Documentation timing.** The default sequence is: write the story with its `[ ]` checklist → execute the tasks → flip them to `[x]` → present at the approval gate. The **`debug` exception** is the only legitimate inversion: when the root cause is unknown until exploration, the sequence becomes explore → reproduce → small-scope fix → write the story (Step 5). Either way, **the story exists on disk by the time the cycle reaches its approval gate.** Entering a gate with undocumented work is not in scope for any mode.
- **Spikes for uncertainty reduction.** When the path forward is uncertain — the design choice is non-obvious, the integration boundary is unproven, the fix path may not exist — document the work as a **spike**: a time-boxed, throwaway effort whose deliverable is the documented outcome (decision / pattern / hypothesis), not production code. Three flavors are recognized: **integration spike** (will external systems connect?), **architectural spike** (will this design work?), **investigation spike** (is there a viable path at all?). Full definitions, triggers, and placement rules live in `developer/best-practices-guide.md` § "Hello World First — Spike Early, Spike Often." Picking a spike is a legitimate action when the next step is genuinely unclear — don't fabricate a confident implementation when the right move is to scope the uncertainty first.
- **Approval-gate documentation handoff.** Every approval gate presents two things together: (a) the story (or stories) reflecting the current completion state — `[x]` for done, `[ ]` for outstanding, with a one-line note on any in-progress items — and (b) the list of files changed with line references. If you reach a gate with work that is not yet captured in a story, **write or update the story before pausing**, not after the developer asks. The handoff is for a developer returning to the conversation with reduced context; it must independently name what was done, what remains, and what decision is being asked for. The story is the artifact; do not defer authoring it to the developer.
- After compacting memory, re-read this guide to refresh your context.
- Before recording a new memory, reflect: is this fact project-specific (belongs in `docs/specs/project-essentials.md`) or cross-project (belongs in LLM memory)? Could it belong in both? If project-specific, add it to `project-essentials.md` instead of or in addition to memory.
- When creating any new source file, add a copyright notice and license header using the comment syntax for that file type (`#` for Python/YAML/shell, `//` for JS/TS, `<!-- -->` for HTML/Svelte). Check this project's `project-essentials.md` for the specific copyright holder, license, and SPDX identifier to use.
- **Bundled artifact templates** live at `docs/project-guide/templates/artifacts/` in this project (installed by `project-guide init`, refreshed by `project-guide update`). When a mode step references an artifact template by name (e.g. `concept.md`, `stories.md`, `project-essentials.md`), that is the directory to read from — do not search the filesystem, the Python install location, or `site-packages`.
- **Files under `docs/project-guide/` are install output, not source.** Static files are regenerated by `project-guide update`; `go.md` is dynamically regenerated on every `project-guide mode` invocation. Hand-edits are silently lost on the next sync **unless** the file is first marked overridden via `project-guide override <file> "<reason>"` (reverse: `project-guide unoverride <file>`). If you find yourself wanting to edit one of these files, treat it as a substantive conflict — do **not** edit silently. Flag it to the developer and surface the options:
  1. **Override and edit locally** (`project-guide override`) — for project-specific divergence the developer wants to keep.
  2. **File an issue or PR** at https://github.com/pointmatic/project-guide — for changes that would benefit every consumer of project-guide.
  3. **Wait for developer guidance** when the right path isn't obvious.

---
{% if project_essentials or pyve_essentials %}
## Project Essentials
{% if project_essentials %}
{{ project_essentials }}
{% endif %}
{% if pyve_essentials %}
### Pyve Essentials

{{ pyve_essentials }}
{% endif %}
---
{% endif %}
# {{ mode_name }} mode ({{ sequence_or_cycle }})

> {{ mode_info }}
