# Refactor Documentation Artifacts

Migrate existing documentation files into the v2.x format. This covers brand descriptions, the landing page, and MkDocs configuration/pages.

{% include "modes/_header-cycle.md" %}

## Targets

The following documents should be refactored (in order):

1. `{{ spec_artifacts_path }}/descriptions.md` → `{{ spec_artifacts_path }}/brand-descriptions.md` (format from `templates/artifacts/brand-descriptions.md`)
2. `{{ web_root }}/index.html` → updated structure from `document-landing-mode.md`
3. MkDocs configuration (`mkdocs.yml`) and documentation pages (`{{ web_root }}/*.md`)

Skip any document that does not exist. If a document already matches the target format, confirm with the developer and skip.

## Cycle Steps (for each document)

### Step 1: Backup

Move the existing document to a backup:

```
docs/specs/descriptions.md → docs/specs/descriptions_old.md
docs/site/index.html → docs/site/index_old.html
```

For MkDocs files, no backup is needed — they are updated in place.

### Step 2: Read and Extract

Read the old document as the primary source of information. Map its content to the sections defined in the corresponding artifact template or mode template.

**For `descriptions.md` → `brand-descriptions.md`:**
- Map existing description sections to the brand-descriptions artifact template
- Sections: Name, Tagline, Long Tagline, One-liner, Friendly Brief Description, Two-clause Technical Description, Benefits, Technical Description, Keywords, Feature Cards, Usage Notes

**For `index.html`:**
- Extract hero text, feature cards, quick start content
- Map to the structure defined in `document-landing-mode.md`

**For MkDocs:**
- Review `mkdocs.yml` configuration
- Review documentation pages for consistency with new mode system

### Step 3: Fill Gaps

If any sections required by the target format are missing from the old document:

1. Note which sections are missing
2. Ask the developer for the missing information
3. Wait for the developer's response before proceeding

Do not invent content — only use information from the old document or the developer.

### Step 4: Generate New Document

Write the new document using the target format, populated with content from the old document and any developer-provided additions.

### Step 5: Legacy Content

If any information from the old document does not fit into the target format sections, append it to the end:

```markdown
---

## Legacy Content

<content that didn't map to any target section>
```

For HTML files, add legacy content as an HTML comment at the bottom.

If all content mapped cleanly, omit this section.

### Step 6: Present for Approval

Present the completed document to the developer. Show:
- Which sections were populated from the old document
- Which sections required new information from the developer
- Whether a Legacy Content section was added
- For `descriptions.md` → `brand-descriptions.md`: note the filename change

Iterate as needed until the developer approves. Then proceed to the next document in the targets list.

### Step 7: Cleanup

After the developer approves, backup files (`_old.md`, `_old.html`) can be deleted at the developer's discretion. Do not delete them automatically.
