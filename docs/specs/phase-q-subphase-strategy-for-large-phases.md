# Change request: Subphase strategy for large/complex phases

**Target repo:** [`project-guide`](https://github.com/pointmatic/project-guide)
**Consumption:** `pyve` (and any `project-guide` consumer) invokes `project-guide mode plan_production_phase` (or `plan_phase`) when scoping a new phase. The current templates assume a phase can be fully decomposed into stories in one planning session. For genuinely large phases — major-version cutovers, architectural pivots, multi-component re-platformings — that assumption breaks down, and the resulting workaround (the LLM inventing structure on the fly) is ad-hoc, inconsistent across sessions, and requires the developer to bootload the convention into every relevant LLM conversation.

---

## Problem statement

When a single phase is too large to draft every story up front, the current `plan_phase` / `plan_production_phase` templates offer no idiomatic structure for partial decomposition. Concrete consequences observed in a real planning session:

- **Bootloading burden on the developer.** Drafting Pyve's Phase N (`Pyve 3.0 — Plugin Architecture & Named Envs`, ~7 cohesive sub-units of work) required the developer to manually instruct the LLM: "predetermine major sub-units; only break the first one into stories; add a preamble so future LLM sessions don't get confused; story letters continue monotonically across sub-units; sub-unit headings use `##` (same level as the phase); use the hyphenated `N-1`/`N-2` form so sub-unit IDs don't collide with the story-ID scheme; cap story IDs at 3 levels of nesting." None of that is in the templates today.
- **Inconsistent shape across sessions.** The next `plan_production_phase` invocation (for the same project or a different one) starts fresh; the same conversation has to happen again. Pattern drift is guaranteed.
- **Phase-boundary rule conflict.** `_header-common.md`'s *Scope of authority — structural changes to `stories.md`* rule forbids creating new `## Phase` headings outside `plan_phase` / `plan_production_phase`. Without an articulated subphase concept, the LLM has no way to distinguish "I'm adding internal structure to my phase" from "I'm creating a new phase" — the natural fallback (jumping to `Phase O` for what is conceptually still Phase N) corrupts the phase-letter sequence.
- **Multi-release coupling.** Large phases sometimes need to ship more than one release tag (e.g., Pyve Phase N ships v3.0.0 after the architectural cutover and v3.1.0 after a post-release UX polish subphase). The current Version Cadence rule "one phase = one bundled release at end-of-phase" doesn't acknowledge this; the workaround is again ad-hoc developer instruction.

---

## Proposed change

Add a **subphase decomposition** option to `plan_production_phase` (and optionally `plan_phase`) for phases that are too large for single-session story breakdown. The pattern is **opt-in**: small/medium phases continue to be drafted as a single block exactly as today. The pattern becomes default behavior only when the developer (or the LLM's judgment, ratified by the developer) signals "this phase is too big."

### The subphase pattern (formalized)

A **subphase** is a structural grouping of related stories within a phase. Subphases are sub-units of *one* phase — they do not create new phases, they do not get their own concept/features/tech-spec sections, and they do not participate in the phase-letter sequence (which remains `A, B, …, Z, AA, …` per `_phase-letters.md`).

**Subphase identifiers** use arabic numerals with a hyphen separator: `N-1`, `N-2`, …, `N-9`, `N-10`, …. The hyphen separator is deliberate — it cannot collide with story IDs (`N.a`, `N.b`, …) or with the existing sub-numbered story form (`N.m.1`, `N.m.2`, …).

**Story letters continue monotonically across subphases.** If Subphase `N-1` ends at story `N.f`, Subphase `N-2` starts at story `N.g`. Subphases are structural markers in `stories.md`, not part of the story-ID scheme. Story sub-letters reset only at the **phase** boundary (existing rule), never at a subphase boundary.

**Story breakdown is per-subphase.** When subphases are used, the initial `plan_production_phase` session drafts stories only for **Subphase 1**. Subsequent subphases carry only a description paragraph and a deferred-story marker. Each subsequent subphase's stories are drafted in **its own future `plan_production_phase` session**, kicked off immediately before that subphase's implementation begins. The trigger to re-enter `plan_production_phase` is the start of a new subphase, not the start of a new phase — re-entering for a subphase is the canonical mid-phase re-invocation pattern.

**Subphase headings** use `##` (same level as the phase heading in `stories.md`), making them peers of `## Future` and visible to the same parsers that already handle the phase-letter sequence. The phase heading carries a **structural preamble** above the first subphase explaining (a) why the phase is subphased, (b) the story-ID continuation rule, and (c) any multi-release exception (see below).

### Multi-release subphases (optional sub-pattern)

A large phase may ship more than one release tag — for example, an architectural cutover ships at the end of Subphase N-7 as `v3.0.0`, and a follow-on UX polish subphase ships at the end of Subphase N-8 as `v3.1.0`. This is an **explicit exception** to the Version Cadence rule "one phase = one bundled release at end-of-phase" and must be documented in the phase plan with rationale. Releases that fit the single-bundle pattern are preferred; multi-release subphases exist only because some work is genuinely conceptually-within-the-phase but should not block the primary release tag.

### Trigger heuristics

The mode should suggest subphasing when **any** of the following hold:

- The developer says "this phase is huge" / "this is a major-version cutover" / "this involves multiple coupled re-platformings."
- The gap-analysis table has more than ~7 substantively distinct rows.
- The technical-changes section spans more than ~4 architectural layers (new modules, new contracts, renamed core seams, …).
- The anticipated-breaking-changes table has more than ~4 substantive items.
- The version-bump target is `vX+1.0.0` (major) **and** the developer signals there's "polish that should not block the major."

When subphasing is suggested, the LLM presents the proposed subphase decomposition to the developer for approval **before** drafting any stories. The developer may redirect (collapse subphases, split further, reorder).

---

## Motivation

- **Captured during Pyve Phase N planning, 2026-06-01.** The session drafted [docs/specs/phase-n-plugin-architecture-named-envs-plan.md](../phase-n-plugin-architecture-named-envs-plan.md) and the corresponding Phase N section of [docs/specs/stories.md](../stories.md). The phase decomposes into 8 subphases, ships two releases (`v3.0.0` after N-7 and `v3.1.0` after N-8), and only Subphase N-1's 10 stories were drafted in that initial session.
- **The pattern is general.** Every major-version cutover (`v2.x → v3.0`, `v3.x → v4.0`) is a candidate; multi-component re-platformings (e.g., switching language runtimes, replacing a primary backend) are candidates; phases that combine "architectural change" with "post-release polish" benefit from the multi-release sub-pattern.
- **Removes developer-side bootloading.** Codifying the pattern means the next consumer who hits a large phase gets the structure for free, instead of having to articulate it from scratch.
- **Preserves the simple case.** Small/medium phases continue to use the current single-block decomposition with zero changes to behavior or output.

---

## Suggested template changes

### `templates/modes/plan-production-phase-mode.md`

Primary target. Insert a new **Step 4a (Subphase decomposition — optional)** between the current Step 4 (Generate a phase plan document) and Step 5 (Breaking-change negotiation):

```markdown
4a. **Subphase decomposition (optional).** If the phase is large enough
    that drafting every story up front is infeasible, propose a subphase
    decomposition to the developer. Trigger heuristics: …[list]…

    When subphasing is chosen:
    - The plan document's "Out of scope" / "Subphase overview" section
      enumerates each subphase (`X-1`, `X-2`, …) with a one-paragraph
      scope summary and an explicit "story breakdown deferred to its own
      plan_production_phase session" marker for subphases beyond the first.
    - The initial planning session drafts stories only for Subphase 1.
    - The phase plan documents a "multi-release exception" line if any
      subphase ships a release separate from the phase's primary release
      tag (e.g., a polish subphase shipping a minor bump after the major).
    - Re-entering `plan_production_phase` mid-phase, to draft a later
      subphase's stories, is the canonical pattern — not a misuse.

    Skip this step entirely if the phase is small/medium; the existing
    single-block decomposition (Steps 5–8 below) applies as today.
```

Also update Step 7 (Add a new phase section and stories to `stories.md`) to reference the subphase layout when the previous step opted in.

### `templates/modes/_phase-letters.md`

Add a new section after **Story sub-letters** (before **Sub-numbered stories**):

```markdown
### Subphases (structural grouping within a phase)

When a phase is too large to draft every story in one planning session,
it may be decomposed into **subphases** — sub-units of one phase. Subphases
are structural markers in `stories.md`, not part of the story-ID scheme.

- **Subphase IDs** use arabic numerals with a hyphen separator: `N-1`,
  `N-2`, …, `N-9`, `N-10`, ….
- **Subphase headings** use `##` (same level as the phase heading).
- **Story letters continue monotonically across subphases.** If Subphase
  `N-1` ends at story `N.f`, Subphase `N-2` starts at story `N.g`. Story
  sub-letters reset only at the phase boundary — never at a subphase
  boundary.
- **Story breakdown is per-subphase.** The initial `plan_production_phase`
  session drafts stories only for Subphase 1; subsequent subphases get
  their stories drafted in their own future `plan_production_phase`
  sessions immediately before that subphase's work begins.
- **3-level story-ID depth limit holds.** A story like `N.b` may still
  bundle into `N.b.1`, `N.b.2`, …, but never `N.b.1.1`. Subphase IDs do
  not consume a story-ID level — they live in a separate namespace.

See `plan_production_phase` Step 4a for when to introduce subphases.
```

### `templates/modes/_header-common.md`

Update the **Scope of authority — structural changes to `stories.md`** rule to clarify that adding `## Subphase X-N:` headings is allowed in `plan_production_phase` (and `plan_phase`) for phases that opted into subphasing — it is *not* the same as creating a new `## Phase` heading, which remains exclusive to those modes anyway. Add one sentence:

```markdown
Subphase headings (`## Subphase X-N:`) under an existing `## Phase X:`
heading are structural sub-groupings, not new phases; they are created
under the same authority that created the phase and may be added by
subsequent `plan_production_phase` invocations under the same phase.
```

### `templates/modes/plan-phase-mode.md`

Add a parenthetical to Step 4 noting that subphasing is **available pre-1.0 too** but rarely needed — pre-1.0 phases tend to be small enough to fit a single planning session, so the default is to skip subphasing. One sentence:

```markdown
For phases large enough to warrant decomposition, the **subphase pattern**
described in `plan_production_phase` Step 4a applies here too — but pre-1.0
phases rarely reach that threshold; the default is to draft every story in
one session.
```

### `templates/modes/plan-stories-mode.md`

No change recommended. `plan_stories` is for *initial* story planning of a project that does not yet have a story plan; the subphase pattern applies to later, larger phases.

### `templates/modes/refactor-plan-mode.md`

No change recommended. `refactor_plan` does not create phases.

### `templates/modes/_header-cycle.md` / `_header-sequence.md`

No change recommended. These are inclusion partials for cycle/sequence headers; subphasing is a structural feature, not a cycle/sequence change.

---

## Compatibility notes

- **Additive.** Every change is opt-in: phases that don't subphase produce identical output to today. No existing `stories.md` is invalidated; no existing phase plan is invalidated.
- **Parser-safe.** Subphase headings use `##` (already a heading level the rendered docs handle); subphase IDs use a hyphen-separated form (`N-1`) that does not collide with story IDs (`N.a`), sub-numbered stories (`N.m.1`), or phase letters (`N`, `AA`).
- **Consumers** that already grep for `## Phase` continue to work — they will not see false matches against `## Subphase X-N:`.
- **Consumers** that grep for `### Story X.y` continue to work — story letters retain their existing format; subphases live one level up.
- **No tooling rename required.** `project-guide bump-version`, the `archive_stories` mode, and downstream version detection continue to operate on the phase boundary, not the subphase boundary.

---

## Pyve-side follow-up

After upstream release `vX.Y.Z` with this change:

- Update [pyve.sh](../../../pyve.sh) only if the consumed version string changes (no behavior change expected).
- Future Pyve phases that hit the subphase trigger heuristics will use the codified pattern instead of the ad-hoc instruction set carried in Phase N planning.
- The Phase N artifacts ([phase-n-plugin-architecture-named-envs-plan.md](../phase-n-plugin-architecture-named-envs-plan.md), [stories.md](../stories.md) Phase N section) become the worked example referenced from the upstream template.
- Optional: derive a minimum project-guide version comment alongside the existing `--no-input ≥ 2.2.3` citation in [lib/utils.sh](../../../lib/utils.sh) if any consumer-side gate is added that depends on the upstream change.
