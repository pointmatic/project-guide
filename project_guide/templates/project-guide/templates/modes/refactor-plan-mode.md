Rewrite or update existing planning documents because of new features, improvements, or to migrate legacy formats into the v2.x artifact template structure.

{% include "modes/_header-cycle.md" %}

## Targets

The following documents may need updating (in order):

1. `{{ spec_artifacts_path }}/concept.md` — artifact template: `docs/project-guide/templates/artifacts/concept.md`
2. `{{ spec_artifacts_path }}/features.md` — artifact template: `docs/project-guide/templates/artifacts/features.md`
3. `{{ spec_artifacts_path }}/tech-spec.md` — artifact template: `docs/project-guide/templates/artifacts/tech-spec.md`

The artifact templates above are installed by `project-guide init` and refreshed by `project-guide update` — read them directly from the path shown.

Skip any document that does not exist. If a document already reflects the current state of the project, confirm with the developer and skip.

## Session Story (author once, before the per-document cycle)

Per `_header-common.md` Rule 1 (Sequential, story-by-story documentation), every refactor session is captured as a **single story** in `docs/specs/stories.md` under the existing phase — the rewrites across concept/features/tech-spec plus the project-essentials revisit collectively are *one* unit of work that the developer commits as one PR. Per `_phase-letters.md`'s "Inserting a new story" rules, the default insertion is Append (next sequential top-level ID under the current phase); refactor sessions never create new phase headings (Rule: Scope of authority).

**When:** after Step 1 (Understand the Change) of the first document establishes which documents will be touched and why; before Step 2 (Backup) of that document.

**How:**

1. Pick the next sequential top-level story ID under the current phase (Append default).
2. Author the heading: `### Story <id>: Refactor planning docs (<brief reason>) [Planned]`. The `(<brief reason>)` captures the developer's Step-1 answer in 4–8 words (e.g., `Phase Q feature additions`, `v2.x artifact migration`, `scope reshape for new ML backend`).
3. Write a checklist: one `[ ]` task per document that will be touched in this session (only documents that actually need work — skip any the developer confirms are current), plus one `[ ]` task for the Final Step project-essentials revisit if it will fire. Use bare-form task names: `Refactor concept.md (gap: ...)`, `Refactor features.md (...)`, `Refactor tech-spec.md (...)`, `Revisit project-essentials.md`.
4. Present the planned heading + checklist to the developer for confirmation. Adjust per their feedback. Then begin the per-document cycle below.

**Version assignment** is deferred to the developer at the session gate — pure prose restructure with no behavioral implications omits the version (rides the next code-story release per Version Cadence); refactors that surface user-visible feature changes via the doc updates may take a minor bump.

## Cycle Steps (for each document)

### Step 1: Understand the Change

Ask the developer what needs updating and why. This could be:
- **New features or improvements** — sections need to reflect new capabilities, architecture changes, or revised scope
- **Legacy migration** — the document predates the v2.x artifact template format and needs restructuring

**Note:** the first document's Step 1 doubles as the session-scope conversation. After completing this step for the first document, **author the session story** (see "Session Story" section above) before proceeding to Step 2 for any document.

### Step 2: Backup

Copy the existing document to `<doc_name>_old.md` before making changes:

```
docs/specs/concept.md → docs/specs/concept_old.md
```

This protects against uncommitted work being overwritten.

### Step 3: Read and Extract

Read the old document as the primary source of information. Read the corresponding artifact template at `docs/project-guide/templates/artifacts/<doc_name>.md` to understand the target structure and required sections.

Map the old document's content to the artifact template sections. Note what needs to change based on the developer's instructions from Step 1.

### Step 4: Fill Gaps

If any sections required by the artifact template are missing or need new content:

1. Note which sections are missing or outdated
2. Ask the developer for the missing information
3. Wait for the developer's response before proceeding

Do not invent content — only use information from the old document or the developer.

### Step 5: Generate Updated Document

Write the updated document using the artifact template structure, incorporating:
- Existing content that is still accurate
- Updates based on the developer's instructions
- Any new information provided by the developer

### Step 6: Legacy Content

If any information from the old document does not fit into the artifact template sections, append it to the end of the new document:

```markdown
---

## Legacy Content

<content that didn't map to any template section>
```

If all content mapped cleanly, omit this section.

### Step 7: Present for Approval

Present the completed document to the developer. Show:
- What changed and why
- Which sections were preserved, updated, or added
- Whether a Legacy Content section was added

Iterate as needed until the developer approves. Then proceed to the next document in the targets list.

### Step 8: Cleanup

After the developer approves, the `_old.md` backup can be deleted at the developer's discretion. Do not delete it automatically.

## Final Step: Revisit Project Essentials

After all document cycles are complete, run this step **once** (not per-document) to refresh `docs/specs/project-essentials.md` with any must-know facts the refactor introduced. This is distinct from the per-document cycle above — `project-essentials.md` is freeform and short, and asking about it once at the end gives the developer a chance to capture cross-document changes.

### Step F.1: Check for Existing File

Check whether `docs/specs/project-essentials.md` exists:

- **If it exists**: this is the **modify** path. Read the current content and keep it in mind while asking the prompt below.
- **If it does NOT exist**: this is the **create** path. This is especially common for legacy projects being migrated to the v2.x artifact structure — they are the highest-value case for project-essentials capture, because none of their conventions have been written down. Be especially explicit in the prompt below: the developer may never have articulated these rules even to themselves.

### Step F.2: Ask the Refactor-Revisit Prompt

Ask the developer whether the refactor introduced any new must-know facts that future LLMs should know to avoid blunders. Put these **concrete worked examples** in front of the developer — not abstract category names — because a refactor often touches things the developer has already internalized and forgotten they're non-obvious:

- **Switched or added an environment manager.** Did the refactor adopt or replace a tool like `uv`, `poetry`, or `hatch`? If so, capture the canonical Python invocation and dev-tool install commands. *Example:* "We switched from `poetry` to `hatch`. Canonical runtime invocation is now `hatch run python ...`; dev tools run via `hatch run test:pytest`. Do NOT use `poetry run` — the `pyproject.toml` still has leftover poetry config but poetry is no longer installed." **Note:** if the refactor adopted `pyve`, the canonical pyve rules are auto-rendered from the bundled `pyve-essentials.md` artifact — do NOT duplicate them into `project-essentials.md`. Capture only pyve-related facts that are **specific to this project** (e.g., migration-in-progress quirks, leftover config from a former tool, or local conventions beyond the bundled defaults).
- **Split runtime from dev environment.** Did the refactor move dev tools (pytest, ruff, mypy) out of the main venv into a dedicated testenv? If so, capture which commands target which env, and explicitly note the **anti-pattern** to avoid. *Example:* "Dev tools live in `.tox/dev/venv/`, not `.venv/`. Use `tox -e dev -- pytest` for tests, `tox -e dev -- mypy` for type-check. **Never** run `pip install -e '.[dev]'` — that pollutes the runtime venv and breaks the isolation contract." (For pyve projects, this split is already covered by the bundled `pyve-essentials.md` — only capture project-specific deviations.)
- **Renamed module or moved source-of-truth.** Did the refactor move a file that looks hand-edited but is actually generated or installed from elsewhere? Capture the source-of-truth path and the installed-copy path so the LLM doesn't edit the copy. *Example:* "Template source moved from `docs/guides/` to `project_guide/templates/project-guide/`. The `docs/project-guide/` directory is now an installed copy — NEVER hand-edit files there."
- **Changed domain conventions.** Did the refactor change how domain values are represented? *Example:* "Money representation changed from float dollars to integer cents. All new code must use `int` for money; the old `Decimal`-based `money_old.py` module is deprecated but not yet removed."
- **New auto-generated or hidden-coupling files.** Did the refactor introduce a build step that regenerates a file, or a pair of files that must stay in sync? *Example:* "`docs/project-guide/go.md` is re-rendered by `project-guide mode <name>`. Never hand-edit it — run `project-guide mode default` to regenerate."
- **Principle:** If the refactor introduced a fork-in-the-road where the *wrong* choice still "works" (runs, compiles, passes some tests), that is a project-essential. The goal is to prevent future LLMs from random-walking to a legitimate-looking-but-wrong answer.

**Skip if there are none.** If the refactor genuinely did not introduce any new must-know facts (pure doc-restructure with no tool/architecture/convention change), confirm with the developer and skip this step entirely.

### Step F.3: Generate or Update the File

Depending on Step F.1's branch:

- **Create path**: Generate a new `docs/specs/project-essentials.md` from the artifact template at `docs/project-guide/templates/artifacts/project-essentials.md` (installed by `project-guide init`; refreshed by `project-guide update`). The **File header conventions** section is mandatory baseline content — pre-fill `<YEAR>`, `<OWNER>`, and `<LICENSE>` from the project's `LICENSE` file and `pyproject.toml` (or equivalent manifest) and remove the trailing TODO note. Do **not** ask the developer whether to include the headers — the question is only ever about *additional* facts (gathered in Step F.2). For legacy projects, this is often the first time these rules have been written down — take the time to capture them properly. Present to the developer for approval and iterate as needed.
- **Modify path**: Read the existing `docs/specs/project-essentials.md`, integrate the new facts from Step F.2, and write the updated file. Preserve existing content that is still accurate; update content that the refactor has changed; add new sections for new categories.

In both paths, follow the artifact template's heading convention: **do NOT include a top-level `#` heading** (the rendered `go.md` wrapper provides `## Project Essentials`), and use `###` for subsection headings so they nest correctly.

### Step F.4: Approval

Present the completed (or updated) `project-essentials.md` to the developer for approval. Show:
- What was added (new facts from the refactor)
- What was modified (existing facts the refactor invalidated)
- What was preserved (existing facts the refactor did not touch)

Iterate as needed. Once approved, proceed to Step F.5.

### Step F.5: Close the Session Story and Present at the Session-Level Gate

Per `_header-common.md` Rule 4 (Approval-gate documentation handoff), every cycle ends with a session-level handoff to the developer that pairs (a) the story reflecting current completion state with (b) the files changed.

1. Return to `docs/specs/stories.md` and locate the session story authored after Step 1 of the first document.
2. Flip every `[ ]` task in its checklist to `[x]`. If any task was abandoned mid-session (e.g., a document the developer ultimately decided not to refactor), mark it `[x]` with a one-line note in the body explaining the deferral, or remove the task and note the change in the story body.
3. Change the story's status suffix from `[Planned]` to `[Done]`.
4. If the developer indicated at session start that the refactor warrants a version bump (typically a minor bump when user-visible feature changes surface via the doc updates), add the bump-and-CHANGELOG tasks to the checklist now and execute them per the standard Version Cadence rule. Pure prose restructure with no behavioral implications omits the bump (rides the next code-story release).
5. **Present the session story at the gate.** Name each document rewritten, the project-essentials outcome (added / modified / preserved / skipped), any Legacy Content sections that were added, and the version bump (or its absence). The developer commits the refactor session as one PR/commit referencing the story ID — do **not** propose the commit yourself (per `_header-common.md` Rule 5; approval-gate discipline).

This is the session-level gate, distinct from the per-document gates at Step 7 of each document's cycle. Once approved, this cycle ends.
