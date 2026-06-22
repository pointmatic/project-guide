**Next Action**
Restart the cycle of steps. 

---

## Version Cadence (quick reference)

When bumping the package version for a completed story, follow the **Version Cadence** rule documented at the top of `docs/specs/stories.md`. Quick reference:

- Bugfix or trivial change → **patch**
- Feature or improvement → **minor**
- Breaking change → **major** (post-1.0 only; only via `plan_production_phase`)
- **Phase-bundled releases:** stories within a phase can run unversioned during work; the phase ships a single release/tag at end-of-phase, with bump magnitude determined by the highest-impact change in the bundle.

**Do not extrapolate the bump magnitude from `pyproject.toml`'s current version.** Re-read `docs/specs/stories.md`'s Version Cadence section if unsure.

## Out-of-scope items in stories

When announcing a story (Step 2 in code cycles, or the equivalent gate in other cycle modes), check whether the story or its parent phase plan has an "Out of scope" section. If so, **briefly summarize those items to the developer**. They are a negotiation point — the developer may opt some items back into scope before implementation begins. Do not silently treat them as deferred.

## Story execution order

**Sequential is the strong default — not an absolute.** The next story to work on is normally the next-in-sequence `[Planned]` story in `stories.md`, and that is the right pick in the overwhelming majority of cycles. Two bounded departures are legitimate:

- **One story out of order is allowed.** Pulling a *single* `[Planned]` story ahead of its position — because it makes the *implementation* flow more naturally, unblocks the story you actually want to write next, or the developer asked for it — is fine. Do it deliberately and name it in your Step 2 (announce next story) beat so the developer can redirect cheaply. This mirrors the shipped `project-guide git-push` single-story out-of-sequence opt-in: one uncommitted `[Done]` story is unambiguous to attribute, so the wrapper offers to commit it in place rather than erroring.
- **Cherry-picking is not.** Working *multiple* stories non-sequentially — hopping around the `[Planned]` list picking whatever looks appealing — is the corrupting pattern the sequence rule exists to prevent. A scatter of out-of-order `[Done]` stories is exactly the genuine multi-story out-of-sequence state `project-guide git-push` hard-errors on (attribution across several uncommitted stories is ambiguous). One deliberate step out of line is fine; a scatter is not.

**When the sequencing itself looks wrong.** If you judge the *overall* order of `[Planned]` stories is off — a structural mis-sequence, not just one story you want to pull forward — raise it with the developer instead of silently reordering a whole bundle. Offer to do a resequencing pass (flag it as **token-expensive**: it touches IDs and their cross-references across the file), or let the developer resequence themselves. Reordering more than a single sanctioned insert is the developer's call, not yours to make unilaterally.

**If an ad-hoc request needs a new story before existing `[Planned]` work,** insert it at the correct position first (per the *Exception — developer-signaled priority insert* rule on Option 1 Append in the Phase and Story ID Scheme section) — do not append at the tail and then work it out of order.

**Recovery when already out of order.** If a story was marked `[Done]` while earlier `[Planned]` stories remain unstarted *and the result looks wrong* — a scatter, or a pulled-forward story that now strands its prerequisites — do not silently continue. Surface it and let the developer choose between (a) moving the completed story to its proper position (renumber per Option 3, allowed by the reference-accretion rule on the untouched `[Planned]` placeholders) or (b) undoing the work and restoring `[Planned]` status on the out-of-order story. Do not pick (a) or (b) unilaterally. A single, deliberate, developer-sanctioned out-of-order story is **not** a defect to recover from — leave it.

## Story scope & splitting

Story scope is re-assessed at **implementation time**, not only when the story was planned — a heading that looked right on the roadmap can prove too large once you open it.

- **Split an oversized `X.y` into an `X.y.#` bundle.** When the story as written is too big to land as one coherent unit/commit, split it into `X.y.1`, `X.y.2`, … (the pre-implementation split described in the "Sub-numbered stories" section: drop the bare `X.y` heading; the sequence becomes `…, X.x, X.y.1, X.y.2, X.z, …`). Each sub-numbered story is still one unit of work → one story → one commit.
- **Sub-numbering is also a practical ordering device.** Inserting an `X.y.1` to get the ordering you want is legitimate *even when the new story is not semantically or procedurally a child of `X.y`* — proximity in the sequence is a sufficient reason on its own, distinct from the conceptual-follow-up framing in Option 2 (Sub-number extension).
- **No 4th level.** The depth limit is hard: `X.y.#` is the floor, never `X.y.#.#`. If you are already working inside a 3-level `X.y.#` bundle and need finer ordering, either resequence the small `X.y.#` bundle or append to the existing `X.y.#` list — do not invent `X.y.1.1`.

**Brittle cross-story dependencies.** When implementation reveals that two stories depend on each other so tightly that landing one without the other leaves the tree in a bad state, you **may** offer to reorganize tasks between them into a more self-contained structure. Reserve this for **extreme** cases. Stories within a phase / subphase / bundle are normally implemented in rapid succession, so the long-term repo risk from any single story briefly breaking the build is low, and reshuffling task boundaries (and the cross-references pointing at them) usually costs more than it saves. Offer it; do not do it unilaterally.

---
