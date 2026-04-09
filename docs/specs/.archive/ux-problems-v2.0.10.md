# project-guides: Problems to fix

## Default Mode 

New install: default mode is `plan_concept`. Should be `default`. 

## Templates File Exists Check in Metadata File

The templates filecheck is looking for the code repo path and not the artifacts path. 

The problem appeared when I tried to change mode to `plan_phase`:

```bash
(venv:pyve) pointmatic@Michaels-MB-Pro-M3 pyve % project-guide mode plan_phase
✓ Mode set: plan_phase
  Generate a feature phase prompt, which includes a mini-concept, features, and technical details
  Guide: docs/specs/go-project-guide.md

  Prerequisites not yet met:
    ✗ docs/specs/concept.md
    ✗ project_guide/templates/project-guide/templates/modes/plan-phase-mode.md
```

The `docs/specs/concept.md` missing is valid
The other is not and should be `docs/project-guide/modes/plan-phase-mode.md`

The fix is to update the paths from `{{mode_templates_path}}` to `{{spec_artifacts_path}}`.

## Metadata File Name

Regarding the current metadata file...
- template: `project_guide/templates/project-guide/templates/project-guide-metadata.yml`
- artifact: `docs/project-guide/project-guide-metadata.yml`

Let's simplify the name and hide it:
- template: `project_guide/templates/project-guide/templates/.metadata.yml`
- artifact: `docs/project-guide/.metadata.yml`