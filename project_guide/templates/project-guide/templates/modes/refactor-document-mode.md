Update existing documentation files because of new features, improvements, or to migrate legacy formats into the v2.x structure. Covers README, brand descriptions, the landing page, and MkDocs configuration.

{% include "modes/_header-cycle.md" %}

## Targets

The following documents may need updating (in order):

1. `README.md` — project README at the repository root
2. `{{ spec_artifacts_path }}/brand-descriptions.md` — artifact template: `docs/project-guide/templates/artifacts/brand-descriptions.md` (installed by `project-guide init`; refreshed by `project-guide update`)
3. `{{ web_root }}/index.html` — project landing page
4. MkDocs configuration (`mkdocs.yml`) and documentation pages (`{{ web_root }}/*.md`)

Skip any document that does not exist. If a document already reflects the current state of the project, confirm with the developer and skip.

**Note:** If the project has a legacy `{{ spec_artifacts_path }}/descriptions.md`, it should be migrated to `brand-descriptions.md` using the artifact template format.

## Session Story (author once, before the per-document cycle)

Per `_header-common.md` Rule 1 (Sequential, story-by-story documentation), every refactor session is captured as a **single story** in `docs/specs/stories.md` under the existing phase — the rewrites across README / brand-descriptions / landing page / MkDocs collectively are *one* unit of work that the developer commits as one PR. Per `_phase-letters.md`'s "Inserting a new story" rules, the default insertion is Append (next sequential top-level ID under the current phase); refactor sessions never create new phase headings (Rule: Scope of authority).

**When:** after Step 1 (Understand the Change) of the first document establishes which documents will be touched and why; before Step 2 (Backup) of that document.

**How:**

1. Pick the next sequential top-level story ID under the current phase (Append default).
2. Author the heading: `### Story <id>: Refactor user-facing docs (<brief reason>) [Planned]`. The `(<brief reason>)` captures the developer's Step-1 answer in 4–8 words (e.g., `v2.x release messaging update`, `legacy descriptions.md migration`, `MkDocs config refresh`).
3. Write a checklist: one `[ ]` task per document that will be touched in this session (only documents that actually need work — skip any the developer confirms are current). Use bare-form task names: `Refactor README.md (gap: ...)`, `Refactor brand-descriptions.md (...)`, `Refactor docs/site/index.html (...)`, `Refresh MkDocs config and pages`.
4. Present the planned heading + checklist to the developer for confirmation. Adjust per their feedback. Then begin the per-document cycle below.

**Version assignment** is deferred to the developer at the session gate — pure documentation polish typically omits the version (rides the next code-story release per Version Cadence); refactors that surface new user-facing features (e.g., README rewrite to announce a new capability shipping in this release) may take a minor bump or be folded into that capability's own version bump.

## Cycle Steps (for each document)

### Step 1: Understand the Change

Ask the developer what needs updating and why. This could be:
- **New features or improvements** — documentation needs to reflect new capabilities, updated descriptions, or revised messaging
- **Legacy migration** — the document predates the v2.x format and needs restructuring (e.g., `descriptions.md` → `brand-descriptions.md`)

**Note:** the first document's Step 1 doubles as the session-scope conversation. After completing this step for the first document, **author the session story** (see "Session Story" section above) before proceeding to Step 2 for any document.

### Step 2: Backup

Copy the existing document to a backup before making changes:

```
README.md → README_old.md
docs/specs/brand-descriptions.md → docs/specs/brand-descriptions_old.md
docs/site/index.html → docs/site/index_old.html
```

For MkDocs configuration files, no backup is needed — they are updated in place.

This protects against uncommitted work being overwritten.

### Step 3: Read and Extract

Read the old document as the primary source of information. For documents with artifact templates, read the corresponding template to understand the target structure.

**For `README.md`:**
- Extract project description, installation instructions, usage examples, badges
- Update to reflect current features and version

**For `brand-descriptions.md`:**
- Map to artifact template sections: Name, Tagline, Long Tagline, One-liner, Friendly Brief Description, Two-clause Technical Description, Benefits, Technical Description, Keywords, Feature Cards, Usage Notes

**For `index.html`:**
- Extract hero text, feature cards, quick start content

**For MkDocs:**
- Review `mkdocs.yml` configuration and documentation pages for consistency

Note what needs to change based on the developer's instructions from Step 1.

### Step 4: Fill Gaps

If any sections required by the target format are missing or need new content:

1. Note which sections are missing or outdated
2. Ask the developer for the missing information
3. Wait for the developer's response before proceeding

Do not invent content — only use information from the old document or the developer.

### Step 5: Generate Updated Document

Write the updated document using the target format, incorporating:
- Existing content that is still accurate
- Updates based on the developer's instructions
- Any new information provided by the developer

### Step 6: Legacy Content

If any information from the old document does not fit into the target format sections, append it to the end:

```markdown
---

## Legacy Content

<content that didn't map to any target section>
```

For HTML files, add legacy content as an HTML comment at the bottom.

If all content mapped cleanly, omit this section.

### Step 7: Present for Approval

Present the completed document to the developer. Show:
- What changed and why
- Which sections were preserved, updated, or added
- Whether a Legacy Content section was added
- For legacy migrations: note any filename changes (e.g., `descriptions.md` → `brand-descriptions.md`)

Iterate as needed until the developer approves. Then proceed to the next document in the targets list.

### Step 8: Cleanup

After the developer approves, backup files (`_old.md`, `_old.html`) can be deleted at the developer's discretion. Do not delete them automatically.

## Session Close: Mark Story [Done] and Present at the Session-Level Gate

After every targeted document has completed its per-document cycle (or has been deliberately skipped at the session's start), close out the session story.

Per `_header-common.md` Rule 4 (Approval-gate documentation handoff), every cycle ends with a session-level handoff to the developer that pairs (a) the story reflecting current completion state with (b) the files changed.

1. Return to `docs/specs/stories.md` and locate the session story authored after Step 1 of the first document.
2. Flip every `[ ]` task in its checklist to `[x]`. If any task was abandoned mid-session (e.g., a document the developer ultimately decided not to refactor), mark it `[x]` with a one-line note in the body explaining the deferral, or remove the task and note the change in the story body.
3. Change the story's status suffix from `[Planned]` to `[Done]`.
4. If the developer indicated at session start that the refactor warrants a version bump (typically when the doc updates announce new user-facing features), add the bump-and-CHANGELOG tasks to the checklist now and execute them per the standard Version Cadence rule. Pure documentation polish omits the bump (rides the next code-story release).
5. **Present the session story at the gate.** Name each document rewritten, any Legacy Content sections that were added, any filename changes (e.g., `descriptions.md` → `brand-descriptions.md`), and the version bump (or its absence). The developer commits the refactor session as one PR/commit referencing the story ID — do **not** propose the commit yourself (per `_header-common.md` Rule 5; approval-gate discipline).

This is the session-level gate, distinct from the per-document gates at Step 7 of each document's cycle. Once approved, this cycle ends.
