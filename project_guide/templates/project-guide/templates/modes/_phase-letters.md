## Phase and Story ID Scheme

Phase and story IDs use a base-26 letter scheme with no zero. The same scheme applies to both — single letters first, then two-letter combinations, etc. This keeps IDs short while supporting projects of any size, and lets archive boundaries continue the sequence cleanly.

### Phase letters

Phases are labeled `A`, `B`, …, `Z`, then `AA`, `AB`, …, `AZ`, `BA`, …, `ZZ`, then `AAA`, …. The scheme is base-26 with no zero — there is no "phase 0" and `B` follows `A` (not `AB`).

Examples in order: `A`, `B`, …, `Z`, `AA`, `AB`, `AC`, …, `AZ`, `BA`, `BB`, …, `ZZ`, `AAA`, ….

### Story sub-letters

Within a phase, stories use lowercase letters following the same scheme: `A.a`, `A.b`, …, `A.z`, then `A.aa`, `A.ab`, …, `A.az`, `A.ba`, ….

Examples: `A.a`, `A.b`, …, `A.z`, `A.aa`, `A.ab`, ….

### Sub-numbered stories

A story may carry an optional numeric suffix — `J.m.1`, `J.m.2`, … — appended after the sub-letter. Sub-numbers are flat (no cascading like `J.m.1.1`) and start at `1`. Two situations use them:

- **Pre-implementation split.** When `J.m` is planned but its scope is judged too large before any work begins, the heading is split into `J.m.1`, `J.m.2`, … and the bare `J.m` heading is dropped. Sequence becomes `…, J.l, J.m.1, J.m.2, J.n, …`.
- **Post-implementation follow-up.** When `J.m` ships but a bug or follow-on feature must land before proceeding to `J.n`, the follow-up is added as `J.m.1` (and may cascade to `J.m.2`, `J.m.3`, …). Sequence becomes `…, J.l, J.m, J.m.1, J.m.2, …, J.n, …`.

Sub-numbered stories follow normal Version Cadence: each one that ships code takes its own bump.

### Continuing across archive boundaries

When `stories.md` is archived (via `archive_stories` mode), the fresh `stories.md` starts empty — but phase letters do **not** reset. To determine the next phase letter:

1. Look in `docs/specs/.archive/` for files matching `stories-vX.Y.Z.md`.
2. If any exist, read the one with the highest version and find the highest phase letter inside it. The next phase letter is the successor in the base-26 sequence (e.g., if the archive's last phase was `K`, the next is `L`; if it was `AZ`, the next is `BA`).
3. If `.archive/` is missing or empty, start at `A`.

Story sub-letters reset within each phase — they do not continue across phases or archive boundaries.

---
