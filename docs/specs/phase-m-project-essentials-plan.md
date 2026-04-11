# Phase M: Project Essentials Integration Plan

> Originally drafted as Phase L on 2026-04-10 as a follow-up to Phase K story K.h. Renumbered to **Phase M** on 2026-04-11 when a new Phase L (`project-guide init --no-input` mode) was inserted ahead of it. At the same time, the former Phase K stories K.h and K.i were moved out of Phase K and absorbed into this phase as M.a and M.b, because they are thematically part of the project-essentials integration rather than the K release-lifecycle work.
>
> This plan describes how the `project-essentials.md` artifact is established (placeholder + render hook + render-time validation), then how the three planning modes (`plan_tech_spec`, `refactor_plan`, `plan_phase`) populate and maintain it so the artifact stays useful over the life of any project — not just this one.

## Mini-Concept (Why)

The `project-essentials.md` artifact is a per-project file that captures must-know facts future LLMs need to avoid blunders: workflow rules, architecture quirks, dogfooding/meta notes, hidden coupling. Phase M establishes it and wires it in end-to-end:

1. **Placeholder + render hook** (M.a) creates the artifact template, teaches `render.py` to read it, and injects it into every rendered mode via `_header-common.md` as a `## Project Essentials` section. Empty/missing renders cleanly.
2. **Render-time validation** (M.b) turns the render pipeline into a hard gate against unrendered `{{ placeholder }}` strings anywhere in the output. Catches missed intent, typos, and removed `{% if %}` guards across all templates, not just `_header-common.md`.
3. **Planning-mode wiring** (M.c–M.e) teaches `plan_tech_spec`, `refactor_plan`, and `plan_phase` to populate and maintain the artifact at the three points in the project lifecycle where must-know facts typically change.
4. **Documentation pass** (M.f) updates the artifacts catalogue, CHANGELOG, and README.

Without M.a/M.b, there is nothing to populate. Without M.c/M.d/M.e, the artifact must be hand-crafted by every project and silently rots the moment architecture or workflow shifts. Phase M makes the artifact self-maintaining over the lifecycle.

## Gap Analysis

| Capability | Before Phase M | Needed in Phase M |
|---|---|---|
| `project-essentials.md` artifact template exists | No | Yes — M.a ships the template |
| Render pipeline injects the content into every mode | No | Yes — M.a adds the read + `_header-common.md` hook |
| Rendered output is validated for unrendered placeholders | No — `_LenientUndefined` silently passes them through | Yes — M.b adds a post-render regex scan that raises `RenderError` |
| New projects automatically get prompted to populate it | No | Yes — M.c adds a final step to `plan_tech_spec` |
| Existing projects pick up new must-know facts after architecture shifts | No | Yes — M.d adds a revisit step to `refactor_plan` |
| New phases capture phase-specific gotchas | No | Yes — M.e adds an append prompt to `plan_phase` |
| Legacy projects without the artifact get it created on first refactor/phase | No | Yes — M.d/M.e handle the create case conversationally |

## Feature Requirements (What)

### F1. `project-essentials.md` placeholder artifact and render hook (M.a)

- A new artifact template at `project_guide/templates/project-guide/templates/artifacts/project-essentials.md` with an empty body and a brief comment block describing what belongs there: workflow rules, architecture quirks, domain conventions, hidden coupling, dogfooding/meta notes. An empty file is acceptable.
- `render.py` reads `<spec_artifacts_path>/project-essentials.md` if present and passes the content as the `project_essentials` Jinja2 context variable. Missing or empty file → empty string, no error.
- `_header-common.md` renders a `## Project Essentials` section guarded by `{% if project_essentials %}` so the section is omitted entirely when empty.
- Dogfooded immediately for this project: `docs/specs/project-essentials.md` is populated with the current must-know facts (pyve dual-environment split, template-source-path rule, go.md is auto-rendered).
- **Not** added as a tracked artifact to any mode's `.metadata.yml` yet — that wiring is M.c–M.e's responsibility.

### F2. Render output validation — fail on unrendered placeholders (M.b)

- A post-render validation function in `render.py` that scans the rendered string for any remaining `{{ identifier }}` Jinja-style placeholders (regex: `\{\{\s*[a-zA-Z_]\w*\s*\}\}`).
- If any are found, raise `RenderError` with the placeholder names and a hint: "Check (1) render.py context variables and (2) template variable spellings."
- Called inside `render_go_project_guide` after `template.render(...)` but before `output_path.write_text(...)`.
- This generalizes the M.a regression guard from `{{ project_essentials }}` alone to **all** templates — catching missed intents, typos, and removed `{% if %}` guards project-wide.
- `_LenientUndefined` stays unchanged — its placeholder-passthrough behavior is what makes the validator's job possible.
- **Known limitation documented in a code comment:** templates that want to legitimately emit `{{ var }}` as literal text (e.g., Jinja syntax documentation) will trigger false positives. Not currently a problem; bridge if/when needed.

### F3. `plan_tech_spec` populates `project-essentials.md` (M.c)

- After the developer approves `tech-spec.md`, the mode prompts for project-essentials content with **concrete worked examples** in the prompt — not just abstract category names like "workflow rules" or "architecture quirks". The prompt surfaces specific scenarios (e.g., `pyve run python ...` vs `python -m ...` vs `.venv/bin/python ...`; `pyve testenv --install` vs `pip install -e ".[dev]"`) so the developer is reminded of forks-in-the-road where the wrong choice still "works" but isn't canonical. See Story M.c's checklist for the full example list.
- If the developer provides facts, write them to `docs/specs/project-essentials.md`.
- If the developer has nothing to add, leave the file empty (or skip creation entirely — the render hook handles both).
- The mode declares `project-essentials.md` as a `create` artifact in `.metadata.yml`.

### F4. `refactor_plan` refreshes `project-essentials.md` (M.d)

- The cycle includes a step that asks: "Did any of these refactor changes affect facts that future LLMs must know?"
- The mode handles both cases: file exists (read, modify, write) and file does not yet exist (create from artifact template, then populate).
- The mode declares `project-essentials.md` as a `modify` artifact in `.metadata.yml`.

### F5. `plan_phase` appends to `project-essentials.md` (M.e)

- After phase approval, the mode asks: "Does this phase introduce any new must-know facts?"
- If yes, append (do not overwrite) to `project-essentials.md`.
- The mode handles the create case for legacy projects.
- The mode declares `project-essentials.md` as a `modify` artifact in `.metadata.yml`.

### F6. Self-documenting prompt language

- All three planning modes (M.c, M.d, M.e) use consistent prompt language and consistent example categories so the developer learns what belongs in the file regardless of which mode they happen to use first.
- **Worked examples, not abstract categories.** The prompt names specific anti-patterns the developer (and the LLM) might otherwise commit:
  - *Tool wrapper conventions*: pyve/poetry/hatch/uv invocation forms vs `python -m ...` vs direct `.venv/bin/...`. All execute, but only one is canonical.
  - *Runtime vs dev environment splits*: dedicated test environment vs `pip install -e ".[dev]"` into the runtime venv. Different isolation guarantees.
  - *Source vs installed/generated copies*: editing the installed copy when the source is elsewhere.
- **Underlying principle:** legitimate alternatives exist for each fork, but they should be intentional choices, not a random walk to whatever happens to work first. The `project-essentials.md` content should make the canonical choice unambiguous so future LLMs don't drift.

## Technical Changes (How)

### T1. New artifact template + render-pipeline changes (M.a)

- Create `project_guide/templates/project-guide/templates/artifacts/project-essentials.md`.
- Update `project_guide/render.py` to read `<spec_artifacts_path>/project-essentials.md` if present and pass the content as the `project_essentials` Jinja2 context variable. Default to empty string when missing or empty.
- Update `project_guide/templates/project-guide/templates/modes/_header-common.md`: after the **Rules** section and before the `# {{ mode_name }} mode` heading, render `{% if project_essentials %}## Project Essentials\n\n{{ project_essentials }}\n\n---\n{% endif %}`.
- Tests in `tests/test_render.py`:
  - Rendered output contains `## Project Essentials` when fixture file is non-empty.
  - Rendered output omits the section when fixture file is empty.
  - Rendered output omits the section when fixture file is missing (no error).
  - **Regression guard** (temporary, removed in M.b): rendered output never contains the literal string `{{ project_essentials }}` in any of the above cases. Catches a future edit that removes the `{% if %}` guard, since `_LenientUndefined.__str__` would otherwise render the placeholder verbatim.
- Populate `docs/specs/project-essentials.md` for this project with current must-know facts (dogfooding). This is a one-time action, not a code change.

### T2. Post-render validator (M.b)

- New function in `project_guide/render.py` that scans the rendered string with regex `\{\{\s*[a-zA-Z_]\w*\s*\}\}`.
- If any matches found, raise `RenderError` listing the offending placeholder names plus the "check render.py context variables and template variable spellings" hint.
- Call the validator inside `render_go_project_guide` after `template.render(...)` and before `output_path.write_text(...)`.
- Remove the M.a `{{ project_essentials }}` regression-guard assertion once the general validator is in place (leave a brief comment noting the validator subsumes it).
- Audit existing mode templates and `_header-common.md` to confirm none rely on undefined variables silently passing through. Fix any that do.

### T3. Update `plan-tech-spec-mode.md` (M.c)

- Add a final step after tech-spec approval.
- Step prompts the developer with the four example categories and a "skip if none" option.
- If the developer provides facts, generate `docs/specs/project-essentials.md` from the artifact template with the facts inserted.
- If the developer has nothing, skip generation — the render hook treats missing as empty.

### T4. Update `refactor-plan-mode.md` (M.d)

- Extend the cycle (either as a new dedicated step or as part of Step 1 / Step 7) with a "revisit project-essentials" prompt.
- Mode template logic: check if `docs/specs/project-essentials.md` exists; if yes, read and offer modifications; if no, offer to create.
- Modifications are presented for approval like any other artifact change.

### T5. Update `plan-phase-mode.md` (M.e)

- Add a step after the current Step 6 (phase approval) that asks the developer about new must-know facts the phase introduces.
- Append to `project-essentials.md` if facts are provided. Use a date or phase-letter heading to group facts by source phase if useful (decision deferred to implementation).
- Handle the create case for legacy projects.

### T6. `.metadata.yml` updates (M.c–M.e)

- `plan_tech_spec.artifacts` gets a new entry: `{ file: "{{spec_artifacts_path}}/project-essentials.md", action: create }`.
- `refactor_plan.artifacts` gets: `{ file: "{{spec_artifacts_path}}/project-essentials.md", action: modify }`.
- `plan_phase.artifacts` gets: `{ file: "{{spec_artifacts_path}}/project-essentials.md", action: modify }`.
- **Open question:** the `modify` action's existing semantics may require `files_exist`. For legacy projects, the file may not exist when `refactor_plan` or `plan_phase` first runs. Two resolutions:
  - **Option A** (preferred): the mode template handles existence-checking conversationally — the LLM checks, creates if needed, modifies otherwise. No metadata change required.
  - **Option B**: introduce a `create_or_modify` action type. More work, more validator changes; only worth it if other artifacts also need this semantic.
- Plan assumes Option A. Revisit during M.d implementation if it doesn't feel natural.

### T7. Tests

- M.a: tests listed under T1 above.
- M.b: tests for the validator — undefined variable raises `RenderError` with the placeholder name; all variables defined succeeds; templates with no Jinja variables at all do not raise.
- M.c–M.e: each mode template gets rendering tests that verify the new prompt step appears.

### T8. Documentation (M.f)

- Update artifacts catalogue (wherever `concept.md`, `features.md`, etc. are listed) to include `project-essentials.md`.
- Optional: add a one-line "see also: project-essentials.md" cross-reference from `concept.md` / `features.md` / `tech-spec.md` artifact templates.
- Update CHANGELOG with v2.3.0–v2.3.5 entries.
- Update README if any user-facing wording references the new artifact.

## Out of Scope for Phase M

- A dedicated `refactor_essentials` mode for editing `project-essentials.md` directly. Not needed — the three planning modes cover the lifecycle, and direct editing is always available via a normal text editor.
- A `create_or_modify` action type. Mode templates handle existence-checking conversationally instead. Revisit only if other artifacts develop the same need.
- Validation/linting of `project-essentials.md` content. The artifact is freeform by design.
- Auto-detection of stale essentials (e.g., comparing against last commit). Out of scope; the planning-mode prompts are the maintenance mechanism.
- Migrating other LLM memory entries into `project-essentials.md`. Per-project decision the developer makes when they first run an updated planning mode.
- Support for literal `{{ var }}` strings as rendered output (e.g., Jinja syntax docs). Documented as a known limitation of the M.b validator; bridge if/when a real template needs it.

## Proposed Stories (Phase M)

To be added to `docs/specs/stories.md` immediately following the new Phase L. Versions assume Phase L ships through v2.2.2; Phase M opens at v2.3.0 (minor bump per phase, matching the project's cadence).

- **M.a — v2.3.0** `project-essentials.md` placeholder and render hook *(originally planned as Phase K story K.h)*
- **M.b — v2.3.1** Render output validation — fail on unrendered placeholders *(originally planned as Phase K story K.i)*
- **M.c — v2.3.2** `plan_tech_spec` populates `project-essentials.md`
- **M.d — v2.3.3** `refactor_plan` refreshes `project-essentials.md` (handles create-or-modify conversationally)
- **M.e — v2.3.4** `plan_phase` appends to `project-essentials.md`
- **M.f — v2.3.5** Phase M documentation, CHANGELOG, and artifacts catalogue updates

**Ordering is load-bearing only within two pairs:**

- M.a must ship before M.b (the validator generalizes M.a's regression guard).
- M.a must ship before M.c/M.d/M.e (nothing to populate otherwise).

M.c, M.d, and M.e are mutually independent and can ship in any order within Phase M. The listed order matches the project lifecycle (initial → refactor → per-phase).

No spike. The integration boundary (the `project_essentials` render context variable) is validated by M.a's own tests. Each subsequent story is independent and small.
