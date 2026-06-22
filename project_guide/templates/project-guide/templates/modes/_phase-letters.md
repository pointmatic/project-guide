## Phase and Story ID Scheme

Phase and story IDs use a base-26 letter scheme with no zero. The same scheme applies to both — single letters first, then two-letter combinations, etc. This keeps IDs short while supporting projects of any size, and lets archive boundaries continue the sequence cleanly.

### Phase letters

Phases are labeled `A`, `B`, …, `Z`, then `AA`, `AB`, …, `AZ`, `BA`, …, `ZZ`, then `AAA`, …. The scheme is base-26 with no zero — there is no "phase 0" and `B` follows `A` (not `AB`).

Examples in order: `A`, `B`, …, `Z`, `AA`, `AB`, `AC`, …, `AZ`, `BA`, `BB`, …, `ZZ`, `AAA`, ….

### Story sub-letters

Within a phase, stories use lowercase letters following the same scheme: `A.a`, `A.b`, …, `A.z`, then `A.aa`, `A.ab`, …, `A.az`, `A.ba`, ….

Examples: `A.a`, `A.b`, …, `A.z`, `A.aa`, `A.ab`, ….

### Subphases (structural grouping within a phase)

When a phase is too large to draft every story in one planning session, it may be decomposed into **subphases** — structural sub-groupings within one phase. Subphases live in a separate namespace from story IDs: they group stories without participating in the story-ID scheme, and they do **not** create new phases.

- **Subphase IDs** use arabic numerals with a hyphen separator: `N-1`, `N-2`, …, `N-9`, `N-10`, …. The hyphen is deliberate — it cannot collide with story IDs (`N.a`, `N.b`, …) or with sub-numbered stories (`N.m.1`, `N.m.2`, …).
- **Subphase headings** use `##` (peer of the `## Phase <Letter>:` heading), e.g. `## Subphase N-1: <name>`. This makes them visible to the same parsers that already handle the phase-letter sequence (a grep for `^## Phase ` continues to match phases only; `^## Subphase ` is a distinct anchor).
- **Story letters continue monotonically across subphases.** If Subphase `N-1` ends at story `N.f`, Subphase `N-2` starts at story `N.g`. Story sub-letters reset only at the **phase** boundary — never at a subphase boundary.
- **Story breakdown is per-subphase.** The initial `plan_production_phase` session drafts stories only for Subphase 1. Subsequent subphases get their stories drafted in their own future `plan_production_phase` sessions, kicked off immediately before that subphase's work begins. Re-entering `plan_production_phase` mid-phase to draft a later subphase's stories is the canonical pattern — see `plan-production-phase-mode.md` Step 4a.
- **3-level story-ID depth limit holds.** A story like `N.b` may still bundle into `N.b.1`, `N.b.2`, …, but never `N.b.1.1`. Subphase IDs do not consume a story-ID level — they live in a separate namespace.
- **Multi-release exception.** A large phase may ship more than one release tag (e.g., an architectural cutover ships at the end of Subphase N-7 as `vX+1.0.0`, and a follow-on polish subphase ships at the end of Subphase N-8 as `vX+1.1.0`). This is an explicit exception to the Version Cadence "one phase = one bundled release at end-of-phase" rule and must be documented in the phase plan with rationale. Single-bundle phases remain the preferred shape; multi-release subphases exist only when some work is genuinely conceptually within the phase but should not block the primary release tag.

See `plan_production_phase` Step 4a for the trigger heuristics and the structural-preamble shape inside `stories.md`.

### Sub-numbered stories

A story may carry an optional numeric suffix — `J.m.1`, `J.m.2`, … — appended after the sub-letter. Sub-numbers are flat (no cascading like `J.m.1.1`) and start at `1`. These situations use them:

- **Pre-implementation split (scope too large).** When `J.m`'s scope is judged too large to land as one coherent unit/commit — at planning time, **or** when you open it at implementation time and find it bigger than expected — the heading is split into `J.m.1`, `J.m.2`, … and the bare `J.m` heading is dropped. Sequence becomes `…, J.l, J.m.1, J.m.2, J.n, …`. (Scope is legitimately re-assessed at implementation time, not only at planning time — see the cycle modes' "Story scope & splitting" guidance.)
- **Post-implementation follow-up.** When `J.m` ships but a bug or follow-on feature must land before proceeding to `J.n`, the follow-up is added as `J.m.1` (and may cascade to `J.m.2`, `J.m.3`, …). Sequence becomes `…, J.l, J.m, J.m.1, J.m.2, …, J.n, …`.
- **Ordering convenience.** Sub-numbering is also a legitimate ordering device on its own: inserting `J.m.1` to place new work immediately after `J.m` is fine *even when that work is not semantically or procedurally a child of `J.m`*. Proximity in the sequence is a sufficient reason — you need not manufacture a conceptual parent-child link to justify it.

In every case the form stays flat — `J.m.#`, never a 4th level like `J.m.1.1`. If you are already inside a 3-level `J.m.#` bundle and need finer ordering, resequence the small `J.m.#` bundle or append to the existing `J.m.#` list rather than cascading deeper.

Sub-numbered stories follow normal Version Cadence: each one that ships code takes its own bump.

### Inserting a new story

When a new story needs to land and the obvious sequential ID is contested (work has paused/resumed, multiple stories were drafted in parallel, a follow-up to an earlier story emerged), choose one of three insertion options in this order of preference:

1. **Append (default).** Use the next sequential ID at the top level (`A.a → A.b → A.c → …`). This is correct in the overwhelming majority of cases — new work goes after the latest committed story, regardless of which earlier story conceptually motivated it. Always try Option 1 first.

   **Exception — developer-signaled priority insert.** When the developer indicates a new story should land *before* one or more existing `[Planned]` stories in the current phase (higher priority, prerequisite, blocker, ad-hoc interrupt request, or similar), insert it immediately after the last `[Done]` story and renumber the `[Planned]` tail (per Option 3 Renumber). The P.w reference-accretion check confirms this is safe on untouched `[Planned]` placeholders. An ad-hoc work request that interrupts the planned sequence is itself such a signal; when in doubt, ask the developer where the new story belongs rather than defaulting to the tail. Without an explicit or implicit developer signal, the Append default applies — do not infer priority from your own read of conceptual fit.

2. **Sub-number extension.** Add `<parent>.1`, `<parent>.2`, … when the new work is conceptually a follow-up to an existing story (`J.m → J.m.1`) **or** simply needs to sit immediately after `<parent>` for ordering (proximity is a sufficient reason on its own — see "Sub-numbered stories" → *Ordering convenience*; the new story need not be a true child of `<parent>`). Two pre-conditions apply:
   - **Parent must be the latest top-level ID committed under its phase.** If `J.n` (or any later top-level ID) already exists in committed git history, sub-numbering `J.m` would produce a heading that appears in the file *before* `J.n` — violating the "stories appear in the order performed" invariant. Use Option 1 (Append) instead in that case.
   - The form is flat — no cascading like `J.m.1.1`. Maximum two levels: top-level (`J.m`) and one numeric suffix (`J.m.1`). The 3-level depth limit is hard.

3. **Renumber (last resort).** Insert at an existing position by shifting later IDs by one (`A.c → A.d`, `A.d → A.e`, …) and updating every cross-reference. Used only when neither Append nor Sub-number applies and the conceptual ordering genuinely matters more than the historical ordering. One hard pre-condition:
   - **Only valid on IDs around which no references have accreted.** An ID becomes **locked** as soon as any of the following is true: **(a)** its current status is anything other than `[Planned]` (i.e., `[In Progress]` or `[Done]`); **(b)** any commit message names it; **(c)** it is cited outside `stories.md` itself — in `CHANGELOG.md`, other spec docs, PR descriptions, or external tooling. An ID that merely sits in committed `stories.md` as an untouched `[Planned]` placeholder from initial roadmapping is **not** locked — being present in the file is not the same as having references accrete around it. Verify safety with:

     ```bash
     git log --all --grep='<ID>'                              # commit-message references
     grep -RFn '<ID>' docs/ CHANGELOG.md --exclude=stories.md # cross-references in tracked text
     ```

     If both come up empty and the story's current status is `[Planned]`, the ID is renumberable. Otherwise, choose Append or Sub-number.

Sub-numbering and renumber are both deliberate exceptions to the simpler "always append" rule. When in doubt, Append.

### Continuing across archive boundaries

When `stories.md` is archived (via `archive_stories` mode), the fresh `stories.md` starts empty — but phase letters do **not** reset. To determine the next phase letter:

1. Look in `docs/specs/.archive/` for files matching `stories-vX.Y.Z.md`.
2. If any exist, read the one with the highest version and find the highest phase letter inside it. The next phase letter is the successor in the base-26 sequence (e.g., if the archive's last phase was `K`, the next is `L`; if it was `AZ`, the next is `BA`).
3. If `.archive/` is missing or empty, start at `A`.

Story sub-letters reset within each phase — they do not continue across phases or archive boundaries.

---
