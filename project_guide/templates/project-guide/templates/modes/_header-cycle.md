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

**Work stories in document order.** The next story to work on is the next-in-sequence `[Planned]` story in `stories.md` — never a new story appended at the tail when other `[Planned]` stories sit ahead of it, and never a `[Planned]` story chosen out of position. This rule binds regardless of any explicit developer signal: completing a story out of order produces the same out-of-sequence state that `project-guide git-push` flags at commit time, and is corrupting whether or not the developer asked for the work. If an ad-hoc developer request would create a new story that needs to land before existing `[Planned]` stories, insert it at the correct position first (per the *Exception — developer-signaled priority insert* rule on Option 1 Append in the Phase and Story ID Scheme section) — do not append at the tail and then work it.

**Recovery when already out of order.** If a story has been marked `[Done]` while earlier `[Planned]` stories remain unstarted, do not silently continue. Stop and ask the developer to choose between (a) moving the completed story to its proper position — renumber per Option 3, allowed by the reference-accretion rule on the untouched `[Planned]` placeholders — or (b) undoing the work and restoring `[Planned]` status on the out-of-order story. Do not pick (a) or (b) unilaterally.

---
