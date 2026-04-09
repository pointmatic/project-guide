# Refactor Planning Artifacts

Migrate existing planning documents (`concept.md`, `features.md`, `tech-spec.md`) into the v2.x artifact template format. This preserves all information while restructuring it into the standardized sections.

{% include "modes/_header-cycle.md" %}

## Targets

The following documents should be refactored (in order):

1. `{{ spec_artifacts_path }}/concept.md` → format from `templates/artifacts/concept.md`
2. `{{ spec_artifacts_path }}/features.md` → format from `templates/artifacts/features.md`
3. `{{ spec_artifacts_path }}/tech-spec.md` → format from `templates/artifacts/tech-spec.md`

Skip any document that does not exist. If a document already matches the artifact template format, confirm with the developer and skip.

## Cycle Steps (for each document)

### Step 1: Backup

Move the existing document to `<doc_name>_old.md`:

```
docs/specs/concept.md → docs/specs/concept_old.md
```

### Step 2: Read and Extract

Read the old document as the primary source of information. Map its content to the sections defined in the corresponding artifact template.

For reference, read the artifact template at `templates/artifacts/<doc_name>.md` to understand the target structure and required sections.

### Step 3: Fill Gaps

If any sections required by the artifact template are missing from the old document:

1. Note which sections are missing
2. Ask the developer for the missing information
3. Wait for the developer's response before proceeding

Do not invent content — only use information from the old document or the developer.

### Step 4: Generate New Document

Write the new document using the artifact template structure, populated with content from the old document and any developer-provided additions.

### Step 5: Legacy Content

If any information from the old document does not fit into the artifact template sections, append it to the end of the new document:

```markdown
---

## Legacy Content

<content that didn't map to any template section>
```

If all content mapped cleanly, omit this section.

### Step 6: Present for Approval

Present the completed document to the developer. Show:
- Which sections were populated from the old document
- Which sections required new information from the developer
- Whether a Legacy Content section was added

Iterate as needed until the developer approves. Then proceed to the next document in the targets list.

### Step 7: Cleanup

After the developer approves, the `_old.md` backup can be deleted at the developer's discretion. Do not delete it automatically.
