# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.13.0] - 2026-06-05

**Subphase Q-3 bundled release: Pyve-managed-hosting cross-repo contract + awareness.** Subphase Q-3 of Phase Q pins the four cross-repo contracts that let Pyve host project-guide as a globally-shimmed tool in its toolchain venv (Pyve Story N.aw), and teaches project-guide's user-facing surfaces to reflect pyve-managed hosting. Three contracts already held in code and are now guarded by tests (Q.l); the fourth — branching content on whether pyve is detected, plus a defensive local-install warning — is the new behavior (Q.m). Stories Q.l/Q.m ran unversioned during work; Q.n marks the release boundary. The minor bump reflects the new behavior and the newly-published contract surface. Plan: [`docs/specs/phase-q-subphase-3-pyve-hosting-plan.md`](docs/specs/phase-q-subphase-3-pyve-hosting-plan.md); cross-repo contract: [`docs/specs/phase-q-pyve-toolchain-hosting.md`](docs/specs/phase-q-pyve-toolchain-hosting.md).

### Added
- **Q.l — Cross-repo contract tests.** New `tests/test_cross_repo_contract.py` pins three contracts Pyve depends on: **install-location independence** (`init`/`update`/`mode` write only to the cwd, never the package install location), the **`--version` output format**, and the **`.project-guide.yml` marker shape** (filename + the `version` / `installed_version` / `target_dir` / `current_mode` field subset).
- **Q.l — Cross-repo contract documentation.** New "Cross-Repo Contracts" section in `features.md` (functional enumeration with guarding tests) and a "Pyve cross-repo contracts" section in `project-essentials.md` (architectural invariants: renames/field-removals/`--version`-format changes are coordinated breaking changes requiring a paired Pyve story; pyve detection is cached at init time, never re-run per invocation).
- **Q.m — Pyve-managed-hosting awareness.** When pyve is detected (cached `pyve_version`), the rendered `go.md` onboarding line (`_header-common.md`) uses pyve-managed wording instead of `pip install`; `project-guide status` appends a dim `Managed by pyve vX.Y.Z (detected at init time).` footer (read from cache, no runtime re-detection); and `README.md` gains a "Via pyve (recommended)" install section.
- **Q.m — Defensive local-install warning.** `project-guide heal` (and the auto-hook) warn on stderr when a project-local `site-packages` install of project-guide coexists with pyve-managed hosting, with a copyable `pip uninstall project-guide` command. Never auto-removes (same wrapper-initiates-side-effects discipline as the P.o `go.md` warning); an editable source checkout is deliberately not flagged.

### Changed
- **Q.m — `developer/project-guide.md` install line.** Reworded to be host-agnostic (names both `pyve self install` and `pip install project-guide`), fixed the `project-guides` typo, and corrected a stale `docs/guides/project-guide.md` read target to `docs/project-guide/go.md`.

## [2.12.0] - 2026-06-05

**Subphase Q-2 bundled release: `plan_envs` mode + full documentation drift sweep.** Subphase Q-2 of Phase Q adds a new `plan_envs` sequence mode that guides the developer through enumerating a Pyve-managed repo's named environments (root + test envs, with closed-vocabulary attributes), authoring `docs/specs/env-dependencies.md` from a template vendored from Pyve at `spec_version: "3.0"`. Stories Q.d/Q.e/Q.e.1/Q.e.2 ran unversioned during work; Q.f marks the release boundary. The minor bump is driven by the new opt-in mode and artifact template. Plan and rationale: [`docs/specs/phase-q-subphase-2-plan-envs-plan.md`](docs/specs/phase-q-subphase-2-plan-envs-plan.md); cross-repo contract: [`docs/specs/phase-q-wizard-env-contract.md`](docs/specs/phase-q-wizard-env-contract.md).

### Added
- **Q.d — `plan_envs` sequence mode.** New mode template (`plan-envs-mode.md`) that infers environment topology from `features.md` / `tech-spec.md` plus the codebase, then authors `docs/specs/env-dependencies.md`. Slotted into the canonical planning sequence as `plan_tech_spec → plan_envs → plan_stories` (`plan_tech_spec.next_mode` flipped to `plan_envs`; the change is advisory-only and non-breaking — explicit-mode-name invocation is unchanged). The mode carries a closed-vocabulary discipline note: backend / language / framework / packaging / app_type values come from the vendored §2 glossary; a value outside the set is a spec violation and a missing mechanism is a Pyve change-request, never an invented value.
- **Q.d — `env-dependencies.md` bundled artifact template.** New artifact template vendored from Pyve's `env-dependencies-template.md` at `spec_version: "3.0"` (hard-coded at the §4.0 machine-readable YAML block). Preserves the §0–§9 structure and the closed-vocabulary tables verbatim; carries a header comment recording the vendored-template invariant and pointing at the `project-essentials.md` contract section.
- **Q.e — Pyve env-spec vendored-template contract** documented as a new `project-essentials.md` section: Pyve owns the vocabulary; the known+implemented / known+advisory / unknown→error trichotomy; the refresh-story protocol (same shape as Q.b's pyve-essentials alignment); the authoritative upstream pointer; and its complementary relationship to the auto-rendered `### Pyve Essentials` block.

### Changed
- **Q.e / Q.e.1 — Planning-artifact spec sync.** `features.md` FR-1 modes table gains `plan_envs` and `plan_production_phase` rows (count → 17 total); FR-1 acceptance count "15 modes" → "17 modes"; FR-2 gitignore description updated from the legacy "3 lines" form to the negation-free explicit-list form. `concept.md` Scope refreshes the CLI command list to the current subcommand set (adds `heal`, `archive-stories`, `bump-version`, `git-push`), completes the mode list with `archive_stories`, retires the stale `project_scaffold` / `code_velocity` names (→ `scaffold_project` / `code_direct`), and reconciles the "17 modes" count with the listed items.
- **Q.e.2 — Documentation-artifact drift sweep.** `README.md` and the MkDocs site under `docs/site/` refreshed: mode counts → 17 across `index.html`, `workflow.md`, `configuration.md`, `commands.md`; retired `code_velocity` → `code_direct` in `getting-started.md`, `install-options.md`, `configuration.md`; the `modes.md` reference gains full `plan_envs` and `plan_production_phase` entries plus an updated planning-sequence intro, `plan_tech_spec` Next field, and New-Project flow diagram.

## [2.11.0] - 2026-06-01

**Subphase Q-1 bundled release: subphase strategy for large phases + Pyve v2.8.0 alignment.** Phase Q ("DX Improvements & Subphase Support") opens with Subphase Q-1, which lands two coupled developer-experience improvements as one bundle. Stories Q.a and Q.b ran unversioned during work; Q.c marks the release boundary. The minor bump is driven by the highest-impact change in the bundle (the new opt-in subphase pattern in `plan_production_phase` / `plan_phase`); the pyve-essentials refresh on its own would have been patch-grade. Plan and rationale: [`docs/specs/phase-q-dx-subphases-plan.md`](docs/specs/phase-q-dx-subphases-plan.md); change request for the subphase pattern: [`docs/specs/subphase-strategy-for-large-phases.md`](docs/specs/subphase-strategy-for-large-phases.md).

### Added
- **Q.a — Subphase strategy pattern for large/complex phases.** New opt-in **Step 4a (Subphase decomposition — optional)** in `plan-production-phase-mode.md`, inserted between Step 4 (generate phase plan) and Step 5 (breaking-change negotiation). The mode now suggests subphasing when the phase exceeds rough size thresholds (>~7 gap-analysis rows, >~4 architectural layers or breaking changes, major bumps with post-major polish), then drafts stories only for Subphase 1 — subsequent subphases get their stories drafted in their own future `plan_production_phase` invocations. Re-entering `plan_production_phase` mid-phase to draft a later subphase is now documented as the canonical pattern, not a misuse. Small/medium phases continue to use the single-block decomposition unchanged; the pattern is fully additive.
- **Q.a — Subphase ID scheme in `_phase-letters.md`.** New "Subphases (structural grouping within a phase)" section between "Story sub-letters" and "Sub-numbered stories". Subphase IDs use arabic numerals with a hyphen separator (`N-1`, `N-2`, …) — deliberately distinct from story IDs (`N.a`) and sub-numbered stories (`N.m.1`). Subphase headings use `##` (peer of the phase heading); story letters continue monotonically across subphase boundaries; the 3-level story-ID depth cap holds; the multi-release exception is documented for phases that ship more than one release tag.
- **Q.a — `plan_production_phase` Step 7 subphase layout.** When Step 4a opted into subphasing, Step 7 now emits a `## Subphase <Letter>-N:` heading per subphase under the phase heading, with stories drafted only under Subphase 1's heading and the structural preamble explaining the monotonic continuation rule and any multi-release exception.
- **Q.a — `plan_phase` pre-1.0 cross-reference.** Step 4 picks up a parenthetical noting the subphase pattern is available pre-1.0 too but rarely needed — the default is to draft every story in one session; cross-reference to `plan_production_phase` Step 4a.
- **Q.b — Named test environments (`[tool.pyve.testenvs]`) awareness.** New section in the bundled `pyve-essentials.md` artifact (auto-rendered into every consumer's `go.md` under `## Project Essentials > ### Pyve Essentials` via FR-13) mentioning Pyve v2.8.0's declarative test-env configuration — per-env `backend`, dependency `source`, lazy lifecycle — with a pointer at Pyve's `testing.md` for the full schema. Project-guide does not duplicate the schema; awareness only.
- **Q.b — `pyve update` vs. `pyve init --force` section.** New section in `pyve-essentials.md` distinguishing the non-destructive refresh path (`pyve update`) from the destructive rebuild (`pyve init --force`), and folding in `pyve check` as the diagnostic command that replaced Pyve v2.0's removed `pyve doctor` / `pyve validate` aliases.

### Changed
- **Q.a — `_header-common.md` scope-of-authority clarification.** The "Scope of authority — structural changes to `stories.md`" rule now explicitly names subphase headings (`## Subphase <Letter>-N:`) as structural sub-groupings, not new phases — closing the loophole where an LLM drafting a later subphase mid-phase would have read the rule as forbidding the new `##` heading. The phase-creation gate itself is unchanged: only `plan_phase` / `plan_production_phase` may create `## Phase` headings.
- **Q.b — `pyve-essentials.md` testenv path refresh.** Replaced `.pyve/testenv/venv/` references with `.pyve/testenvs/testenv/venv/` (Pyve v2.8.0 layout, default env name); added a one-paragraph note explaining the generalization to `.pyve/testenvs/<name>/{venv,conda}/` for declared named envs. Pyve handles the on-disk migration transparently the first time `pyve update` / `pyve test` / `pyve testenv …` runs against a v2.8+ binary — no consumer-facing breakage.

## [2.10.2] - 2026-05-25

**Story-insertion priority signal and out-of-order completion guard (P.x).** Two related LLM workflow bugs surfaced in a downstream project, both rooted in the same scenario: an ad-hoc developer request arriving while `[Planned]` stories sit ahead in the phase queue. The LLM appended the new story at the tail (wrong position — the work belonged before the queue) and then marked it `[Done]` while the earlier `[Planned]` stories remained untouched (wrong execution order). Two template edits fix the two bugs at their respective rule layers: the numbering layer (`_phase-letters.md`) gains a developer-signaled priority-insert exception to Option 1 Append, and the cycle-discipline layer (`_header-cycle.md`) gains a "Work stories in document order" rule plus a "Recovery when already out of order" rule that names both move-to-proper-position and undo-the-work as developer-choice options.

### Changed
- **P.x — `_phase-letters.md` Option 1 Append exception.** New paragraph appended to the Option 1 bullet: when the developer signals (explicitly *or* implicitly via an ad-hoc interrupt request, prerequisite, blocker, or similar) that a new story should land before existing `[Planned]` stories, insert immediately after the last `[Done]` story and renumber the `[Planned]` tail via Option 3. The exception explicitly invites the LLM to ask the developer when the signal is ambiguous, rather than defaulting to the tail. Without any signal, the Append default still rules. The renumber is safe by construction in the untouched-`[Planned]` case per the P.w (v2.10.1) reference-accretion rule.
- **P.x — `_header-cycle.md` "Story execution order" section.** Two new paragraphs, included into every cycle mode at render time. *Work stories in document order:* the next story to work on is the next-in-sequence `[Planned]` story; never a new story appended at the tail when `[Planned]` stories sit ahead of it, never a `[Planned]` story chosen out of position. Binds regardless of any developer signal. *Recovery when already out of order:* when a story has been marked `[Done]` while earlier `[Planned]` stories remain, stop and ask the developer to choose between moving the completed story to its proper position (renumber per Option 3, P.w-enabled) or undoing the work and restoring `[Planned]` status. Do not pick either unilaterally.

## [2.10.1] - 2026-05-23

**Loosen the renumber pre-condition in the `_phase-letters.md` partial template (P.w).** Field experience in a downstream project surfaced that `plan_phase` was refusing to renumber phases whose `[Planned]` headings had been committed to `stories.md` as untouched roadmap placeholders — even though no commits, CHANGELOG entries, or cross-references actually named them. The rule has been restated around *reference accretion* rather than mere presence in committed history.

### Changed
- **P.w — `_phase-letters.md` "Renumber (last resort)" pre-condition.** The rule now locks an ID iff (a) its current status is anything other than `[Planned]`, (b) any commit message names it, or (c) it is cited outside `stories.md` itself (CHANGELOG, other spec docs, PR descriptions, external tooling). A `[Planned]` heading in committed `stories.md` with none of (a)/(b)/(c) is renumberable. The rule ships with two mechanical verification commands — `git log --all --grep='<ID>'` for commit-message references, and `grep -RFn '<ID>' docs/ CHANGELOG.md --exclude=stories.md` for cross-doc references (the `--exclude=stories.md` flag is essential — without it the grep always matches the heading being checked, making the success condition unreachable). Pre-P.w the rule locked any ID appearing in committed git history regardless of status or accreted references, which produced false-positive lockouts in the field.

## [2.10.0] - 2026-05-20

**`project-guide git-push` learns about header stories and out-of-sequence commits (P.v).** Two safety refinements to the bundle-offer flow shipped in v2.9.0, surfaced by dogfooded use in a downstream project: (1) "group overview" stories that have no checklist items are now treated as decorative headers and filtered out of the uncommitted-detection flow — they no longer get proposed for commit; (2) when uncommitted `[Done]` stories sit out-of-document-order with committed `[Done]` stories between them, the wrapper now exits 1 with a precise error instead of silently bundling them. A small consumer-visible semantic change: the "nothing real to commit" case is now **exit 0** instead of exit 1, because the repo being in the desired state is success.

### Added
- **P.v — Header-story filter.** A `[Done]` story whose body contains zero `- [ ]` / `- [x]` checklist items is treated as a header (group-overview heading for a sub-numbered cluster like `H.m` / `H.m.1` / `H.m.2`) and filtered out of `git-push`'s uncommitted-detection flow. New `StoryHeading.is_header` field (default `False` preserves backward compat for direct constructors). The forgiving rule — zero items *of any kind*, not "zero checked items" — means a `[Done]` story with all-unchecked items is still treated as a real story; the unchecked items are a developer-discipline concern, not a header signal.
- **P.v — Out-of-sequence detection.** After the header filter, the `[Done]` list in document order must follow a clean committed-prefix → uncommitted-suffix partition. Any uncommitted story whose document index is less than the index of the last committed story is out-of-sequence; the wrapper exits 1 with an error block listing every offender (plus their later-committed context) and the uncommitted-tail stories that would be eligible for normal flow. This is an unambiguous error path — `--no-input` does *not* auto-yes/no it.

### Changed
- **P.v — `_read_done_stories` body scan.** `project_guide/stories.py:_read_done_stories` now slices each story's body (between its `### Story` heading and the next story / phase / future heading or EOF) and scans for `- [ ]` / `- [x]` lines (regex `^\s*- \[[ x]\]\s`, multiline) to populate the new `is_header` flag.
- **P.v — `StoryHeading` frozen dataclass gains `is_header: bool = False`.** Field has a default so existing callers and tests constructing `StoryHeading(story_id=..., title=...)` directly continue to work unchanged.
- **P.v — `git_push` exit semantics for "all committed".** When every `[Done]` story is already in git log (post-header-filter), the wrapper now exits **0** with `"Nothing to commit — every real [Done] story is already in git log."` (plus a parenthetical naming any headers present). Pre-P.v this was exit 1 with the misleading `"Story <last id> is already committed"` text — which named the header heading when the last `[Done]` happened to be a header. The "no `[Done]` story at all" path keeps its exit-1 stories.md-authoring-problem semantics.
- **P.v — `project-essentials.md` `git-push` section.** Expanded with the header-filter rule (zero-checklist-items signal, forgiving direction, scope limited to `git-push`), the out-of-sequence partition rule, the new exit-0 nothing-to-commit semantics, and the rationale for each.

### Fixed
- **P.v — Field bug: header story bundled with later sibling.** Pre-P.v, a stories.md shape like `H.m (header) / H.m.1 / H.m.2 / H.m.3 / H.n (header, [Planned]) / H.n.1 (uncommitted)` — with `H.m.1`/`H.m.2`/`H.m.3` already committed in git — caused the wrapper to propose `H.m, H.n.1: ...` as a bundle subject. The two IDs look in-sequence in isolation, but `H.m.1`/`H.m.2`/`H.m.3` sat committed between them in document order. Post-P.v: the header filter removes `H.m`, and the out-of-sequence check (had `H.m` been a real story) would have caught the gap.
- **P.v — Field bug: out-of-sequence stories silently bundled.** Pre-P.v, the bundle offer assembled the uncommitted set in document order without verifying that order was actually contiguous. Now any committed-after-uncommitted gap is a hard error before the bundle offer can fire.

## [2.9.0] - 2026-05-20

**`project-guide git-push` learns to read and write bundled commits (P.u).** When a developer commits multiple `[Done]` stories under one bundled subject (e.g., `H.a, H.b, H.c InputSource ...`), the wrapper now correctly recognizes all bundled IDs as committed instead of misreporting them as uncommitted. When 2+ `[Done]` stories remain uncommitted, the wrapper offers a bundled commit subject with a `[Y/n]` gate rather than forcing the developer to hand-type one. A new duplicate-`<id>` warning surfaces git-log anomalies where the same story ID appears in multiple commits.

### Added
- **P.u — Bundled-commit recognition in already-committed check.** `parse_committed_ids_from_subject` (new, in `project_guide/stories.py`) extracts the full ordered list of story IDs from a commit subject across single-ID, legacy `Story <id>:`, legacy bundle (no colons), canonical unversioned bundle (`H.a, H.b, H.c: title`), per-story-versioned bundle (`H.j: v0.10.0, H.k: v0.11.0 title`), mixed-version bundle, and single-trailing-version bundle forms. The parser is permissive on read (every `:` optional) and the formatter is strict on emit (colon precedes a version or a title, never separates two bare IDs).
- **P.u — Bundle-offer flow.** When 2+ uncommitted `[Done]` stories exist, the wrapper proposes a bundled commit subject `<id1>[: <ver1>], <id2>[: <ver2>], ... <title1> + <title2> + ...` and prompts `Use this message? [Y/n]` (default `Y`). Accept → invoke `git-push` with the bundled message. Decline → exit 1 with the existing `"use git-push directly"` manual-resolution hint. New `derive_bundle_commit_message` formatter in `project_guide/stories.py` handles per-story version detection, backtick / double-quote sanitization (same rules as single-story), title joining with `" + "`, and whitespace trim-and-collapse on the final subject.
- **P.u — Duplicate-`<id>` warning.** When the same bare story ID appears in 2+ commit subjects in `git log`, the wrapper emits a stderr warning listing each duplicate ID and the offending subjects, and prompts `Continue? [Y/n]` (default `Y`). The version is incidental — duplicate detection is keyed on `<id>` only, so a story shipped under two different versions still surfaces.
- **P.u — `--no-input` flag on `git-push`.** New `--no-input/--input` option auto-declines both the bundle offer and the duplicate-`<id>` continuation prompt (also auto-enabled by `CI=1` or non-TTY stdin per the standard `--no-input` contract). Auto-no is chosen for both gates because accepting either would change the shape of a commit (or paper over a history anomaly) silently — a developer decision, not a CI default.

### Changed
- **P.u — `_get_committed_story_ids` return type.** The helper now returns `tuple[set[str], dict[str, list[str]]]` (committed-IDs set + duplicates map) instead of `set[str]`. This is an internal-only API; no public surface affected.
- **P.u — Commit-subject parser location.** Retired `_COMMIT_SUBJECT_STORY_ID_RE` from `project_guide/cli.py` (introduced by P.k, made permissive in P.s) in favor of the structured `parse_committed_ids_from_subject` parser in `project_guide/stories.py`. Tests that referenced the regex directly have been migrated to call the parser.
- **P.u — `project-essentials.md` `git-push` section.** Expanded with the bundle-offer flow, the colon-precedes-version-or-title rule, the duplicate-`<id>` warning, the `--no-input` defaults, and the parse-permissive / emit-strict invariant.

### Fixed
- **P.u — Field bug: bundled commits no longer misclassified as uncommitted.** Pre-P.u, a bundled commit like `H.a, H.b, H.c InputSource ...` was invisible to the single-ID regex, so all bundled stories appeared "uncommitted" on the next `git-push` invocation — the wrapper either re-proposed the oldest one or fell through to the multi-uncommitted error path. Now correctly recognized.

## [2.8.0] - 2026-05-20

**Phase P closing bundle: cycle-mode LLM-workflow discipline + XP methodology grounding + untracked-by-default `go.md` policy.** Six stories shipped between v2.7.2 and v2.8.0 (P.n–P.s). The one consumer-visible behavior change is the new tracked-`go.md` heal warning and the matching `git rm --cached docs/project-guide/go.md` consumer migration (P.o); the remaining five stories are template/doc reshapes that change how the LLM behaves on the next `project-guide mode <X>` render, with no consumer migration required.

### Changed
- **P.o — Untracked-by-default `go.md` policy.** `project_guide/cli.py:heal` now detects when `docs/project-guide/go.md` is in the consumer's git index and emits a stderr warning with a copyable migration command (`git rm --cached docs/project-guide/go.md && git commit`). Silent when go.md is untracked, when cwd is not a git repo, under the recursion guard, or under `--no-input`. `project_guide/cli.py:init` emits a stderr note after the initial render that `go.md` is intentionally untracked. The warning is non-fatal and never runs git operations itself — same wrapper-initiates-git-ops constraint that bounded the P.k `git-push` wrapper.
- **P.s — Permissive commit-subject regex.** `_COMMIT_SUBJECT_STORY_ID_RE` now accepts both the bare `<id>: <title>` form (canonical going forward; matches `derive_commit_message`'s output) and the legacy `Story <id>: <title>` form (still seen in consumer repos). Resolves a field bug where mixed-form commit history caused the `git-push` wrapper to miss `Story `-prefixed commits and emit a spurious "multiple uncommitted" error.

### Added
- **P.p — Three-flavor spike taxonomy.** `developer/best-practices-guide.md`'s "Hello World First — Spike Early, Spike Often" section now documents three spike flavors: **integration spike** (will external systems connect?), **architectural spike** (Beck-canonical; will this design work?), **investigation spike** (is there a viable path at all?). Each flavor has a question-answered framing, triggers, and output. New section closing with the canonical 3-story foundation table (A.a Scaffolding / A.b Hello World / A.c integration spike).
- **P.p — XP methodology grounding.** New top-level section in `developer/best-practices-guide.md` covering lineage (Beck 1999, C3 team), why XP practices counter known LLM failure modes (test-first vs. "looks right" hallucination, small steps vs. context-window drift, spikes vs. fabricated confidence, documented decisions vs. invisible scope creep, pair-style developer/LLM rotation), and a bibliography (Beck 1999/2004, Jeffries/Anderson/Hendrickson 2000).
- **P.p — Inserting-a-new-story rules.** New "Inserting a new story" subsection in `_phase-letters.md` covering Append (default) / Sub-number extension / Renumber (last-resort) with both P.s-triage precision rules: Sub-number is valid only when the parent is the latest top-level committed ID; Renumber is valid only on working-tree-only IDs.
- **P.q — Four cycle-discipline rules** in `_header-common.md`'s universal Rules block: **Sequential, story-by-story documentation**, **Documentation timing** (default write-then-execute + debug exception, on-disk-before-gate invariant), **Spikes for uncertainty reduction** (cross-references P.p's three-flavor taxonomy), **Approval-gate documentation handoff** (LLM authors the story before pausing, not after the developer asks).
- **P.q — Debug-mode Step-5 reinforcement.** New "Documentation timing in `debug`" paragraph names debug as the one legitimate exception to the universal timing rule and states explicitly that the LLM authors the story. New **"Deferring the Gate Artifact to the Developer"** anti-pattern entry sibling to "Declaring the Fix Complete After Step 4."
- **P.r — Mode echo + step-name conventions** in `_header-common.md`: the "After reading" protocol now has `**First line, always:** "Mode: <mode_name>."` as the always-first line, and a new universal Rules-block bullet requires step references to include the step's name in parens on first mention (e.g., "Cycle Step 1 (read stories) done; per Step 2 (announce next story), …").

### Fixed
- **P.n — Scope-of-authority guardrail.** Closed a drift path where cycle modes could rationalize creating new `## Phase` headings in `stories.md`. New universal Rules-block bullet plus debug-mode Step-5 "Scope reminder" paragraph: cycle modes may append stories under an *existing* phase and edit story bodies, but may **not** create new phase headings, re-theme existing phases, or move stories between phases — phase creation is the exclusive job of `plan_phase` / `plan_production_phase`.
- **P.p — Foundation-story reconciliation.** Three docs (`plan-stories-mode.md`, `developer/best-practices-guide.md`, `developer/project-guide.md`) previously disagreed on the foundation-story structure (3-story vs. 2-story; A.a "Hello World" vs. A.a Scaffolding). Reconciled to the canonical 3-story foundation that `plan-stories-mode.md` already produces: **A.a Scaffolding** (in `scaffold_project` mode), **A.b Hello World** (runtime self-proof), **A.c integration spike** (integration self-proof). The terminology rename "end-to-end stack spike" → "integration spike" propagated across `plan-stories-mode.md`, `plan-phase-mode.md`, and `plan-production-phase-mode.md`.
- **P.s docs reconciliation.** Commit-message examples across `project-essentials.md`, `code-direct-mode.md`, `best-practices-guide.md`, and `production-github-guide.md` flipped from the legacy `"Story <id>: <title>"` form to the bare `"<id>: <title>"` form (canonical; matches the wrapper's emitted output).
- **P.t (this release) — Foundation cleanup follow-up.** Fixed stale "Start with Story A.a (Hello World)" line in `code-direct-mode.md:39` left over from P.p's reconciliation (A.a is now Scaffolding; A.b is Hello World; A.c is the integration spike).
- **P.t (this release) — Refactor modes now author session-level stories.** Closed the gap surfaced by P.t's mode-template audit: `refactor-plan-mode.md` and `refactor-document-mode.md` did not previously create `stories.md` entries, leaving refactor work outside the universal P.q Rule 1 "every chunk of LLM-produced work is captured as a story" invariant. Both modes now have a new **Session Story** section (authored once per session, after Step 1 of the first document; checklist captures one task per document touched + the project-essentials revisit for `refactor_plan`) and a closing **Session Close** / **Step F.5** that flips the checklist `[x]`, marks the story `[Done]`, defers the version-bump decision to the developer, and presents the session story at a session-level gate distinct from the per-document gates. One refactor session = one story = one developer commit.

### Migration
Consumers upgrading from v2.6.x – v2.7.x: run once on your default branch to migrate `go.md` to untracked-by-default per the new policy:
```bash
git rm --cached docs/project-guide/go.md && git commit -m "untrack go.md per project-guide v2.8.0"
```
`heal` continues to warn until the migration is applied. Consumers who never migrate continue to function — `go.md` keeps appearing in their working-tree diff on every mode switch, but no command fails. See P.o's body in `docs/specs/stories.md` for full rationale. No migration required for the five template/doc stories beyond the standard `project-guide update` on next invocation.

## [2.7.2] - 2026-05-19

Bug fix: `project-guide git-push` (and version/phase detection) silently dropped sub-numbered story IDs (`J.m.1`, `J.m.2`, …). When the latest `[Done]` story used the sub-numbered form, the wrapper fell back to the previous bare-letter heading and reported it as "already committed," blocking the push of the new story.

### Fixed
- **`project_guide/stories.py:_STORY_RE`** — extended the story-ID character class from `[A-Z]\.[a-z]+` to `[A-Z]\.[a-z]+(?:\.\d+)?` so headings of the form `### Story J.m.1: ...` parse correctly. Without this, `_read_done_stories()` silently filtered such headings out and the wrapper picked the wrong "last [Done] story."
- **`project_guide/cli.py:_COMMIT_SUBJECT_STORY_ID_RE`** — extended in the same shape so the already-committed check recognizes commit subjects like `J.m.1: ...`. Without this fix the duplicate-detection path would have a second-layer hole even after the stories.md side was fixed.
- **`project_guide/actions.py:_VERSION_RE`** — extended in the same shape so `detect_latest_version()` no longer under-reports the highest version when the latest story uses the sub-numbered form.

### Documented
- **`_phase-letters.md`** — added a "Sub-numbered stories" subsection covering both use cases: pre-implementation split (`J.m` was planned but split into `J.m.1`, `J.m.2` before any work; bare `J.m` heading dropped) and post-implementation follow-up (`J.m` shipped, then a bug or follow-on feature lands as `J.m.1` before proceeding to `J.n`). Flat single-level only — no cascading like `J.m.1.1`.

### Tests
- New `tests/test_stories.py` covering `_STORY_RE`, `_read_done_stories()`, and `derive_commit_message()` — `stories.py` had no direct unit tests prior to this story (the test-coverage gap that let the bug ship in P.k).
- New `tests/test_cli.py` cases for both `git-push` scenarios (post-impl follow-up with bare `J.m` present; pre-impl split with no bare `J.m`) and the round-trip "sub-numbered story is already committed" path.
- New `tests/test_actions.py` case asserting `detect_latest_version()` picks up the version on a sub-numbered heading.

## [2.7.1] - 2026-05-11

Compatibility fix for IDE-integrated LLM @-mention / fuzzy-search. The v2.6.0–v2.7.0 gitignore block used a clean `<target>/**` + `!<target>/go.md` negation pair — correct per the `.gitignore` spec, but **several IDE tools** (Cursor, parts of the VS Code fork ecosystem, certain LSP-based search backends) implement a subset of gitignore semantics that does not honor re-include negation. Those tools applied the broad `**` rule, hid `go.md`, and defeated the IDE-LLM-visibility constraint that's the entire reason `go.md` is tracked. P.l switches to a negation-free explicit-list form so simplistic parsers handle it reliably.

### Changed
- **`project_guide/cli.py:_build_project_guide_block()`** — rewritten to enumerate the bundled template root (`_get_package_template_dir()`) and emit one anchored `/<target>/<child>[/]` line per top-level entry other than `go.md`, plus a trailing `/<target>/**/*.bak.*` defensive catch-all for top-level backups. The list is dynamic — new top-level files/directories in the bundled tree are picked up automatically by both the writer and the test helper that mirrors it. Default install now writes:
  ```
  # project-guide
  /docs/project-guide/.metadata.yml
  /docs/project-guide/README.md
  /docs/project-guide/developer/
  /docs/project-guide/templates/
  /docs/project-guide/**/*.bak.*
  ```
- **`project_guide/cli.py`** — `_recognized_block_lines()` replaced with `_is_recognized_block_line(line, target_dir)` predicate. Accepts the v2.7.1+ form (any line anchored at `/<target>/`) plus every prior legacy line (`<target>/**`, `!<target>/go.md`, `<target>/**/*.bak.*`, `<target>/go.md`). Existing v2.6.x/v2.7.0 installs heal cleanly to the v2.7.1 form on `init --force`; no multi-step migration required.
- **Tests** — `_EXPECTED_GITIGNORE_BLOCK` constant replaced with `_expected_gitignore_block()` helper that mirrors the writer's enumeration; new `test_init_force_rewrites_v261_three_line_block_to_explicit_list` for the v2.6.1/v2.7.0 → v2.7.1 migration path; the foreign-block test now seeds a line not anchored at `/<target>/` so the predicate correctly flags it as foreign.
- **Docs** — updated the gitignore prose in `docs/specs/features.md`, `docs/specs/tech-spec.md`, and `docs/specs/project-essentials.md` to document the three-version evolution (v2.6.0 → v2.6.1 → v2.7.1) and the "do not simplify back to negation" warning for future maintainers.

### Migration
None required at the consumer level. The v2.6.x/v2.7.0 negation form and the v2.7.1 explicit-list form produce identical git-tracking outcomes (only `go.md` is tracked). The behavior change is purely in what `_ensure_gitignore_entry()` writes. Consumers whose IDE handles negation correctly may keep their existing block indefinitely; only consumers hitting the IDE bug actually benefit from running `project-guide init --force` to adopt the new form.

## [2.7.0] - 2026-05-11

New top-level `project-guide git-push` command — a thin wrapper over [gitbetter](https://github.com/pointmatic/gitbetter)'s `git-push` that auto-derives the commit subject from the most-recently-completed-and-not-yet-committed story in `docs/specs/stories.md`. Developer-lane convenience only; the LLM still does not initiate commits.

### Added
- **`project-guide git-push [BRANCH_NAME]` command** (`project_guide/cli.py`) — parses `docs/specs/stories.md` for the last `[Done]` story heading, derives a normalized commit subject (strip `### Story ` prefix and ` [Done]` suffix, convert backticks and double quotes to single quotes, preserve the colon after the story ID), and shells out to gitbetter's `git-push` via `shutil.which` discovery + `subprocess.run(check=False)` with no captured output (gitbetter inherits stdin/stdout/stderr and stays fully interactive). Child exit code propagates unchanged.
- **Hard-error semantics** for ambiguous states: no `[Done]` story → exit 1; last `[Done]` already committed (per `git log --pretty=%s` subject-prefix match) → exit 1 with `Use 'git-push' directly for any follow-up commit.`; multiple uncommitted `[Done]` stories → exit 1 listing the IDs; `git-push` not on PATH → exit 1 with `brew install pointmatic/tap/gitbetter` hint. The wrapper deliberately refuses to second-guess the developer in ambiguous cases — raw `git-push` remains the escape hatch.
- **`project_guide/stories.py`** — `StoryHeading` dataclass, `_read_done_stories()`, and `derive_commit_message()` as reusable helpers (the message transformer is exposed as a public name because the heading rules are part of the wrapper's documented contract).
- **External CLI dependency pattern** documented in `docs/specs/tech-spec.md` under Cross-Cutting Concerns — `git-push` is the first project-guide subcommand depending on an external binary; future workflow-integration commands should follow the same shape (`shutil.which` discover, `subprocess.run(check=False)` invoke, propagate exit code).

### Docs
- `docs/specs/features.md` — new FR-15 (Story-Aware `git-push` Wrapper), added Inputs / Command Line entry, added Acceptance Criteria item 17.
- `docs/specs/tech-spec.md` — added `git-push` to the Commands table, Key Functions documents the new helpers, new Cross-Cutting Concerns section "External CLI Dependencies (Story P.k pattern)".
- `docs/specs/project-essentials.md` — new sub-section reinforcing the LLM-vs-developer-lane rule for this command and documenting the heading-derivation rules.
- `README.md` — new `### git-push` section in Command Reference between `heal` and `override`, with the optional-dependency callout for gitbetter.

## [2.6.1] - 2026-05-11

Post-v2.6.0 follow-up: tighten the canonical `# project-guide` gitignore block from four lines to three. Behavior unchanged; the dropped line was functionally redundant.

### Changed
- **`project_guide/cli.py:_build_project_guide_block()`** — dropped the trailing `<target>/**/*.bak.*` line. The broader `<target>/**` rule introduced in v2.6.0 already ignores backups under that subtree, so the explicit line was a no-op carried over from the pre-P.d block during the policy inversion. New canonical form is three lines: header, `<target>/**`, `!<target>/go.md`.
- **`project_guide/cli.py:_recognized_block_lines()`** — kept the `<target>/**/*.bak.*` entry in the recognized-lines set so v2.6.0-shipped installs heal cleanly to the v2.6.1 3-line form on the next `init --force`. Foreign hand-customized blocks remain warned-about (no behavior change there).
- **Tests** — `_EXPECTED_GITIGNORE_BLOCK` updated to the 3-line form; added a test for the v2.6.0-→-v2.6.1 cleanup path on `init --force`.
- **Docs** — updated the gitignore prose in `docs/specs/features.md`, `docs/specs/tech-spec.md`, `docs/specs/project-essentials.md`, and `README.md` to reflect the 3-line canonical form. Historical references to the 4-line v2.6.0 form retained where they explain the migration path.

### Migration
None required. v2.6.0 installs see no behavioral change — the dropped line was a no-op under the `<target>/**` rule. Running `init --force` on a v2.6.0 install simply produces a tidier 3-line block. Consumers who never run `init --force` keep the 4-line block forever without issue.

## [2.6.0] - 2026-05-09

Phase P: Auto-heal and production hardening. Collapses the consumer-repo install footprint to a single tracked file (`go.md`) plus the tracked config; everything else is gitignored bundled data, repopulated on demand by a new self-contained `heal` command that runs invisibly before every other invocation. Bundled with a subset of post-1.0 production-readiness items: `SECURITY.md`, `CONTRIBUTING.md`, tightened `dependabot.yml`, and a CI-workflow PR-readiness audit.

### Added
- **`project-guide heal` command** (`project_guide/cli.py`) — repairs the install in place: detects drift between the bundled package templates and the on-disk template tree, then creates missing files and refreshes stale ones. Silent when there is nothing to do (exit 0, no stdout); prompts `Update? [Y/n]` on drift and exits 1 on decline. Hard error on missing `.project-guide.yml` with the exact message `Missing .project-guide.yml — run 'project-guide init' to bootstrap the project.`. Honors the `--no-input` contract: under `--no-input` / `PROJECT_GUIDE_NO_INPUT` / `CI=1` / non-TTY stdin the prompt is replaced with auto-yes plus a non-suppressible one-line stderr notice (`Auto-healing N templates under --no-input.`). `SchemaVersionError` propagation mirrors `update`'s older/newer guidance. (Stories P.a, P.c)
- **Group-level auto-heal hook** (`HealGroup(click.Group)` in `project_guide/cli.py`) — every `project-guide` invocation, **including `--help` and `--version`**, runs the heal drift-detection + prompt path before dispatching the requested subcommand. Implemented by overriding `Group.main()` so the hook fires ahead of `make_context` / arg parsing (which is what catches eager flags). Silent in the steady state; declining the prompt does not block the original subcommand. Recursion across nested `project-guide` subprocess invocations is prevented by `PROJECT_GUIDE_HEALING=1` in `os.environ`, set by `_apply_heal()` before any write. The hook also inherits the `--no-input` skip-input contract via env / TTY signals. (Story P.b, extended in P.c)
- **`SECURITY.md`** — vulnerability reporting policy at repo root. Supported-versions table (latest minor only), GitHub Security Advisories as the private reporting channel, ~7-day acknowledgement expectation, and a "Threat model" section enumerating the narrow attack surface (no secrets, no network calls, local-filesystem only). (Story P.e)
- **`CONTRIBUTING.md`** — canonical dev guide at repo root: pyve two-environment setup, code-style commands, test conventions (`pyve test`, 85% coverage, mode-render parametrized regression test), PR process (fork → branch → green CI → review), substantive-contributions guidance (scope via stories before opening a PR for non-trivial work), and the `bump-version` end-of-phase release process. (Story P.f)
- **README.md** — new `### heal` Command Reference section, "Auto-Heal" feature bullet, dedicated `## Security` section pointing at `SECURITY.md` and GitHub Security Advisories. (Stories P.a–P.i)

### Changed
- **`.gitignore` writer (`_ensure_gitignore_entry()` in `project_guide/cli.py`)** — inverted policy: ignore everything under `target_dir` *except* `go.md` and `.bak.*` backups. Eliminates the ~35-file install footprint from consumer-repo `git status` and PR reviews. `go.md` must remain non-gitignored because IDE-integrated LLMs (Cursor, Claude Code, etc.) typically hide gitignored files from the LLM's view. The writer is now idempotent and recognizes prior blocks (canonical form, legacy `.bak.*`-only form, legacy `<target>/go.md` line) for clean rewrite; foreign hand-customized blocks are left untouched with a stderr warning. Migration for pre-Phase-P consumer repos: `project-guide init --force`. (Story P.d)
- **`.github/dependabot.yml`** — added minor+patch grouping per ecosystem (one weekly PR per ecosystem instead of one per dependency), commit-message prefixes (`chore(ci)` for github-actions, `chore(deps)` for pip), and aligned labels with `dependencies` + `ci`. Majors land as separate PRs so a breaking upgrade is easy to revert. (Story P.g)
- **`README.md` Development and Contributing sections** — slimmed to brief quick-references that point at `CONTRIBUTING.md` as canonical; replaced stale `pip install -e ".[dev]"` / `pytest tests/` commands with the dogfooded pyve canonical forms (`pyve run pip install -e .`, `pyve test`, `pyve testenv run ruff check ...`). (Story P.f)
- **`docs/specs/features.md`** — added FR-14 (Auto-Heal & Self-Repair Install) covering the heal command, the auto-hook, the recursion guard, the inverted gitignore policy, and the IDE-LLM-visibility constraint. Updated FR-8 to add `heal` to the list of commands that respect the `--no-input` contract. Updated Inputs / Command Line, Outputs / File Structure, and Acceptance Criteria. (Story P.i)
- **`docs/specs/tech-spec.md`** — added `heal`, `archive-stories`, and `bump-version` to the CLI Design / Commands table; documented `_apply_heal`, `_run_pre_invoke_hook`, and `HealGroup` under Key Functions; added the Auto-Heal Group Hook section under Cross-Cutting Concerns; updated `.gitignore` Management to the new policy with rationale. (Story P.i)
- **`docs/specs/project-essentials.md`** — appended five new sub-sections: auto-heal hook contract, inverted gitignore policy, IDE-LLM visibility constraint, `heal` vs. `update` vs. `init` division of labor, and the heal `--no-input` auto-yes notice. (Story P.i)

### Verified (no code changes)
- **`.github/workflows/ci.yml`** and **`test.yml`** are PR-ready — `pull_request` triggers present, no `continue-on-error: true` shortcuts, lint and tests are mandatory, all matrix legs required. The green-CI expectation is documented in `CONTRIBUTING.md` (informal until branch protection is enabled). (Story P.h, audit-only)

## [2.5.15] - 2026-05-07

### Changed
- **`project_guide/cli.py:_MODE_CATEGORIES`** — Renamed two section labels to reflect the project lifecycle's one-time-vs-repeated split: `"Planning"` → `"Project Planning"` (one-time-per-project), `"Post-Release"` → `"Release Planning"` (repeated per release). Moved `plan_phase` from Project Planning to Release Planning (each release ships at least one phase, so phase planning is repeated work). `plan_production_phase` (added in O.p) is now registered under Release Planning. Added inline comments documenting the rationale for each section group.
- **`project_guide/cli.py:_CATEGORY_ORDER`** — Reordered to match the lifecycle flow: `Getting Started → Project Planning → Scaffold → Coding → Debugging → Documentation → Refactoring → Release Planning → Other`. Previously the order was alphabetic-ish; now it reads top-to-bottom as "what you do first → what you do last."
- **`project_guide/cli.py:set_mode` docstring** — Expanded from a single line ("Set or show the active development mode.") to a multi-paragraph block enumerating the three invocation paths: positional (`project-guide mode <name>` sets and exits), `--no-input` (prints annotated mode list and exits — the discovery / automation path), and bare invocation (interactive numbered menu, TTY only). Also documents the section ordering, the per-mode annotation markers (→ / ✓ / ✗), what `--verbose` adds, and the auto-enable conditions for `--no-input` (CI=1 or non-TTY stdin).
- **`README.md`** — Updated the **Available Modes** section to match the new section labels and ordering. Renamed "Planning Modes" → "Project Planning Modes" (one-time-per-project) and "Post-Release Modes" → "Release Planning Modes" (repeated per release). Added `plan_phase` (pre-1.0) and `plan_production_phase` (post-1.0 mandatory) to Release Planning Modes, removed `plan_phase` from Project Planning. Added a one-line description above each section explaining its lifecycle role.
- **`docs/specs/features.md`** FR-11 — Updated the section-grouping bullet to use the new labels and ordering.

## [2.5.14] - 2026-05-07

### Added
- **`plan_production_phase` mode** — derived from `plan_phase` and mandatory for every phase once the package version is at v1.0.0 or beyond (per the cadence rule from O.o). Adds: a Production-readiness checklist walk (branch protection, SECURITY.md, CONTRIBUTING.md, Dependabot, trusted publisher, mandatory CI, bundled-release cadence) sourced from `developer/best-practices-guide.md`'s Velocity-vs-Production section; a breaking-change negotiation step that walks each anticipated breaking change and asks whether it substantively breaks user expectations or is technically-but-trivially breaking (worked example: log-format change when logs aren't a core consumer capability); explicit version-bump target recorded in the phase plan. New file `project_guide/templates/project-guide/templates/modes/plan-production-phase-mode.md` (developer renamed the orphan `production-mode.md` to `plan-production-mode.md`, then again to its final name as part of this story). Registered in `.metadata.yml` and `cli.py:_MODE_CATEGORIES` (under "Post-Release"; will move to "Release Planning" in Story O.q).
- **`project-guide bump-version <X.Y.Z>` CLI command** — deterministic helper parallel to `archive-stories`. Updates `pyproject.toml`'s `[project] version`, an auto-detected `__version__` source file (tries `<package>/version.py`, `<package>/_version.py`, `<package>/__init__.py`, plus `src/<package>/...` variants), and inserts a fresh `## [X.Y.Z] - YYYY-MM-DD` heading just below `## [Unreleased]` in `CHANGELOG.md`. Idempotent on re-run for the same version (date is refreshed; body preserved). Validates semver format. Honors the `--no-input` contract (missing positional fails loud with exit 2 and the canonical error message); honors `--quiet` (suppresses success-path stdout, errors and warnings still emit on stderr). Used at end-of-phase when shipping a bundled release per the cadence rule.

### Changed
- **`project_guide/templates/project-guide/templates/modes/plan-phase-mode.md`** — Inserted a new **Step 1: Verify this is the right mode** that halts and recommends `plan_production_phase` if the package version is `>= 1.0.0`. Renumbered subsequent steps to 2–8 and updated internal cross-references ("from step 1" → "from step 2"; "see step 5" → "see step 6"). Updated Prerequisites prose to name `plan_phase` as pre-1.0-only.
- **`project_guide/templates/project-guide/.metadata.yml`** — Registered `plan_production_phase` mode entry (parallel structure to `plan_phase`). Updated `plan_phase` description to call out it is pre-1.0-only.
- **`project_guide/cli.py:_MODE_CATEGORIES`** — Registered `plan_production_phase` under "Post-Release" (the section will be renamed to "Release Planning" in Story O.q).
- **`project_guide/templates/project-guide/developer/best-practices-guide.md`** — Velocity-vs-Production section gains a "How project-guide enforces the switch" paragraph cross-referencing `plan_production_phase` mode (which walks the readiness checklist), `plan_phase`'s pre-1.0-only redirect, and `bump-version` as the end-of-phase release helper.

## [2.5.13] - 2026-05-07

### Changed
- **`project_guide/templates/project-guide/templates/artifacts/stories.md`** — Added a new top-level **`## Version Cadence`** section as static baseline content (parallel to file-header-conventions in `project-essentials.md` from O.h, channel-discipline in `tech-spec.md` from O.k, and CI/CD-summary in `tech-spec.md` from O.l). Documents the project-guide default cadence: every story belongs to a phase; per-story bumping is bugfix=patch, feature=minor, breaking=major (post-1.0 only via `plan_production_phase`); phase-bundling option lets stories run unversioned during work with one tag at end-of-phase; no out-of-order implementation. Pre-1.0 starts at v0.1.0; post-1.0 must use `plan_production_phase`. Closes a downstream failure mode where the LLM extrapolated patch-bumps from `pyproject.toml`'s `0.0.1` placeholder for 48 stories before randomly switching to minor.
- **`project_guide/templates/project-guide/templates/modes/_header-cycle.md`** — Added a Version Cadence quick-reference (the four bump-magnitude bullets + bundling option + no-extrapolation rule) and a separate Out-of-scope items rule (when announcing a story, briefly summarize any "Out of scope" items so the developer can opt some back in). Loads with every cycle mode (`code_direct`, `code_test_first`, `debug`).
- **`project_guide/templates/project-guide/templates/modes/plan-phase-mode.md`** step 3 — Extended the "Out of scope" bullet so the LLM walks each item with the developer; out-of-scope is a negotiation, not a unilateral declaration. Primary site for this rule (cycle-header summary is the backstop).
- **`project_guide/templates/project-guide/templates/modes/plan-stories-mode.md`** step 3 + Story Writing Rules — Cross-references the Version Cadence rule. Story A.a starts at v0.1.0; most initial-planning stories are features → minor; bugfixes are patch; major is forward-deferred to `plan_production_phase`.
- **`project_guide/templates/project-guide/templates/modes/code-direct-mode.md`** Step 8 + Velocity Practices, **`code-test-first-mode.md`** Step 7 — Bump-version step now references the Version Cadence rule and forbids extrapolation from `pyproject.toml`'s current version.
- **`project_guide/templates/project-guide/templates/modes/debug-mode.md`** Step 5 — Added a one-line note that bug-fix stories take patch bumps per the cadence rule (or run unversioned if phase-bundling is in play).

## [2.5.12] - 2026-05-06

### Changed
- **`project_guide/templates/project-guide/templates/modes/code-direct-mode.md`** and **`code-test-first-mode.md`** Cycle Steps — Inserted a new **Step 2: Identify and announce** between Read and Implement. Before implementing anything, the LLM must announce the intended next story to the developer (story ID, title, one-line scope summary) and wait for "go" — a *precise* confirmation of that specific story — or redirect to a different story. Renumbered subsequent steps (`code_direct` cycle is now 11 steps; `code_test_first` is now 10 steps). The final Wait step extended with explicit "go re-enters the cycle at Step 1" language so the cycle's two gates (announce-before-implement, present-before-next-cycle) are symmetric. Same family of bug as Stories O.f / O.l / O.m: a missing read-and-announce-before-acting gate let the LLM pick a story silently after a mode switch and start implementing whatever it thought was next.
- **`code-direct-mode.md` Story Ordering section** — Reframed the "If unclear which story is next, ask" bullet so it reads as guidance for the Step 2 announce (surface ambiguity in the announce, e.g., "I see two candidates: Story B.c and Story B.d — which?"), not a fallback the LLM may skip when it *thinks* it knows.

## [2.5.11] - 2026-05-06

### Changed
- **`project_guide/templates/project-guide/templates/modes/scaffold-project-mode.md`** — Inserted a new **Step 1: Read the project-specific spec** that mandates reading Story A.a in `docs/specs/stories.md` and `docs/specs/tech-spec.md` *before* any scaffolding work. Names Story A.a as the authoritative source for build backend, version, dependencies, package layout, console scripts, dev tooling, and any other project-specific prescriptions. Frames the subsequent steps as **generic defaults** that apply only when Story A.a is silent; on conflict, Story A.a wins. Renumbered the existing 9 steps to 2–10. Substep references updated (`8a`/`8b` → `9a`/`9b`; "steps 1–3" → "steps 2–4").
- **Step 4 (Package Manifest)** — Reframed each concrete default as a fallback. Build backend ("use what Story A.a prescribes; do not pick a default without checking") was previously unspecified and led downstream LLMs to silently default to setuptools when Story A.a prescribed hatchling. Version is now "per Story A.a; default to `0.1.0` only if A.a is silent" — observed downstream defaulting to `0.1.0` against an A.a-prescribed `0.0.1`. Added explicit prompts for runtime deps, optional-dep extras, console scripts, entry-point groups, and dev-tool config (ruff/mypy/pytest) sourced from the spec.
- **Step 5 (README.md)**, **Step 6 (CHANGELOG.md)**, **Step 7 (.gitignore)** — Added one-liner reminders that Story A.a / `tech-spec.md` may prescribe additional sections / seeded entries / patterns that override the generic recipe.
- **Step 8 (formerly Step 7, Mark Story A.a Done)** — Renamed to **"Verify Story A.a is Implemented and Mark Done"** and reframed the preamble. Reading Story A.a here is now a **verification gate** — by this point every task should already be implemented (Step 1 mandated full read; Steps 2–7 implemented A.a's prescriptions). If unmet tasks remain, the LLM loops back and implements them rather than mass-marking `[x]` or surfacing a "want to extend now or leave [Planned]?" delta for developer guidance. Same family of bug as plan_features (O.f) and plan_stories (O.l) — read the project-specific spec first, not at the end.

## [2.5.10] - 2026-05-06

### Changed
- **`project_guide/templates/project-guide/templates/modes/plan-stories-mode.md`** — Three tightenings to prevent observed `plan_stories` missteps:
  1. **Prerequisites no longer instruct the LLM to confirm "approval".** The presence of `concept.md` / `features.md` / `tech-spec.md` and the developer's choice to invoke this mode imply approval; the natural pause-on-summary at the present-for-approval step is the rejection path. Mirrors the `plan_features` tightening from Story O.f (v2.5.4).
  2. **Standalone CI/CD question removed.** The previous "Will this project need CI/CD automation?" prompt is replaced with a one-liner pointing the LLM at `tech-spec.md`'s `## CI/CD Automation` section as the authoritative source. Permission to ask the developer is preserved only when the spec is silent or genuinely ambiguous.
  3. **New Step 1 ("Verify this is the right mode") with three deterministic checks** — existing `### Story` headings in `stories.md`, substantive source beyond Phase A scaffolding, or `git log` deeper than ~10 commits. If any check trips, the LLM halts and recommends `plan_phase` (optionally preceded by `refactor_plan`) rather than silently overwriting prior planning work. Existing read/generate/approve steps renumbered to 2/3/4.
- **`project_guide/templates/project-guide/templates/modes/plan-tech-spec-mode.md`** step 2 — Added `ci_cd_automation` to the technical-details list. One-line summary of CI/CD scope (lint/test on push, coverage reporting, automated registry publishing on tag); "None" is a valid answer. The single fact `plan_stories` reads to decide whether to include a Phase G — captured once during plan-tech-spec rather than scattered across packaging/distribution and cross-cutting breadcrumbs.
- **`project_guide/templates/project-guide/templates/artifacts/tech-spec.md`** — New top-level **CI/CD Automation** section with `{{ci_cd_automation}}` placeholder, between Packaging and Distribution and the document end. Pinned by `test_tech_spec_artifact_has_ci_cd_automation_section` and located so `plan_stories` can deterministically locate it during inference.

## [2.5.9] - 2026-05-06

### Changed
- **`project_guide/templates/project-guide/templates/artifacts/tech-spec.md`** — Cross-Cutting Concerns section gains a static **Logging and User Output** subsection naming `rich`/`logging` (Python) and cross-language analogues (`chalk`/`pino`, `pterm`/`slog`, `console`/`tracing`). The rule (user-facing output goes to `rich`; structured operational events including warnings/retries go to stdlib `logging`) is mandatory baseline content the LLM does not negotiate per-project; it ships as default tech-spec content so `plan_stories` reads it and stories carry the discipline into code modes. The original `{{cross_cutting}}` placeholder is preserved under a new **Additional Cross-Cutting Concerns** subheading for project-specific cross-cutting concerns gathered during plan-tech-spec mode's developer Q&A.
- **`project_guide/templates/project-guide/developer/best-practices-guide.md`** — New **Logging and User Output** section between Error Handling and Open Source Sustainability. Captures the rich/logging discipline with rationale, the `console.print(...)` anti-pattern for operational warnings, and cross-language analogues. The bundled developer doc that ships with the package via `init`.
- **`project_guide/templates/project-guide/templates/modes/_header-common.md`** — Rules block gains a new bullet (sibling to the v2.5.7 bundled-artifact-templates anchor) naming `docs/project-guide/` as **install output, not source**: hand-edits are silently lost on `project-guide update` / `project-guide mode` invocations unless the file is first marked overridden via `project-guide override <file> "<reason>"` (reverse: `project-guide unoverride <file>`). The LLM is instructed to flag conflicts as substantive and surface three resolution paths to the developer — override locally, file an issue/PR at `https://github.com/pointmatic/project-guide`, or wait for guidance — rather than editing silently. The dogfooding-specific "edit source-of-truth template" path stays in this repo's `docs/specs/project-essentials.md` (where it already lived); only universal moves go into the shared header.
- **`docs/specs/project-essentials.md`** (this repo, dogfooding) — Augmented the existing dogfooding rule's "Installed copy" bullet to mention the `project-guide override`/`unoverride` escape hatch alongside the existing "Never hand-edit" guidance, with a note that for dogfooding work in this repo the override path is rarely the right answer (the fix lives in the source-of-truth template).

## [2.5.8] - 2026-05-05

### Changed
- **`project_guide/templates/project-guide/templates/artifacts/pyve-essentials.md`**, **`developer/python-editable-install.md`**, and **`templates/modes/plan-tech-spec-mode.md`** — Updated all `pyve testenv` invocations from the stale **flag form** `pyve testenv --install -r requirements-dev.txt` to the current **subcommand form** `pyve testenv install -r requirements-dev.txt`. The pyve CLI now exposes `init`, `install`, `purge`, and `run` as subcommands of `testenv` (per `pyve testenv --help`); the `--install` flag is gone. Six occurrences across two artifacts and one mode template; `.archive/*.md` files retain the historical form.
- **`pyve-essentials.md`** and **`developer/python-editable-install.md`** — Added the required `pyve testenv init` step before `pyve testenv install` / `pyve testenv run` invocations. Those subcommands do not auto-create `.pyve/testenv/venv/` and fail until `init` runs once. `pyve-essentials.md` gains a new "Initialize the testenv (one-time)" bullet citing the upstream [pyve `testenv` subcommand reference](https://pointmatic.github.io/pyve/usage/#testenv-subcommand). `python-editable-install.md` gets the init step in both runnable code blocks plus a new "Common Mistakes" table row for the env-doesn't-exist failure mode.

## [2.5.7] - 2026-05-04

### Changed
- **`project_guide/templates/project-guide/templates/modes/{plan-concept,plan-features,plan-stories,plan-tech-spec,plan-phase,scaffold-project,refactor-plan,refactor-document}-mode.md`** — Every reference to a bundled artifact template now uses the project-root-relative path `docs/project-guide/templates/artifacts/<file>.md` (installed by `project-guide init`, refreshed by `project-guide update`) instead of the ambiguous bare `templates/artifacts/<file>.md` form. The bare form had no base directory the LLM could discover from inside a downstream project, leading at least one observed session (nbfoundry) to attempt `find / -path '*/project_guide*/templates/...'` before being interrupted.
- **`project_guide/templates/project-guide/templates/modes/_header-common.md`** — Added a Rules-block anchor sentence naming `docs/project-guide/templates/artifacts/` as the canonical install location and explicitly forbidding filesystem / `site-packages` / install-location searches. Loads with every mode so the rule is always-context.
- **`project_guide/templates/project-guide/templates/artifacts/project-essentials.md`** — Added a project-guide-consumer hint under the **Architecture quirks** category naming the install location and listing the environment managers (pip, poetry, uv, conda, mamba, micromamba, pyve, pixi) that all stash `site-packages` differently — the canonical "why the project-root-relative path is the only environment-agnostic answer" rationale.

## [2.5.6] - 2026-05-04

### Changed
- **`project_guide/templates/project-guide/templates/modes/{plan-tech-spec,plan-phase,refactor-plan,scaffold-project}-mode.md`** and **`templates/artifacts/project-essentials.md`** — Reframed the **File header conventions** section as mandatory baseline content the LLM pre-fills automatically from `concept.md` / `LICENSE` / `pyproject.toml`, rather than as optional starter content gated on developer-provided "must-know facts". `plan_tech_spec` step 5 no longer treats `project-essentials.md` creation as conditional on extra facts; step 6 is unconditional and requires substituting `<YEAR>` / `<OWNER>` / `<LICENSE>` and removing the trailing TODO note. `plan_phase` step 7 create branch and `refactor_plan` Step F.3 create path each gain the same canonical pre-fill instruction. `scaffold_project` step 8 split into 8a (verify or create with concrete file headers using values from steps 1–3) and 8b (existing memory-review behavior). Artifact comment block replaces the "An empty file is acceptable — omit this file entirely" guidance with "This file is **always** created — file headers are mandatory baseline content; additional sections are optional". Closes a recurring failure where the LLM (observed in a downstream nbfoundry session) asked the developer whether to include SPDX/copyright headers despite the license/copyright being already authoritative in `concept.md`.

## [2.5.5] - 2026-05-02

### Changed
- **`project_guide/templates/project-guide/templates/artifacts/{concept,features,tech-spec,brand-descriptions}.md`** — Extended each artifact's cross-reference paragraph with a pointer to `docs/project-guide/go.md` for the workflow steps tailored to the current mode (cycle steps, approval gates, conventions), with a re-read hint for mode changes and post-compaction. Matches the v2.5.4 change to `stories.md`; ensures an LLM dropped into a session with any sibling spec open is reminded that mode-tailored guidance lives in `go.md`.
- **`project_guide/templates/project-guide/templates/artifacts/{concept,features,tech-spec,stories,brand-descriptions}.md`** — Cross-reference paragraphs converted from backtick code spans to markdown local links (e.g. `` `concept.md` `` → `` [`concept.md`](concept.md) ``), making sibling-spec references click-navigable in IDEs and on GitHub. The `docs/project-guide/go.md` reference uses a `../project-guide/go.md` relative path so the link resolves from the rendered artifact's location at `docs/specs/`.

## [2.5.4] - 2026-05-02

### Changed
- **`project_guide/templates/project-guide/templates/modes/plan-features-mode.md`** — Reframed Prerequisites so `docs/specs/concept.md` is named as the primary source for almost every field, with each prerequisite annotated with where it usually comes from (`concept.md` or `LICENSE`). Inserted a new Step 1 ("Read what already exists before asking anything") that mandates reading `concept.md` in full plus referenced sibling documents and any `LICENSE` file *before* presenting the developer with prerequisites or questions; renumbered the existing gather/generate/approve steps accordingly. Step 2 explicitly forbids enumerating prerequisites or asking for items `concept.md` already supplies, and requires any genuinely-missing items to be asked in a single consolidated round. Closes a recurring failure where the LLM treated the Prerequisites list as a checklist to interrogate the developer about, even when the upstream artifact already supplied the answers.
- **`project_guide/templates/project-guide/templates/artifacts/stories.md`** — Cross-reference paragraph extended with a pointer to `docs/project-guide/go.md` for the workflow steps tailored to the current mode (cycle steps, approval gates, conventions), with a re-read hint for mode changes and post-compaction. Helps an LLM dropped into a session with `stories.md` open pick up the mode-tailored guide rather than proceeding without it.

## [2.5.3] - 2026-05-02

### Changed
- **`project_guide/templates/project-guide/templates/modes/debug-mode.md`** — Restructured the 5-step Structured Debugging Workflow so Step 5 reads as a named approval gate rather than a wrap-up. Step 5 renamed to *"Document the Fix in `stories.md` (Approval Gate)"* with a single nameable output artifact (the new story); the previous bundle of "Document and Prevent" actions is split into the gate artifact (the story write-up) and a secondary prevention scan. Step 4's Output line now ends with *"but the cycle is not complete; proceed to Step 5"*. The Debugging Checklist moved from its location after the Case Study to immediately after Step 5 and is framed as a mandatory pre-gate run-through. Golden Rule reframed to a four-beat mantra (*"…Document the fix in `stories.md` fourth"*) so the rhythmic anchor includes Step 5. Added an anti-pattern entry *"Declaring the Fix Complete After Step 4"*. Closes a recurring failure where LLMs treated Step 4 ("working code with passing tests") as terminus and skipped the project-record write-up.

## [2.5.2] - 2026-05-01

### Changed
- **`project_guide/templates/project-guide/templates/modes/code-direct-mode.md`** and **`code-test-first-mode.md`** — Cycle step 1 now explicitly mandates a fresh `Read` of `docs/specs/stories.md` from disk at the start of every cycle, calling out that the developer may have edited the file since the LLM last viewed it and that prior conversation context must not be relied on. Closes a recurring drift where the LLM worked from a stale in-context snapshot of `stories.md` after the developer made manual edits and said "go".

## [2.5.1] - 2026-04-30

### Changed
- **`project_guide/cli.py`** — Tightened `--quiet` / `-q` on `init`, `update`, and `purge` for embedded callers (e.g. pyve): **successful runs emit nothing to stdout**; errors and material warnings use **stderr** (including render/update warnings, overridden-file notices, `init --force` config backup notice, and purge “not found (skipped)” hints). Exit codes unchanged. `--quiet` composes with `--no-input` for unattended refreshes without downstream stdout filtering.
- **`project_guide/templates/project-guide/templates/artifacts/stories.md`** — Clarifies that a story **title** includes **`vX.Y.Z` only when that story ships the package version bump**; doc-only stories omit the version in the title (see `project-essentials.md` in each project for full commit/changelog conventions).

### Fixed
- **`project_guide/cli.py`** — The “Available files: …” hint after an unknown template path now prints to stderr on **`update`** and **`override`** for consistency with other diagnostics.

### Documentation
- **`docs/specs/features.md`** — FR-9 and Inputs bullets updated for the machine-quiet contract; acceptance criterion #8 clarified.
- **`docs/specs/project-essentials.md`** (dogfood) — **Commit and version style**: `stories.md` headings and commit-message examples aligned with the bundled artifact; injected into every rendered `go.md`.

## [2.5.0] - 2026-04-17

### Changed
- **`project_guide/templates/project-guide/templates/artifacts/pyve-essentials.md`** — Renamed from `project-essentials-pyve.md` to signal it is a package-versioned bundled artifact (not a project-owned file). Subsection headings demoted from `###` to `####` so they nest under the new `### Pyve Essentials` wrapper rendered by `_header-common.md`.
- **`project_guide/render.py`** — New `_read_pyve_essentials(templates_subdir, pyve_installed)` helper reads the bundled artifact from the template tree and passes its content as the `pyve_essentials` Jinja context variable. When pyve is installed, every `go.md` now auto-renders the bundled pyve rules under `## Project Essentials > ### Pyve Essentials` — upstream improvements flow to every project on the next `project-guide mode <name>` invocation without any one-shot merge step.
- **`project_guide/templates/project-guide/templates/modes/_header-common.md`** — `{% if project_essentials or pyve_essentials %}` wrapper; renders `project_essentials` content first (if any), then `### Pyve Essentials` subsection (if pyve installed). The `## Project Essentials` wrapper still renders when only pyve content is present, so the subsection always has a parent heading.
- **`project_guide/templates/project-guide/templates/artifacts/project-essentials.md`** — Comment block updated to document `pyve-essentials.md` as a sibling bundled artifact and explicitly instruct authors NOT to duplicate pyve-specific rules into this file.
- **`project_guide/templates/project-guide/templates/modes/refactor-plan-mode.md`** — Step F.2 examples updated: environment-manager and runtime/dev-split examples use `hatch`/`tox` rather than `pyve`, and note that pyve-specific rules are auto-rendered from the bundled artifact (do NOT duplicate into `project-essentials.md`).
- **`docs/specs/features.md`** — FR-13 retitled "Pyve Detection and Auto-Rendered pyve-essentials.md"; body rewritten to describe the auto-render contract instead of the former one-shot merge.
- **`docs/specs/tech-spec.md`** — `render.py` module description expanded with the new `_read_project_essentials` and `_read_pyve_essentials` helpers and the `project_essentials` / `pyve_essentials` context variables.
- **`docs/specs/project-essentials.md`** (dogfood) — Removed the "Workflow rules — pyve environment conventions" and "LLM-internal vs. developer-facing invocation" sections; they now auto-render from the bundled `pyve-essentials.md`.

### Removed
- **`scaffold-project-mode.md`** — "Merge Pyve Project Essentials" step (the one-shot merge at scaffold time) removed; pyve content is auto-rendered instead.
- **`plan-tech-spec-mode.md`** — "Pyve users" merge paragraph in step 6 removed.

### Migration
Existing downstream projects may have pyve sections merged into their `docs/specs/project-essentials.md` from pre-v2.5.0 scaffold. The duplication is inert (content renders once from each source and the other is a plain re-render). Users may optionally delete the merged-in pyve sections to defer to the bundled source of truth and pick up future upstream improvements automatically.

## [2.4.19] - 2026-04-17

### Fixed
- **`project_guide/actions.py:render_fresh_stories_artifact`** — Constrained the N.s placeholder validator to the Jinja-rendered output. The scan now runs immediately after `template.render(...)` and before the `## Future` section is spliced in verbatim. Previously it ran on the final output, so any literal `{{ name }}` in the user-authored Future prose (e.g. the existing "Template & Rendering" deferred item in this project's own `stories.md`) was misread as an unrendered placeholder and blocked `archive-stories`. The guard still fails loudly on genuinely missing context variables in the rendered header.

## [2.4.18] - 2026-04-16

### Added
- **`project_guide/config.py`** — New `project_name: str = ""` field on `Config`, round-tripped through YAML save/load.
- **`project_guide/runtime.py`** — `_detect_project_name_from_pyproject()` helper reads `[project].name` from `pyproject.toml` when present; returns `None` otherwise. Shared `UNRENDERED_PLACEHOLDER_RE` pattern extracted here so `render.py` and `actions.py` validate through the same contract.
- **`project_guide/cli.py:init`** — `--project-name` option with a four-level resolution chain (CLI flag → `PROJECT_GUIDE_PROJECT_NAME` env var → `pyproject.toml` → `Path.cwd().name`) persisted into `.project-guide.yml`.
- **`project_guide/cli.py:archive_stories_cmd`** — Merges `config.project_name` into the archive context so fresh `stories.md` headers render correctly even when the old `stories.md` had no parseable header. Prints a drift warning (stderr, exit 0) when `Path.cwd().name` differs from `config.project_name`.
- **`project_guide/actions.py:render_fresh_stories_artifact`** — Post-render placeholder validator raises `ActionError` listing the offending variable name(s) and the template when any `{{ name }}` shape survives the render pass. Fixes the silent placeholder leak that prompted Story N.s.

### Changed
- **`docs/specs/tech-spec.md`** — Documented the `project_name` field, resolution chain, and archive-stories context merge.
- **`docs/specs/project-essentials.md`** — Added the N.s resolution chain bullet to `### Config schema versioning`.

## [2.4.17] - 2026-04-16

### Added
- **`templates/artifacts/project-essentials-pyve.md`** — New `### LLM-internal vs. developer-facing invocation` subsection teaching the LLM to keep `pyve run` (and similar environment wrappers) out of developer-facing command suggestions. The wrapper is only needed because the LLM's Bash-tool shell does not auto-activate `.venv/`; the developer's shell typically does. Placed immediately after the environment-conventions bullet list and before the Python invocation rule.
- **`docs/specs/project-essentials.md`** — Dogfooded: same subsection merged into this project's project-essentials so every rendered `go.md` surfaces the rule under `## Project Essentials`.

## [2.4.16] - 2026-04-16

### Changed
- **`project_guide/cli.py:init`** — Relocated the `.project-guide.yml.bak.<timestamp>` backup from `update`'s `SchemaVersionError("older")` handler into `init --force`. The backup now fires at the destructive-overwrite site itself, making it idempotent (one backup per refresh regardless of how the user got there) and extending coverage to `init --force` invocations that do not go through `update`. Backup only fires when the config already exists; a fresh `init --force` creates nothing to back up.
- **`project_guide/cli.py:update`** — The `SchemaVersionError("older")` handler no longer writes a backup; it prints a short message directing the user to `project-guide init --force`, where the backup is now performed. Fixes the backup-spam bug where repeated `update` invocations against an unresolved older-schema config produced a new timestamped backup on every run.
- **`docs/specs/tech-spec.md`** — Updated the `config.py` module description to record that `init` (not `update`) is the backup writer.
- **`docs/specs/project-essentials.md`** — `### Config schema versioning` section updated to describe the new recovery flow and name `init --force` as the sole backup site.

## [2.4.15] - 2026-04-16

### Added
- **`project_guide/exceptions.py`** — `SchemaVersionError(ConfigError)` exception with `direction: str` attribute (`"older"` or `"newer"`) so command handlers can distinguish config-schema mismatch from other config errors.
- **`project_guide/config.py`** — `SCHEMA_VERSION = "2.0"` module-level constant and `_check_schema_version()` helper. `Config.load()` now validates the loaded `version` field against `SCHEMA_VERSION` using `packaging.version.Version` and raises `SchemaVersionError` on mismatch. Absent `version` field defaults to `SCHEMA_VERSION` (backwards-compatible).
- **`project_guide/cli.py:update`** — Catches `SchemaVersionError`: on `"older"` mismatch, copies `.project-guide.yml` to `.project-guide.yml.bak.<timestamp>` and directs the user to run `init --force`; on `"newer"` mismatch, instructs the user to upgrade project-guide. Exits 1 in both cases.

### Changed
- **`project_guide/cli.py:update`** — Broadened the `go.md` re-render guard: `go.md` is now re-rendered when it is missing, even if no template files changed this run. Previously guarded only by "any template files updated", which made `update` a silent no-op when `go.md` was manually deleted.
- **`project_guide/cli.py:status`** — Removed the now-unreachable `config.version == "1.0"` branch from the v1 migration notice (SchemaVersionError preempts it); `target_dir == "docs/guides"` path remains for layouts that never migrated.
- **`docs/specs/project-essentials.md`** — Added `### Config schema versioning` section documenting the bump policy (rename/remove/retype/semantic only; additive-with-default does not bump) and the `SchemaVersionError` behavior.
- **`docs/specs/tech-spec.md`** — Documented the schema-version guard in the `config.py` module description; added `SchemaVersionError` to the exception hierarchy diagram.

## [2.4.14] - 2026-04-16

### Changed
- **`.github/workflows/publish.yml`** — Added `push: tags: ['v*']` trigger so the build-and-publish job runs automatically on any version tag push, in addition to the existing GitHub Release publication trigger.

## [2.4.13] - 2026-04-16

### Added
- **`templates/modes/_header-common.md`** — Added universal rule to every mode's Rules block: when creating a new source file, add a copyright notice and license header using the comment syntax for that file type, referencing the project's `project-essentials.md` for specific values.
- **`templates/artifacts/project-essentials.md`** — Added `### File header conventions` starter section with language/syntax reference table, placeholder copyright/SPDX fields, and examples for Python, TypeScript, and HTML.
- **`templates/artifacts/project-essentials-pyve.md`** — Added `### Editable install and testenv dependency management` section covering the `pythonpath` vs testenv editable install decision, when each applies, and pyve purge survival.
- **`developer/python-editable-install.md`** — New developer reference guide covering editable installs for both general Python projects and pyve two-environment setups: `pythonpath` vs editable install decision guide, pyve-specific installation patterns, purge survival, and a common-mistakes table.

## [2.4.12] - 2026-04-16

### Changed
- **`docs/specs/features.md`** — Added `archive_stories` to FR-1 modes table; added Stories section to FR-5 status; added FR-8 through FR-13 covering `--no-input`, `--quiet`, story detection in status, mode listing with availability markers and interactive menu, per-project metadata overrides, and pyve detection; updated `.project-guide.yml` schema block with `test_first`, `pyve_version`, `metadata_overrides`; updated CLI inputs and acceptance criteria.
- **`docs/specs/tech-spec.md`** — Updated `Config` dataclass fields (added `test_first`, `pyve_version`, `metadata_overrides`); updated `metadata.py` module description to include `_apply_metadata_overrides`; updated `render.py` signature; updated filename conventions example.
- **`README.md`** — Updated mode listing output example; updated `mode` command options (`--verbose`, `--no-input`); updated `status` output description with Stories section; updated `update` and `purge` options (`--no-input`, `--quiet`); updated config schema with new fields.
- **`docs/site/user-guide/modes.md`** — Updated "Listing Modes" section with marker legend and interactive menu description.
- **`docs/site/user-guide/commands.md`** — Updated `mode`, `status`, `update`, and `purge` sections with new options and behavior.

## [2.4.11] - 2026-04-16

### Added
- **Memory reflection rule in every mode** — rule #7 added to the `_header-common.md` Rules block: before recording a new memory, the LLM must reflect whether the fact is project-specific (belongs in `docs/specs/project-essentials.md`), cross-project (belongs in LLM memory), or both. Propagates to all 15 modes via the shared header template.

## [2.4.10] - 2026-04-16

### Added
- **Memory Review step in `scaffold_project` mode** — penultimate step (before "Present for Approval") instructs the LLM to read its recorded project memories, evaluate which are project-specific, present candidates to the developer, and append confirmed items to `docs/specs/project-essentials.md`. Includes an escape hatch for empty or inaccessible memory stores. Step numbering is conditional on `pyve_installed` (9 without pyve, 10 with).

### Changed
- **Current mode name highlighted in `project-guide mode` listing** — the selected mode name is now rendered with a cyan background and black text (`fg='black', bg='cyan'`) so it stands out clearly from available (✓) and unavailable (✗) entries.

## [2.4.9] - 2026-04-15

### Added
- **Pyve detection in `init`** — runs `pyve --version` at init time; stores `pyve_version` (string or `null`) in `.project-guide.yml`. `pyve_installed` is derived from the stored value at every render call site (`init`, `set_mode`, `update`).
- **Bundled `project-essentials-pyve.md` artifact** — template at `templates/artifacts/project-essentials-pyve.md` covering the two-environment pattern, canonical invocation forms (`pyve run`, `pyve test`, `pyve testenv run`), the `python` vs `python3` asdf-shim rule, and the `requirements-dev.txt` story-writing convention.
- **`{% if pyve_installed %}` branch in `scaffold-project-mode.md`** — adds a "Merge Pyve Project Essentials" step (numbered 8) that copies pyve-specific rules into `docs/specs/project-essentials.md`; "Present for Approval" renumbers to 9 accordingly.
- **`{% if pyve_installed %}` branch in `plan-tech-spec-mode.md`** — step 6 now tells Pyve users to also read and merge `project-essentials-pyve.md` when creating `project-essentials.md`.

## [2.4.8] - 2026-04-16

### Added
- **`metadata_overrides` in `.project-guide.yml`** — projects can patch specific mode fields (`next_mode`, `files_exist`, `info`, `description`) without editing the bundled `.metadata.yml`. Partial patch semantics: unmentioned fields are unchanged. Unknown mode names or fields raise `MetadataError`. Overrides are applied at every `load_metadata()` call site (mode switch, status, archive-stories, update re-render).

## [2.4.7] - 2026-04-15

### Added
- **`project-guide mode` (no argument) now shows a prerequisite-annotated listing** — each mode is marked `→` (current), `✓` (all prerequisites met), or `✗` (unmet prerequisites, dimmed). Modes are grouped by category: Getting Started, Planning, Coding, Post-Release, Scaffold, Documentation, Debugging, Refactoring.
- **Interactive numbered menu on TTY** — on a real terminal, `project-guide mode` prompts for a selection number. Valid input switches mode + re-renders `go.md`; empty input cancels. Up to 3 attempts before exit 1. Under `--no-input`, `CI=1`, or non-TTY stdin, only the annotated listing is shown (exit 0).
- **`--verbose / -v` on `mode`** — shows unmet prerequisite file paths beneath each `✗` entry.
- **`--no-input` on `mode`** — skips the interactive menu and exits after printing the listing.

## [2.4.6] - 2026-04-15

### Added
- **Stories section in `project-guide status`** — shows total/done/in-progress/planned counts and the next unstarted story, parsed from `<spec_artifacts_path>/stories.md` via `project_guide/stories.py`. Section is omitted when the file is absent or contains no story headings (e.g. post-archive). `--verbose` adds a per-phase breakdown.

## [2.4.5] - 2026-04-15

### Added
- **`--quiet` / `-q` flag on `init`, `update`, and `purge`** — suppresses per-file progress lines. Errors, summaries (final counts), and explicit warnings (overridden-file notices) are always shown regardless of `--quiet`. Composes cleanly with `--no-input` for fully silent unattended runs.

## [2.4.4] - 2026-04-15

### Added
- **`--no-input` flag on `purge`** — skips the confirmation prompt when set, when `CI=1`, or when stdin is non-TTY. Pairs with `--force`; both suppress the prompt but via different mechanisms (`--force` is "yes, I'm sure"; `--no-input` is "non-interactive environment").
- **`--no-input` flag on `update`** — infrastructure parity with `init`. `update` has no interactive prompts today; the plumbing is in place for future additions.

## [2.4.3] - 2026-04-15

### Added
- **`--test-first` flag on `init`** — persists `test_first: bool` to `.project-guide.yml`. Resolved via `_resolve_setting` (CLI flag → `PROJECT_GUIDE_TEST_FIRST` env var → default `false`).
- **`test_first` Jinja2 context variable** — passed to all `render_go_project_guide` calls from `cli.py`. Planning modes that suggest a next coding step now use `{% if test_first %}code_test_first{% else %}code_direct{% endif %}`: `default-mode.md`, `plan-stories-mode.md`, `plan-phase-mode.md`.
- **`Config.test_first: bool`** — new field with load/save round-trip.

### Fixed
- **`plan-concept-mode.md` missing output step** — added step 4 "Write the completed document to `docs/specs/concept.md`." LLMs were asking where to write the output because no step named the destination file.

## [2.4.2] - 2026-04-15

### Added
- **`_resolve_setting` helper in `runtime.py`** — reusable four-level resolution chain (CLI flag → env var → config key → default). Type is inferred from `default`: bool settings use `_TRUTHY_ENV_VALUES` for env-var matching; str settings are returned as-is. Required foundation for `--test-first` (N.d) and any future settable prompt.
- **Tests in `tests/test_runtime.py`** — priority-order parametrized tests, full fallback chain, bool/str env resolution, and a contract test pinning the function signature.

## [2.4.1] - 2026-04-15

### Changed
- **`project-scaffold-mode.md` → `scaffold-project-mode.md`** — Renamed mode template file; mode key updated from `project_scaffold` to `scaffold_project` in `.metadata.yml`. `scaffold_project` follows the `<verb>_<noun>` convention established by every other mode.
- **Cross-references updated** — `default-mode.md`, `plan-stories-mode.md`, `docs/specs/features.md`, `docs/site/user-guide/modes.md`, `docs/site/user-guide/workflow.md`, `README.md`.

## [2.4.0] - 2026-04-15

### Changed
- **`code-velocity-mode.md` → `code-direct-mode.md`** — Renamed mode template file; mode key updated from `code_velocity` to `code_direct` in `.metadata.yml`. `code_direct` more clearly describes the mode (direct coding, no mandatory TDD) and pairs naturally with `code_test_first` under the `code_<style>` naming convention.
- **Cross-references updated** — `default-mode.md`, `code-test-first-mode.md`, `plan-stories-mode.md`, `docs/specs/project-essentials.md`, `docs/specs/features.md`, `docs/site/user-guide/modes.md`, `README.md`.
- **Tests updated** — `tests/test_render.py` and `tests/test_cli.py` renamed/updated all `code_velocity` references to `code_direct`.

## [2.3.9] - 2026-04-14

### Changed
- **`plan-stories-mode.md`** — Story A.a redefined from "Hello World" to "Project Scaffolding" (executed in `project_scaffold` mode); A.b is now Hello World; A.c is the stack spike. Added rule requiring every versioned story to include `Bump version to vX.Y.Z` and `Update CHANGELOG.md` as closing tasks. Updated Story Format example block and Phase A table to match.
- **`project-scaffold-mode.md`** — Added Step 7 to mark Story A.a `[Done]` in `stories.md` after scaffolding is complete (warns and continues if A.a is not found).

## [2.3.8] - 2026-04-14

### Fixed
- **Sequence-mode "Next Action" directive caused LLMs to skip steps** (Story M.i) — the `_header-sequence.md` include rendered a prominent "Next Action: Prompt the user to change modes" directive *before* the actual Steps section in all 9 sequence-mode templates. LLMs interpreted this as the primary instruction and jumped straight to suggesting a mode switch, ignoring the mode's steps entirely. Fix is belt-and-suspenders: (1) reworded `_header-sequence.md` from "Next Action / Prompt the user to change modes" to "After completing all steps below, prompt the user to change modes" so the directive is unambiguously post-completion, and (2) moved the `{% include "modes/_header-sequence.md" %}` from the top to the bottom of all 9 sequence-mode templates so the directive structurally appears after the steps.

### Changed
- **`_header-sequence.md`** — reworded from "Next Action / Prompt the user to change modes" to "After completing all steps below, prompt the user to change modes."
- **All 9 sequence-mode templates** — moved `{% include "modes/_header-sequence.md" %}` from top (before Prerequisites/Steps) to bottom (after all steps and reference material): `plan-concept-mode.md`, `plan-features-mode.md`, `plan-tech-spec-mode.md`, `plan-stories-mode.md`, `plan-phase-mode.md`, `archive-stories-mode.md`, `project-scaffold-mode.md`, `document-brand-mode.md`, `document-landing-mode.md`.

## [2.3.7] - 2026-04-14

### Changed
- **Minor tweaks to `plan-features-mode.md`** (Story M.h) — updated the planning mode template to be more aware of `concept.md` during feature planning. Updated pip-installed project-guide package to 2.3.6.

## [2.3.6] - 2026-04-11

### Changed
- **Approval-gate rule added universally** (Story M.g) — closes a dogfooding-discovered bug in the Phase M implementation where the assistant repeatedly proposed "commit first or continue?" footers at the end of story-approval summaries despite the system prompt's explicit `NEVER commit changes unless the user explicitly asks`. Root cause: the `code_velocity` mode template's **Velocity Practices** section mixed LLM-lane instructions ("tests run after every story", "fix linting immediately") with developer-lane conventions ("direct commits to main", "commit messages reference story IDs") in a single unlabeled bullet list. A reasonable LLM reading the mixed list concluded it should offer to do the commit, since the convention was "direct commits with story-ID messages". The fix restructures the templates to separate the two lanes and adds a universal approval-gate rule to `_header-common.md` that inherits into every mode.
- **`_header-common.md` **Rules** block** — added a new rule after "Never auto-advance past an approval gate":
  > At approval gates, present the completed work and wait. Do **not** propose follow-up actions outside the current mode step — in particular, do not prompt for git operations (commits, pushes, PRs, branch creation), CI runs, or deploys unless the current step explicitly calls for them. The developer initiates these on their own schedule.
  This is the universal fix. Because `_header-common.md` is included once by `llm_entry_point.md`, every rendered `go.md` now carries the rule — the 14 modes (`default`, `plan_*`, `refactor_*`, `archive_stories`, `project_scaffold`, `code_*`, `debug`, `document_*`) all inherit it without needing per-mode edits.
- **`code-velocity-mode.md` "Velocity Practices" restructured into two explicitly-labeled lanes** — was a single unlabeled bullet list, is now `**LLM's role in each cycle:**` (version bump, minimal process overhead, tests after every story, fix linting immediately, update CHANGELOG before presenting) and `**Developer's role (do NOT prompt for, offer, or initiate):**` (direct commits to main, commit messages reference story IDs, decides when to commit). The "do NOT prompt for, offer, or initiate" language in the developer-lane header is load-bearing — it tells future template authors *why* the lane exists, which is the discipline that prevents this class of bug from recurring. The developer-lane header's "Decides when to commit" bullet explicitly notes that multiple stories may be bundled into one commit at the developer's discretion, which is not the LLM's call to make or suggest.
- **`code-velocity-mode.md` step 9 ("Present") tightened** — was `**Present** the completed story to the developer for approval`, is now `**Present** the completed story concisely: what changed (files + line refs), verification results (test counts, lint status), and the suggested next story. Do not propose commits, pushes, or bundling options. Do not offer "want me to also…?" follow-ups.` This is belt-and-suspenders reinforcement of the universal rule — it catches LLMs that skim the header and jump to the cycle steps.
- **`code-test-first-mode.md` step 8 ("Present") tightened** with the same language. `code_test_first` does NOT get the Velocity Practices lane restructure because it has no analogous section — the TDD cycle steps go straight from "Wait" to "Red-Green-Refactor" theory to "Test Writing Guidelines", with no mixed-lane bullet list to untangle. The universal `_header-common.md` rule is still sufficient for that mode.
- **`docs/specs/project-essentials.md` for this project** dogfooded with a new `### Approval gate discipline` subsection that summarizes the rule and explains the root cause (the mixed lanes in `code_velocity`'s Velocity Practices). This is deliberately circular: the fix ships by itself as an instruction in `_header-common.md`, AND this project's project-essentials captures the same rule, which the M.a render hook then injects as a second reinforcement when any mode is rendered against this repo.

### Tests
- **Parametrized `test_header_common_approval_gate_rule_renders_in_every_mode`** — the critical test. Runs across every mode returned by `_get_all_mode_names()` (currently 14 modes). For each, runs `init + mode <name>` in a fresh `CliRunner.isolated_filesystem()` and asserts the rendered `go.md` contains the pinned substring `"do not prompt for git operations"` *inside* the **Rules** block (positional assertion, not just a presence check). This proves the rule reaches every mode, not just the ones explicitly touched by this story.
- **`test_code_velocity_mode_separates_llm_lane_from_developer_lane`** — end-to-end render of `code_velocity`. Asserts both lane headers are present; the developer-lane header contains the "do NOT prompt for, offer, or initiate" load-bearing language; `"Direct commits to main"` appears *after* the developer-lane header (positional check, not just presence); and the LLM-lane header comes before the developer-lane header.
- **`test_code_velocity_present_step_forbids_followup_prompts`** — asserts step 9's tightened language is present with two pinned substrings (`"Do not propose commits"` and `'want me to also'`).
- **`test_code_test_first_present_step_forbids_followup_prompts`** — same assertion for `code_test_first`'s step 8. Ensures the Present-step tightening propagates to both code modes.
- All four new tests pass; full suite **266 passed** (was 248; +18 = 14 parametrized + 3 code-mode + 1 from the count arithmetic). Ruff clean. No production code changed — this is a template-instruction fix only, so no mypy delta to report.

### Notes
- **Audit result**: manually grepped every bundled mode template for the "LLM/developer lane mixing" pattern. One orphan was discovered: **`production-mode.md`** (a transition checklist template that is NOT wired to any mode in `.metadata.yml` — dead code that never renders to any `go.md`). Its "Production Mode Transition Checklist" bullets mix LLM-lane and developer-lane items in an unlabeled list, but because the template is not included in any rendered guide, it cannot trigger the bug. Scope-gated to "defer" per the M.g story's out-of-scope clause — a separate follow-up story should either wire `production-mode.md` into `.metadata.yml` with the two-lane restructure or delete it as confirmed dead code. Flagged here for provenance.
- **`document-brand-mode.md:385`** uses the good pattern already (`**Manual Updates (developer must do):**`). No fix needed; confirmed during the audit as the reference for how to label developer-lane sections.
- **`document-landing-mode.md:56`** uses a `**Note:**` callout for a developer-side action. Also confirmed acceptable during the audit.
- **Known limitation**: this fix addresses the *instruction*-level cause of the overreach. It does not prevent an LLM from ignoring the rule anyway — nothing short of a tool-side hook can do that. The rule is a strong nudge, not a hard gate. An LLM that has been conditioned elsewhere to offer commits can still override the rule; the fix substantially raises the cost of doing so (by putting the rule in front of the LLM on every read, in every mode) but does not make it impossible.
- **Phase M is now complete for real this time** (`v2.3.0`–`v2.3.6`). Seven stories shipped: M.a through M.f as previously enumerated, plus M.g (this story) which closes a bug the first six stories introduced by implication. The lifecycle wiring, the render hook, the validator, and now the approval-gate discipline are all in place.

## [2.3.5] - 2026-04-11

### Added
- **Phase M documentation pass** (Story M.f) — the `project-essentials.md` artifact that landed in v2.3.0 and the three planning-mode wirings that landed in v2.3.2 / v2.3.3 / v2.3.4 are now reflected across all user-facing documentation and cross-referenced from the other artifact templates:
  - **`project_guide/templates/project-guide/templates/artifacts/concept.md`** — the existing "see also" sentence in the header gains a fourth cross-reference to `project-essentials.md` with a one-line description of what belongs there ("workflow rules, hidden coupling, tool-wrapper conventions that the LLM would otherwise random-walk on").
  - **`project_guide/templates/project-guide/templates/artifacts/features.md`** — same cross-reference added to the "see also" sentence.
  - **`project_guide/templates/project-guide/templates/artifacts/tech-spec.md`** — same cross-reference, with an additional one-line note that `plan_tech_spec` populates it after the tech-spec is approved (so the developer knows the capture flow is automatic, not manual).
  - **`project_guide/templates/project-guide/templates/artifacts/stories.md`** — same cross-reference, with a one-line note that `plan_phase` appends to it per phase.
  - **`project_guide/templates/project-guide/templates/modes/default-mode.md`** — the "Planning (sequence)" table's `plan_tech_spec` and `plan_phase` rows now mention the `project-essentials.md` side-effect. A new **"Refactoring (cycle)"** section was added to the "All Available Modes" table (previously missing entirely — Refactoring modes were listed in the README but not in the bundled default-mode template). The new `refactor_plan` row explicitly mentions the terminal-step project-essentials refresh.
  - **`README.md` — `### Planning Modes` table** — same `plan_tech_spec` and `plan_phase` updates as above.
  - **`README.md` — `### Refactoring Modes` table** — `refactor_plan` row rewritten from the vague "Plan a refactor" to the specific "Update `concept`/`features`/`tech-spec` for new capabilities or legacy migration; terminal step refreshes `project-essentials.md` (creates it for legacy projects)".
  - **`docs/site/user-guide/modes.md`** — full reference entries rewritten for `plan_tech_spec`, `plan_phase`, and `refactor_plan`:
    - `plan_tech_spec` now lists two **Artifacts** (was one) and explains the post-approval capture flow with the "skip if none" escape hatch called out.
    - `plan_phase` now lists three **Artifacts** (was two) and explains the terminal append step with the append-only-semantics rationale (`refactor_plan`'s Final Step is where you refactor essentials, not here).
    - `refactor_plan` now lists a **Artifact** field (was none) and explains the terminal "Revisit Project Essentials" step with all five refactor-specific framing categories visible in the prose. Legacy projects are explicitly flagged as the highest-value capture moment.

### Notes
- **Phase M is now complete** (`v2.3.0`–`v2.3.5`). Six stories shipped: M.a render hook + artifact template + dogfooding, M.b post-render placeholder validator, M.c `plan_tech_spec` create-wiring, M.d `refactor_plan` modify-wiring (terminal step), M.e `plan_phase` modify-wiring (append-only), and M.f (this documentation pass). The M.a render hook reads `<spec_artifacts_path>/project-essentials.md` at render time and injects its content under a `## Project Essentials` section in every rendered `go.md` via the `{% if project_essentials %}` guard in `_header-common.md`. The three planning modes populate, refresh, and append to the file at their respective lifecycle touchpoints. The M.b validator catches any future template edit that breaks the render pipeline (including removing the guard, typo-ing a context variable, or forgetting to update `render.py` when adding a new template variable).
- **Documentation-only release.** No code or test changes. All 248 tests continue to pass unchanged (`pyve test`). Ruff clean across `project_guide/` and `tests/`. mypy clean on all unchanged production modules.
- **Cross-reference scope**: only the four artifact templates that form the standard planning-doc chain (`concept.md`, `features.md`, `tech-spec.md`, `stories.md`) get the new cross-reference to `project-essentials.md`. `brand-descriptions.md` is a documentation artifact, not a planning doc, and was deliberately not touched — keeping that artifact's header focused on brand-specific cross-references.
- **Implicit verification via the M.c / M.d / M.e end-to-end tests**: the story's "verify by running each of the three updated planning modes against a fresh fixture" checklist item is covered by the existing `test_plan_tech_spec_mode_prompts_for_project_essentials`, `test_refactor_plan_mode_prompts_for_project_essentials_revisit`, and `test_plan_phase_mode_prompts_for_project_essentials_append` tests in `tests/test_render.py`. Each runs `init` + `mode <name>` against a fresh `CliRunner.isolated_filesystem()` and asserts the prompt content. Re-running these three tests as part of the full suite (248 passed) is the verification — no separate fixture test added.
- **What this phase leaves on the table for a future phase**: none. Phases K / L / M are all complete and ready for the next `archive_stories` run. When that happens, `stories.md` will be archived to `.archive/stories-v2.3.5.md` and a fresh empty `stories.md` will be re-rendered for the next phase.

## [2.3.4] - 2026-04-11

### Added
- **`plan_phase` mode appends to `project-essentials.md`** (Story M.e) — wires the third and final planning mode to the M.a render hook, completing the M.c/M.d/M.e lifecycle coverage. Where M.c populates on initial tech-spec creation and M.d revisits on refactor, M.e runs once per new phase plan and **appends** (rather than revisits or rewrites) new must-know facts to the file. The append-only semantics are a deliberate design constraint — `plan_phase` runs frequently over a project's lifetime and should not be the place to refactor or reorder existing project-essentials content; that's `refactor_plan`'s Final Step job.
- **New step 7 in `plan-phase-mode.md`** appended after Step 6 (stories approval), runs **once** at the end of phase planning (not per-story). Structure:
  - **Create-if-absent branch**: if `docs/specs/project-essentials.md` doesn't exist (legacy project), the mode creates it from the artifact template first, following the same create path as `refactor_plan`'s Final Step. Legacy projects are explicitly flagged as the highest-value case.
  - **Modify branch**: if the file exists, the mode reads it, keeps the current content in mind for the phase-specific prompt, and appends new `###` subsections under appropriate categories.
  - **Phase-specific worked examples** with framing appropriate to "adding capability to an existing codebase": new architecture boundary (example cites Phase K's action-type registration pattern); new workflow rule or CLI contract (example cites Phase L's `--no-input` error-message contract that downstream tools pin); new hidden coupling between files (example cites Phase M's own `_header-common.md` guard + M.b validator); new deferred-but-documented item.
  - **Principle anchor**: "if the phase introduced a new *invariant* or *convention* that someone working in this codebase a year from now would waste an hour rediscovering, it belongs in project-essentials." Straightforward feature additions with no new invariants should skip this step.
  - **Skip-if-none escape hatch** is explicit — not every phase introduces new must-know facts.
  - **Append-only semantics** are explicit: "append (do not rewrite or reorder)". Add new `###` subsections under the appropriate category (or create a new category if none fits). Do not edit existing content.
  - **Heading convention reminder** (no top-level `#`; `###` for subsections) is present so the append nests correctly under the wrapper's `## Project Essentials`.
- **`plan_phase` metadata entry** now declares three `artifacts` (was two): `new-phase-{{phase_name}}.md` (no action — document artifact), `stories.md` (`action: modify`), and the new `project-essentials.md` (`action: modify`). The new wiring does not disturb the existing two declarations — the M.e story's test explicitly guards against that regression.

### Changed
- **`{% raw %}...{% endraw %}` escape on the "hidden coupling" worked example** in `plan-phase-mode.md`. The example references `_header-common.md`'s `{% if project_essentials %}` guard literally inside a backtick code span — without the `{% raw %}` escape, Jinja2 parses the literal as an actual tag and the render fails with `Unexpected end of template`. This is the first time any bundled template has needed `{% raw %}` escaping, and it's a useful datapoint for the M.b validator's known-limitation note (templates that want to emit literal `{{ var }}` or `{% ... %}` strings need `{% raw %}`). Discovered during the first M.e test run; documented inline in the template.

### Tests
- **2 new tests in `tests/test_render.py`** under the "Story M.e" heading:
  - `test_plan_phase_mode_prompts_for_project_essentials_append` — end-to-end render. Asserts: append step present and runs once; append-only semantics explicit ("do not rewrite or reorder"); create-if-absent branch present with legacy-project framing; at least two phase-specific worked example categories (architecture boundary, workflow rule / CLI contract); skip-if-none escape hatch; artifact template reference; heading convention reminder.
  - `test_plan_phase_metadata_declares_project_essentials_modify_artifact` — loads bundled metadata, asserts exactly one `project-essentials.md` artifact with `ActionType.MODIFY`. Also sanity-checks that the existing `new-phase-*.md` and `stories.md` declarations are still present, guarding against a clobber regression.
- **`test_every_mode_renders_successfully` parametrized test continues to pass unchanged** — and was specifically what caught the missing `{% raw %}` escape on the first run, since the `plan_phase` mode render failed until the escape was added.

### Notes
- **Phase M wiring is now complete** (M.c/M.d/M.e). All three planning modes populate, refresh, or append to `project-essentials.md` at their respective lifecycle touchpoints:
  - `plan_tech_spec` → `action: create` (initial population after tech-spec approval)
  - `refactor_plan` → `action: modify` (terminal revisit, create-if-legacy, refresh-if-exists)
  - `plan_phase` → `action: modify` (append-only, create-if-legacy)
  - All three use concrete worked examples with lifecycle-specific framing (initial / refactor-driven / phase-driven). All three have end-to-end render tests and metadata wiring tests. All three follow the heading convention that lets the content nest under `_header-common.md`'s `## Project Essentials` wrapper.
- **What M.f (next and final Phase M story) adds**: a documentation pass — README / modes catalogue / CHANGELOG consolidation. No code changes; just closes out Phase M.
- Full test suite: **248 passed** (+2 new M.e tests). Ruff clean across `project_guide/` and `tests/`. mypy clean on the unchanged production modules (no code changes in this story).
- Verified end-to-end by running `pyve run project-guide update && pyve run project-guide mode plan_phase` in this repo. The rendered `go.md` contains the new step 7 at the expected position (after the stories-approval step 6) AND the M.a-injected `## Project Essentials` section at the top. The `{% if project_essentials %}` literal inside the worked example renders correctly (line 162 of the rendered output), confirming the `{% raw %}` escape works.

## [2.3.3] - 2026-04-11

### Added
- **`refactor_plan` mode refreshes `project-essentials.md`** (Story M.d) — wires the second of the three planning modes to the M.a render hook. When a refactor updates concept/features/tech-spec, the mode now runs a terminal "Revisit Project Essentials" sequence to capture any new must-know facts the refactor introduced. Distinct from M.c's `plan_tech_spec` (initial-lifecycle path) and M.e's upcoming `plan_phase` (per-phase append) in two ways: (1) it runs **once** per refactor session, not per-document, and (2) it handles both the **create** case (legacy project being migrated to v2.x, no file exists yet) and the **modify** case (project already has the file).
- **New "Final Step: Revisit Project Essentials" section** in `refactor-plan-mode.md`, appended after Step 8 (Cleanup). Structured as a 4-step sub-sequence to keep the decision path explicit:
  - **Step F.1: Check for Existing File** — branches on whether `docs/specs/project-essentials.md` exists. The legacy-project branch is explicitly flagged as the highest-value case, because these projects typically have *never had their conventions written down* — their developers have internalized the rules and forgotten they're non-obvious.
  - **Step F.2: Ask the Refactor-Revisit Prompt** — five concrete worked examples with *refactor-specific* framing (not M.c's initial-lifecycle framing): switched or added an environment manager (`pyve`/`uv`/`poetry`/`hatch`); split runtime from dev environment with the `pip install -e '.[dev]'` anti-pattern explicitly called out; renamed module or moved source-of-truth; changed domain conventions (money float → cents); new auto-generated or hidden-coupling files. Anchored by the **fork-in-the-road principle**: if the refactor introduced a decision where the *wrong* choice still "works" (runs, compiles, passes some tests), that is a project-essential. Each worked example includes a fully-rendered "*Example:*" sentence so the LLM can put concrete language in front of the developer, not abstract category names.
  - **Step F.3: Generate or Update the File** — explicit create vs modify branching. Legacy projects get a fresh file from the artifact template; existing projects get an in-place update that preserves-updates-adds. Both paths re-iterate the heading convention (no top-level `#`; `###` for subsections).
  - **Step F.4: Approval** — show the developer what was added, modified, and preserved, so the diff is legible.
- **"Skip if there are none" escape hatch** is part of Step F.2, explicitly framed for the pure-doc-restructure case where no tool/architecture/convention change occurred. A pure reformat is a legitimate refactor and should not be forced to produce project-essentials content.
- **`refactor_plan` metadata entry** now declares a single `artifacts` list (was previously empty) containing `project-essentials.md` with `action: modify`. The `modify` action type is the *conversational escape hatch* for the create-if-absent case: the deterministic action doesn't fire if the file doesn't exist, so the LLM's Step F.1 branching is what handles the create path in prose. The `action: modify` declaration is still correct at the metadata level because the *intent* is to end up with a modified (or newly-created) file.

### Tests
- **2 new tests in `tests/test_render.py`** under the "Story M.d" heading:
  - `test_refactor_plan_mode_prompts_for_project_essentials_revisit` — end-to-end render test. Fresh `init` → `mode refactor_plan` → read `go.md`. Asserts the terminal section is present and runs once (not per-document); the create/modify branches are both visible; the legacy-project framing is explicit; at least one concrete worked example with environment-manager naming is present; the artifact template path is referenced; the heading convention reminder is emitted; the "skip if none" escape hatch is present; and the fork-in-the-road / "wrong choice still works" principle is visible (refactor-framing anchor).
  - `test_refactor_plan_metadata_declares_project_essentials_modify_artifact` — loads the bundled metadata, gets the `refactor_plan` mode, and asserts exactly one `project-essentials.md` artifact with `ActionType.MODIFY`. The "exactly one" check is deliberate — a duplicate declaration from a copy-paste mistake would be silently accepted by the schema but would break the conversational handoff.
- **`test_every_mode_renders_successfully` parametrized test continues to pass unchanged** — the new terminal section introduces no undefined-variable placeholders (validated by the M.b post-render validator) and the new metadata wiring does not break rendering for any of the 14 modes.

### Notes
- **Design choice — terminal step vs cycle step**: the M.d story offered two options ("add a cycle step OR extend Step 1"). I chose a terminal step (new "Final Step: Revisit Project Essentials" section appended after Step 8). Rationale: `refactor_plan`'s main cycle processes three documents (concept, features, tech-spec) one at a time — asking about project-essentials once per document would be annoying and redundant, because most of the meaningful facts a refactor introduces are cross-document (a new tool wrapper affects how you run everything, not just how you build one artifact). Running the prompt once at the end gives the developer the full refactor context and produces a cleaner essentials file.
- **Terminology for metadata `action: modify`**: refactor_plan runs `action: modify` even though the file may not exist (legacy projects). This is the design pattern already established by `plan_phase`'s `stories.md` artifact in the bundled metadata — `modify` declares the intent ("end up with a modified file") and the mode template handles the create-if-absent case conversationally. The deterministic action handler in `actions.py` does NOT fire for `modify` actions — those go through the LLM. Only `archive` actions fire deterministically (via the `archive-stories` CLI command). So `modify` on a nonexistent file is not a runtime error; it's an instruction to the LLM.
- Full test suite: **246 passed** (+2 new M.d tests). Ruff clean across `project_guide/` and `tests/`. mypy clean on `project_guide/render.py`.
- Verified end-to-end by running `pyve run project-guide update && pyve run project-guide mode refactor_plan` in this repo. The rendered `go.md` contains all four sub-steps (F.1 through F.4) in the expected terminal position AND the M.a-injected `## Project Essentials` section at the top — proving the two layers compose correctly for this cycle-type mode as well.
- **M.e (next story)** will take the same pattern into `plan_phase` with an *append-only* variant: rather than revisit or refresh, the prompt asks what *new* facts the phase introduces and appends them. Also uses `action: modify`. After M.e ships, all three planning modes (M.c/M.d/M.e) will populate `project-essentials.md` at their respective lifecycle touchpoints.

## [2.3.2] - 2026-04-11

### Added
- **`plan_tech_spec` mode populates `project-essentials.md`** (Story M.c) — wires the first of the three planning modes to the M.a render hook. After the developer approves the tech-spec, the mode now asks whether any must-know facts should be captured for future LLMs working on the project, with concrete worked examples in the prompt (not just abstract category names). If the developer provides facts, the mode generates `docs/specs/project-essentials.md` from the artifact template; if not, the file is not created (an empty file is deliberately avoided on fresh projects — the "skip if none" escape hatch is explicit).
- **New step 5 in `plan_tech_spec` mode template** at `project_guide/templates/project-guide/templates/modes/plan-tech-spec-mode.md`: "After tech-spec approval, capture project essentials." The prompt lists five categories (workflow rules, architecture quirks, domain conventions, hidden coupling, dogfooding/meta notes) and provides concrete worked examples for each — in particular, the *tool wrapper random walk* anti-pattern (Python invocation, dev tool installation, test invocation) that the story's implementation strategy explicitly calls out as the highest-value category to capture.
- **New step 6 in the same mode**: generate `project-essentials.md` from the artifact template when the developer provides facts. The step explicitly reminds the LLM to follow the template's heading convention (no top-level `#`; `###` for subsections) so the content nests correctly under the `## Project Essentials` wrapper injected by `_header-common.md`.
- **`plan_tech_spec` metadata entry** now declares two `artifacts` (was one): `tech-spec.md` + `project-essentials.md`, both with `action: create`. The `create` action type is correct here because `plan_tech_spec` is the initial-lifecycle population path; `refactor_plan` (M.d) and `plan_phase` (M.e) will use `modify`/`modify` since those run against existing projects where the file may already exist.

### Tests
- **2 new tests in `tests/test_render.py`** under the "Story M.c" heading:
  - `test_plan_tech_spec_mode_prompts_for_project_essentials` — end-to-end render test. Fresh `init` → `mode plan_tech_spec` → read `go.md`. Asserts the capture step is present and ordered after tech-spec approval, at least one concrete worked example (`pyve run python` or `poetry run python`) is visible, two category names (`Workflow rules`, `Architecture quirks`) appear, the "skip if none" escape hatch is present, the artifact template path is referenced, and the heading convention reminder ("do NOT include a top-level", `###`) is emitted.
  - `test_plan_tech_spec_metadata_declares_project_essentials_artifact` — loads the bundled `.metadata.yml`, gets the `plan_tech_spec` mode, and asserts both `tech-spec.md` and `project-essentials.md` are declared as artifacts with the `project-essentials.md` artifact using `ActionType.CREATE`. This is the wiring checkpoint that M.d/M.e will deliberately diverge from.
- **`test_every_mode_renders_successfully` parametrized test continues to pass unchanged** — the new prompt content and the new metadata entry do not introduce any undefined-variable placeholders (validated by the M.b post-render validator) and do not break rendering for any of the 14 modes.

### Notes
- The `create` action type on the new artifact is an **intent declaration**, not an unconditional file-creation. The mode template's step 5 "skip to step 7 if there are no facts to capture" clause is the LLM-runtime escape hatch — a fresh project where the developer has nothing to put in `project-essentials.md` does NOT get an empty file. This is a deliberate design choice: empty files would trigger the render hook's "whitespace-only = omit section" branch (which is correct) but would leave a dormant empty file in `docs/specs/` that looks like an oversight. Better to not create it at all.
- Full test suite: **244 passed** (+2 new M.c tests). Ruff clean across `project_guide/` and `tests/`. mypy clean on `project_guide/render.py`.
- Verified end-to-end by running `pyve run project-guide update && pyve run project-guide mode plan_tech_spec` in this repo. The rendered `go.md` contains both the M.a-injected Project Essentials section at the top (fed by this project's own `docs/specs/project-essentials.md`) and the new M.c capture step at step 5 — proving the two layers compose correctly on a project that already has the file populated.
- **What M.d and M.e add next**: M.d (`refactor_plan`) adds the same prompt with a "refactor-driven changes" framing and handles the legacy-project case where `project-essentials.md` does not yet exist; declares `action: modify` so the mode can either create-if-absent or modify-if-present. M.e (`plan_phase`) adds an append-only variant that runs once per new phase plan; also declares `action: modify`. M.c/M.d/M.e are mutually independent (per the phase plan in `docs/specs/stories.md`) but the listed order matches the project lifecycle.

## [2.3.1] - 2026-04-11

### Added
- **Post-render placeholder validator** (Story M.b) — generalizes the M.a `{{ project_essentials }}` regression guard into a project-wide safeguard. After every `render_go_project_guide` call, the rendered output is scanned for any bare `{{ identifier }}` Jinja-style placeholder; if any are found, `RenderError` is raised with the offending names and a fix hint, and the output file is **not** written. This catches three distinct failure modes at the same place:
  1. **Missed intents** — a context variable that should have been set in `render.py` but wasn't.
  2. **Typos** — a template referencing `{{ project_essentialss }}` or any other misspelled variable name.
  3. **Removed guards** — a future edit that drops a `{% if %}` wrapper and lets an unset variable leak through.
- **`_UNRENDERED_PLACEHOLDER_RE` module-level regex** (`render.py`): `\{\{\s*([a-zA-Z_]\w*)\s*\}\}`. Matches exactly the shape that `_LenientUndefined.__str__` emits — `{{var}}`, `{{ var }}`, `{{  var  }}`. Deliberately does **not** match attribute access (`{{ obj.attr }}`), filters (`{{ name|upper }}`), expressions (`{{ a + 1 }}`), or statement blocks (`{% ... %}`). Those shapes raise at Jinja render time and never reach the validator.
- **`_validate_no_unrendered_placeholders(rendered)` helper** (`render.py`): scans the rendered output, deduplicates offenders while preserving first-occurrence order, and raises `RenderError` with a message of the form `Unrendered placeholder(s) in rendered output: <names>. Hint: check (1) render.py context variables and (2) template variable spellings.`. The validator is called inside `render_go_project_guide` **after** `template.render()` and **before** `output_path.write_text()`, so a failing render leaves the filesystem untouched.

### Changed
- **`_LenientUndefined` contract documented inversion**: the class itself is unchanged (still emits `{{ name }}` for undefined variables), but its *purpose* has inverted. Before M.b, the placeholder shape was the final output — a permissive pass-through so unset variables wouldn't crash renders. After M.b, the placeholder shape is the *detection signal* — lenient undefined produces the shape that the post-render validator catches and promotes to an error. The class stays lenient so the validator can see and report every offender in one pass, rather than Jinja crashing on the first undefined variable it encounters.
- **`test_render_undefined_vars_are_preserved` renamed to `test_render_undefined_vars_raise_render_error`** and inverted to assert the new behavior: undefined variables now raise `RenderError` with the offending name, and no output file is written.

### Removed
- **Temporary M.a regression guard `test_project_essentials_never_renders_literal_placeholder`** — the general validator subsumes it. If the `{% if %}` guard on `_header-common.md` is ever removed, the M.b validator raises `RenderError` on every mode render that has no populated `project-essentials.md`, which is far louder than a single dedicated test. A comment in the test file marks the removal for future readers.

### Tests
- **7 new tests in `tests/test_render.py`** under the "Story M.b" heading:
  - `test_validator_raises_on_single_undefined_variable` — baseline: one typo'd variable → `RenderError` citing the name.
  - `test_validator_error_message_lists_all_offenders` — three distinct offenders → error message names all three (no first-match short-circuit).
  - `test_validator_deduplicates_repeated_offenders` — a name repeated 3× → appears exactly once in the message, in first-occurrence order.
  - `test_validator_error_message_includes_fix_hint` — message contains both "render.py context variables" and "template variable spellings".
  - `test_validator_does_not_write_output_on_failure` — the output file must not exist after a raise (pre/post `exists()` assertions).
  - `test_validator_passes_when_all_vars_defined` — happy path: the standard `template_dir` fixture renders cleanly and the rendered file contains zero matching placeholders.
  - `test_validator_passes_on_template_with_no_jinja_variables` — empty-match edge case: a minimal plain-text template renders without raising.
- **Existing `test_every_mode_renders_successfully` parametrized test continues to pass unchanged.** This is the critical cross-template audit: every bundled mode is rendered through a fresh `CliRunner.isolated_filesystem()` install and must now pass the validator. All 14 modes pass, confirming that no bundled template references an undefined variable. This replaces the manual "audit existing templates" step in the M.b story checklist with an empirical proof.

### Notes
- **Audit result**: every bundled mode template's bare `{{ var }}` is backed by either a `render.py` context variable (`mode_name`, `mode_info`, `mode_description`, `sequence_or_cycle`, `next_mode`, `target_dir`, `project_essentials`) or a `metadata.common` entry (`test_invocation`, `spec_artifacts_path`, `web_root`). No mode template `{% include %}`s an artifact template, so artifact-template placeholders like `{{problem_statement}}` never enter the mode render path — they go through a separate `perform_archive` path in `actions.py` with its own `_LenientUndefined`, which is unchanged by this story.
- **Known limitation** (documented inline in `_UNRENDERED_PLACEHOLDER_RE`'s docstring): templates that legitimately want to emit a literal `{{ var }}` string (e.g., documentation of Jinja syntax inside a code fence) will trigger false positives. Not currently a problem in any bundled template; bridge if/when needed, likely via a `{% raw %}` escape.
- Full test suite: **242 passed** (+7 new M.b tests, −1 removed M.a guard, 1 renamed). Ruff clean across `project_guide/` and `tests/`. mypy clean on `project_guide/render.py`.
- Verified end-to-end by re-rendering `docs/project-guide/go.md` under `default` and `plan_concept` modes per the story checklist. Both produce zero unrendered placeholders (confirmed via grep of the output).

## [2.3.0] - 2026-04-11

### Added
- **`project-essentials.md` artifact and render hook** (Story M.a) — a new per-project artifact that captures must-know facts future LLMs need to avoid blunders (workflow rules, architecture quirks, domain conventions, hidden coupling, dogfooding notes). When present and non-empty, its content is injected verbatim under a `## Project Essentials` section in **every** rendered mode via `_header-common.md`, making the facts visible no matter which mode the developer is in. This story lays the rails; the `plan_tech_spec` / `refactor_plan` / `plan_phase` modes will be wired to populate it in stories M.c–M.e.
- **`project_guide/templates/project-guide/templates/artifacts/project-essentials.md`** — the new artifact template. Ships as a comment-block-only file documenting what belongs there (workflow rules with concrete examples, architecture quirks, domain conventions, hidden coupling, dogfooding notes) and explicitly noting that an empty file is acceptable. The template deliberately omits a top-level `#` heading — the wrapper in `_header-common.md` provides the `## Project Essentials` heading, and content uses `###` for subsections to nest cleanly.
- **`_read_project_essentials()` helper in `project_guide/render.py`** — reads `<spec_artifacts_path>/project-essentials.md` (resolved from `metadata.common["spec_artifacts_path"]`, typically `docs/specs`). Returns an empty string when the path is missing, the file does not exist, or the file is whitespace-only. `render_go_project_guide` now calls this helper and passes the result as the `project_essentials` Jinja2 context variable.
- **`{% if project_essentials %}` guard in `_header-common.md`** — renders the `## Project Essentials` section (with the file's content and a `---` separator) only when the variable is non-empty. Empty/missing files omit the section entirely, so projects that don't want to maintain this file render cleanly.
- **`docs/specs/project-essentials.md` for this project** (dogfooding) — populated with the current must-know facts: pyve two-environment workflow rules (`pyve run` / `pyve test` / `pyve testenv run`), the dogfooding rule (edit templates in `project_guide/templates/project-guide/`, never `docs/project-guide/`), v2 mode-driven architecture, the Phase K release-lifecycle pattern, the Phase L `--no-input` contract, and the commit/version style conventions.

### Tests
- **6 new tests in `tests/test_render.py`** under the "Story M.a" heading, all using a new `essentials_template_dir` fixture that faithfully reproduces the `{% if %}` guard shape and a new `essentials_metadata` fixture with `spec_artifacts_path`:
  - `test_project_essentials_rendered_when_file_non_empty` — populated file → section appears between the header and the mode body.
  - `test_project_essentials_omitted_when_file_empty` — zero-length file → section omitted.
  - `test_project_essentials_omitted_when_file_whitespace_only` — whitespace-only file → section omitted (treated as empty).
  - `test_project_essentials_omitted_when_file_missing` — no file at all → section omitted, no error.
  - `test_project_essentials_omitted_when_spec_artifacts_path_not_in_metadata` — minimal metadata without `spec_artifacts_path` → lookup is skipped, section omitted.
  - `test_project_essentials_never_renders_literal_placeholder` — **temporary regression guard** (scheduled for removal by M.b once the general post-render placeholder validator lands). Exercises all four file shapes and asserts the literal string `{{ project_essentials }}` never appears in the output. Catches a future template edit that removes the `{% if %}` guard, since `_LenientUndefined.__str__` would otherwise render the placeholder verbatim. See `render.py:83-99` for the lenient-undefined contract.

### Notes
- The M.a story deliberately does **not** add `project-essentials.md` to any mode's `.metadata.yml` `artifacts` list — that wiring is M.c–M.e's responsibility (population via `plan_tech_spec`, refresh via `refactor_plan`, append via `plan_phase`). M.a only establishes the render-time lookup, the guarded section, and the dogfooded content for this project.
- The existing `test_every_mode_renders_successfully` parametrized test continues to pass unchanged. It runs every bundled mode through an isolated filesystem where no `docs/specs/project-essentials.md` exists, so the section is omitted and the render produces valid output — this is the implicit cross-mode regression guard.
- Full test suite: **236 passed** (`pyve test`). Ruff clean across `project_guide/` and `tests/`. mypy clean on `project_guide/render.py`.
- Verified end-to-end by re-rendering `docs/project-guide/go.md` under both `default` and `code_velocity` modes; the `## Project Essentials` section appears between the `**Rules**` block and the mode heading, with the `###` subsection nesting rendering correctly.

## [2.2.3] - 2026-04-11

### Fixed
- **MkDocs commands reference catch-up for `archive-stories`** (Story L.d) — closes a K.g documentation carryover gap discovered during the L.c documentation pass. The `archive-stories` CLI command shipped in v2.1.3 (Story K.d), and the K.g docs pass (v2.1.6) updated the README's Command Reference, `modes.md`, `workflow.md`, and `default-mode.md` — but `docs/site/user-guide/commands.md` was not on the K.g checklist, so the MkDocs command reference still reflected the pre-v2.1.3 command surface. Rather than retroactively patch the closed Phase K, this fix rolls forward as Phase L's final story.
  - `docs/site/user-guide/commands.md` line 3: "eight commands" → "nine commands".
  - Command Overview table: new `archive-stories` row, inserted between `mode` and `status` to match the README's Command Reference ordering (post-release/lifecycle commands group with `mode` rather than with the file-sync commands).
  - New `## archive-stories` section placed after `## mode` and before `## status`. Content adapted from the canonical `README.md` `### archive-stories` section (which has the authoritative prose from K.g): synopsis, 5-step "What It Does" pipeline, "Failure Modes" (pre-check failure leaves workspace untouched; rollback on re-render failure), and "Usage" note explaining the conversational-vs-deterministic split between the `archive_stories` mode template and the CLI command.
- Verified: every command listed by `project-guide --help` (9 total: `archive-stories`, `init`, `mode`, `override`, `overrides`, `purge`, `status`, `unoverride`, `update`) now has both a row in the `commands.md` overview table and a dedicated `##` section. No other commands drift detected during the audit.

### Notes
- Documentation-only release. No code or test changes. All 230 tests continue to pass unchanged.
- Phase L (`v2.2.0`–`v2.2.3`) is now complete. The pyve post-hook integration path is fully unblocked, documented in both the README and MkDocs command references, and the MkDocs command surface now matches the CLI.
- **Provenance note for future docs-audit work:** this fix catches one specific K.g gap (the missing `archive-stories` content). It is deliberately *not* a general `commands.md` audit — any other drift in that file (stale counts, outdated output samples, etc.) was out of scope and should be tracked separately if discovered. The story's out-of-scope section in `docs/specs/stories.md` documents this boundary.

## [2.2.2] - 2026-04-11

### Added
- **Phase L documentation pass** (Story L.c) — the unattended-use surface shipped in v2.2.0 (idempotent re-run) and v2.2.1 (`--no-input` flag + auto-detection) is now reflected across all user-facing documentation:
  - `README.md` — `### init` gets an "Unattended / CI use" subsection listing all four trigger mechanisms (`--no-input`, `PROJECT_GUIDE_NO_INPUT`, `CI`, non-TTY stdin) with one example each, plus an "Idempotent re-run" paragraph calling out the exit-0 no-op behavior. The `--no-input` flag is documented in the `init` options list.
  - `docs/site/user-guide/commands.md` — `## init` gets a new "Idempotent Re-run" section and a full "Unattended / CI Use" section with a priority-order trigger table. The `--no-input` flag is documented in the options list and Examples block. The new sections also cite the `should_skip_input()` helper and `_require_setting()` contract in `project_guide/runtime.py` so anyone adding a future prompt knows where the plumbing lives.
  - `docs/specs/project-guide-no-input-spec.md` — status line updated from `Proposed (2026-04-10)` to `Implemented in v2.2.0–v2.2.1 (2026-04-11)` with one sentence each citing Story L.a (idempotent re-run) and Story L.b (`--no-input` + auto-detection + `_require_setting`).

### Notes
- This is a documentation-only release: no code or test changes. All 230 tests continue to pass unchanged. Phase L (`v2.2.0`–`v2.2.2`) is now complete; the pyve post-hook integration path is fully unblocked and documented.
- Known gap (out of scope for this release, not introduced by this phase): `docs/site/user-guide/commands.md` still says "eight commands" in its overview and does not document the `archive-stories` command added in v2.1.3. This is a K.g carryover — the K.g docs pass updated the README but not the MkDocs commands reference. Tracked for a follow-up pass.

## [2.2.1] - 2026-04-11

### Added
- **`--no-input` flag on `project-guide init`** (Story L.b) with env-var and non-TTY auto-detection. `init` is now safe to invoke from any unattended context (CI runners, `pyve` post-hooks, subprocess pipelines) without hanging on a future prompt.
- **`project_guide/runtime.py`** — new module exposing `should_skip_input(flag: bool = False) -> bool`. This is the single idiom every future prompt site in this package must use to decide whether it is safe to read from stdin. Trigger priority (first match wins):
  1. Explicit `flag` argument (usually `--no-input`).
  2. `PROJECT_GUIDE_NO_INPUT` env var set to a truthy value.
  3. `CI` env var set to a truthy value.
  4. Non-TTY stdin (piped input, subprocess, closed stdin, `sys.stdin is None`).
  5. Otherwise: interactive.
  - Truthy env values are matched case-insensitively against `{"1", "true", "yes", "on"}`.
  - Subprocess safety: `AttributeError` (when `sys.stdin` is `None`) and `ValueError` (when stdin is closed) are caught and treated as non-TTY.
- **`_require_setting(name, cli_flag, env_var)` helper** in `runtime.py` — raises `click.ClickException` (exit code 1) with the exact message format `<name> is required when --no-input is active. Provide via --<cli_flag> or <env_var>.`. This is the landing spot for any future prompt site that has no sensible default under `--no-input`. No production prompt exercises this today; it exists so the contract is frozen *before* the first caller.
- **`init --no-input` click option** — boolean, default `False`, help text: `Do not read from stdin; use defaults where sensible. Fail loudly if any prompt has no default. (Also auto-enabled by CI=1 or non-TTY stdin.)`. The computed `skip_input = should_skip_input(no_input)` is threaded through `init` as reserved plumbing — today `init` has no interactive prompts, so the value is unused at runtime (marked `# noqa: F841` with a comment explaining why).

### Tests
- **`tests/test_runtime.py`** (new, 31 tests): baseline fixtures for a clean env + forced-TTY stdin; parametrized coverage of truthy and falsy `PROJECT_GUIDE_NO_INPUT` values; parametrized coverage of `CI` truthy values; non-TTY stdin; `sys.stdin is None` and closed-stdin subprocess edge cases; explicit priority-order tests (flag > env > CI > TTY); and `_require_setting` contract tests (exit code + exact message format).
- **`tests/test_cli.py`** (5 new tests under a Story L.b section): `test_init_with_no_input_flag_on_fresh_project`, `test_init_with_no_input_and_force_on_initialized_project`, `test_init_with_ci_env_var_is_idempotent_on_rerun` (composes L.a idempotency with L.b auto-detection), `test_init_with_non_tty_stdin_behaves_like_no_input`, and `test_require_setting_contract_exit_code_and_message` (registers a throwaway `@click.command` that calls `_require_setting` via `CliRunner` — this is the FR-L4 regression guard).

### Notes
- Full test suite: **230 passed** (`pyve test`). Ruff clean across `project_guide/` and `tests/`. mypy clean on the two modified production modules.
- The `skip_input` local in `init` is intentionally unused at present. It exists so that the day someone adds the first real prompt to `init`, the plumbing is already in place and the contract for handling missing required settings is already tested. Removing the `noqa` comment without adding a consumer would be a regression.

## [2.2.0] - 2026-04-11

### Changed
- **`project-guide init` is now idempotent** (Story L.a) — re-running `init` on an already-initialized project is a silent exit-0 no-op instead of raising `click.Abort()` / exit 1. When `.project-guide.yml` already exists and `--force` was not given, `init` now prints `project-guide already initialized at <target_dir>/ (use --force to reinitialize).` and returns. The `--force` branch is unchanged: overwrite semantics still apply. This is the small behavioral fix that unblocks the `pyve` post-hook integration path — `project-guide init` can now be invoked unconditionally from automated flows (CI, scripts, `pyve init` post-hook) without hanging on an existing project. The `--no-input` flag, env-var (`PROJECT_GUIDE_NO_INPUT`, `CI`), and non-TTY auto-detection arrive in v2.2.1 (Story L.b).

### Tests
- `tests/test_cli.py::test_init_on_already_initialized_project_is_idempotent` (renamed from `test_init_with_existing_config_error`) — verifies exit 0 and the "already initialized" message on re-run without `--force`.
- `tests/test_cli.py::test_init_double_run_does_not_modify_files` — new regression guard: a second `init` run must not rewrite any tracked template file (verified via `st_mtime_ns` snapshots of `.project-guide.yml`, `.metadata.yml`, and two mode templates).
- `test_init_with_force_flag` is unchanged and still guards the `--force` overwrite branch.

### Notes
- Idempotency is based solely on `.project-guide.yml` presence. A partial-install state where the config is absent but the target directory is populated is out of scope (falls through to the existing `_copy_template_tree` skip-with-warnings path — documented in `phase-l-no-input-init-plan.md`).
- All 194 tests pass (`pyve test`). Ruff is clean on the changed files.

## [2.1.6] - 2026-04-10

### Added
- **Phase K documentation pass** (Story K.g) — `archive_stories` mode is now reflected across all user-facing documentation:
  - `docs/site/user-guide/modes.md` — new "Post-Release Modes" section with a full `archive_stories` reference entry (Type, Next, Artifact, Prerequisites, the conversational-vs-deterministic split between the mode template and the `archive-stories` CLI command). The `plan_phase` entry now explains that it handles two `stories.md` shapes (populated and empty post-archive) and continues phase letters across the archive boundary. The Ongoing Project Flow bullet list gains an `archive_stories` entry.
  - `docs/site/user-guide/workflow.md` — new Post-Release bullet in the Modes section; new "When to Switch Modes" row for `archive_stories`; reference count updated from "15 modes" to "16 modes".
  - `project_guide/templates/project-guide/templates/modes/default-mode.md` — new "Post-Release (sequence)" table in the "All Available Modes" section with `archive_stories`.
- **README updates**:
  - New "Post-Release Modes" table in the Available Modes section.
  - New `archive-stories` CLI command reference describing the 5-step archive pipeline, pre-check failure behavior, rollback-on-failure semantics, and the LLM-runs-after-developer-approval usage pattern.
  - Quick Start mode list: added `archive_stories` (and `project_scaffold`, which had been missing from this list in earlier versions).

### Changed
- **README Key Features**:
  - "15 modes" → "16 modes".
  - "Eight intuitive commands" → "Nine intuitive commands" (new `archive-stories` command).
  - "91% test coverage with 131 comprehensive tests" → "Comprehensive test coverage across CLI, rendering, and action modules" (drops hard-coded counts that went stale every story and will continue to drift).

### Notes
- Verified via `click.testing.CliRunner`: `project-guide --help` lists `archive-stories`; `project-guide mode` (after `init`) lists `archive_stories` in the mode catalogue; `project-guide archive-stories --help` works.
- All existing tests continue to pass unchanged (193). Phase K (`v2.1.0`–`v2.1.6`) is now complete.

## [2.1.5] - 2026-04-10

### Added
- **Default mode "Suggesting the Next Step" section** (Story K.f) — `default-mode.md` now teaches the LLM to read `docs/specs/stories.md` (when present), check the status of every `### Story X.y: ... [<status>]` heading, and branch on three cases:
  - **All stories `[Done]`**: prompt the developer with both `archive_stories` (clean slate, archive then plan) and `plan_phase` (plan against history) as Option A and Option B, explaining the trade-off and including "Use this when:" guidance for each. Wait for the developer to choose before changing modes.
  - **At least one non-`[Done]`**: defer to the existing project lifecycle suggestions at the top of the mode (no behavior change).
  - **No `stories.md`**: direct the developer to `project-guide mode plan_concept` to begin the lifecycle.
- Detection happens at LLM read time (consistent with the v2 architecture — no Python-side check is added). The bundled mode template carries the prompt language for all three branches simultaneously.

### Tests
- No new tests; the existing parametrized `test_every_mode_renders_successfully` covers `default` and confirms the template still renders without errors. Manual verification via `runner.isolated_filesystem` confirms the rendered guide contains the all-Done section, both option labels, and the fresh-project hint.
- **193 tests pass** (unchanged from K.e).

## [2.1.4] - 2026-04-10

### Added
- **`plan_phase` mode handles post-archive empty `stories.md`** (Story K.e):
  - Step 1 of the mode template now distinguishes two `stories.md` shapes — "Populated" (one or more `## Phase <Letter>:` sections) vs "Empty (post-archive)" (header + `## Future` only). For the empty case, the template instructs the LLM to look in `docs/specs/.archive/` for `stories-vX.Y.Z.md` files, read the highest-version one, and use its highest phase letter as the basis for the next.
  - Step 5 explicitly describes the next-phase-letter algorithm (populated → successor of highest; empty + archive → successor of archived highest; neither → start at `A`) and tells the LLM to insert the new phase as the first phase when `stories.md` was empty.
  - Phase letters **continue across the archive boundary** — they do not reset.
- **`increment_phase_letter(letter)` helper** in `actions.py` — pure function returning the base-26-no-zero successor of a phase letter. Examples: `A→B`, `Z→AA`, `AZ→BA`, `ZZ→AAA`. Raises `ActionError` on invalid input (empty string, lowercase, non-letter characters).
- **`next_phase_letter(stories_text, archive_dir)` helper** in `actions.py` — implements the post-archive lookup algorithm in Python so future tooling can call it directly (e.g., a future `status` command or a Python-driven `plan_phase` action). The current `plan_phase` mode template describes the same algorithm in prose so the LLM can perform it directly without invoking Python (consistent with v2 architecture).
- **`_find_latest_archived_stories(archive_dir)` helper** — filters `.archive/` to files matching `stories-vX.Y.Z.md` (any stem starting with `stories`), ignoring unrelated archived artifacts like `phase-j-modes-plan.md` or `ux-problems-v2.0.10.md`. Returns the file with the highest semver version, or `None` if none exist.

### Tests
- 16 new tests in `tests/test_actions.py`:
  - **`extract_stories_header_context`** — 3 tests (double-hyphen, em-dash, missing → empty dict).
  - **`increment_phase_letter`** — 7 tests covering simple advance, `Z→AA` carry, two-letter advance, `ZZ→AAA` carry, three-letter advance, and three invalid-input cases.
  - **`next_phase_letter`** — 6 fixture tests covering: populated stories.md returns successor (and ignores `.archive/`), empty stories.md + Phase J archive → `K` (using the real `docs/specs/.archive/stories-v2.0.20.md` fixture), empty stories.md + missing `.archive/` → `A`, empty + empty `.archive/` → `A`, empty + `.archive/` containing only non-stories files → `A`, and empty + multiple archived stories versions picks the highest-version one.
- **193 tests pass** (up from 177).

### Notes
- The `next_phase_letter` Python helper duplicates an algorithm that the LLM can also perform from the rendered mode template. The duplication is deliberate: the v2 architecture prefers LLM-driven detection at read time, but having a Python implementation tested against the same fixture means future code (a `status` validator, a Python-driven plan_phase, or an end-to-end test of the full archive→plan_phase flow) can rely on the algorithm without re-implementing it. The tests assert both implementations stay in sync via the Phase J fixture.

## [2.1.3] - 2026-04-10

### Added
- **`archive_stories` mode** (Story K.d) — new sequence-style mode productionizes the archive pipeline from K.a/K.c:
  - New mode template `project_guide/templates/project-guide/templates/modes/archive-stories-mode.md` walks the LLM through reading the current `stories.md`, warning about any non-`[Done]` stories, showing the planned archive path, awaiting developer approval, running the archive command, and suggesting `plan_phase` as the next mode. Includes the `_phase-letters.md` shared include from K.b.
  - New `archive_stories` entry in `.metadata.yml` under the Post-Release section with `action: archive` on `stories.md`, `next_mode: plan_phase`, and a `files_exist: [stories.md]` prerequisite that surfaces a warning when the source is missing.
- **`project-guide archive-stories` CLI command** — new subcommand that wraps `project_guide.actions.perform_archive`. Loads the project's `.project-guide.yml`, looks up the `archive_stories` mode, finds its archive artifact, resolves the bundled `stories.md` template (always uses the package-bundled copy, not the project's installed templates, so the re-render is not affected by any local template edits), and invokes `perform_archive` with the merged metadata context. Prints a summary: archived path, version, last phase letter, and whether a Future section was carried.
- **`extract_stories_header_context(text)` helper** in `actions.py` — parses the stories.md first-line header (`# stories.md -- <project-name> (<programming-language>)`) into a context dict. `perform_archive` merges extracted values with the caller's context (caller wins) so the fresh re-render preserves the header even when the caller doesn't supply `project_name`/`programming_language` explicitly.

### Changed
- **`render_fresh_stories_artifact` uses lenient undefined rendering.** Missing Jinja context variables now render as `{{ name }}` placeholders instead of empty strings, preventing header corruption like `# stories.md --  (Python)` when a project's metadata doesn't include `project_name`. Implemented via a local `_LenientUndefined` class in `actions.py` (mirrors `render.py._LenientUndefined`; kept local to avoid an import cycle).

### Removed
- **`scripts/spike_archive_stories.py`** — the K.a throwaway script is now superseded by `project_guide.actions.perform_archive` + `project-guide archive-stories`. The empty `scripts/` directory was removed as well.

### Tests
- New `tests/test_archive_stories_mode.py` — 9 end-to-end integration tests using `click.testing.CliRunner`:
  - **Mode template rendering**: `mode archive_stories` renders a go.md containing the mode-specific content, the `project-guide archive-stories` command, the phase-letters include, and the `plan_phase` next-mode suggestion.
  - **Prerequisite warning**: missing `stories.md` surfaces the "Prerequisites not yet met" warning.
  - **Happy path**: `archive-stories` moves the source to `.archive/stories-v1.0.0.md`, preserves the source byte-for-byte, re-renders a fresh `stories.md` with carried Future section and preserved `demo-project` header.
  - **No-Future fallback**: source without a Future section falls back to the template default (HTML-comment explainer present).
  - **Error paths**: missing config, missing source, pre-existing archive target (idempotency guard), no versioned story headings. Each error path verifies the source is left untouched.
- **177 tests pass** (up from 168 after K.c refactor).

### Notes
- The mode template is LLM-conversational (read/warn/show/approve), but the actual mutation is Python-deterministic (`project-guide archive-stories` shelling to `perform_archive`). This keeps the file-mutation logic testable and transactional while the decision-making stays in the LLM conversation.

## [2.1.2] - 2026-04-10

### Added
- **`archive` artifact action type** (Story K.c) — new `project_guide/actions.py` module implements the deterministic archive pipeline:
  - `detect_latest_version(text)` — scans `### Story X.y: vN.N.N` headings and returns the numerically highest version (not lexical).
  - `detect_latest_phase_letter(text)` — scans `## Phase <Letter>:` headings using base-26-no-zero ordering (`A` < `Z` < `AA` < `ZZ` < `AAA`).
  - `extract_future_section(text)` — returns the `## Future` block verbatim to EOF, or `""` if absent.
  - `render_fresh_stories_artifact(template, context, future)` — re-renders the bundled `stories.md` artifact template with an empty body, substituting the template's default `## Future` block with a carried section when provided.
  - `perform_archive(source, template, context)` — end-to-end runtime: moves `source` to `<dirname>/.archive/<stem>-vX.Y.Z<suffix>`, re-renders a fresh source with Future preserved, best-effort rollback on failure. Returns `ArchiveResult(archived_to, source_rewritten, version, phase_letter, future_carried)`.
- **`ActionType` StrEnum** and **`Artifact` dataclass** in `project_guide/actions.py`. `ActionType.CREATE`/`MODIFY`/`ARCHIVE` are the canonical action values; `StrEnum` means `ActionType.ARCHIVE == "archive"` is `True`, so YAML round-trips as bare strings. `Artifact` is a typed, validated representation of a mode's artifact entry (`file | webpage | framework` + `action`).
- **`ActionError` exception** in `project_guide/exceptions.py` for archive action failures at runtime.

### Changed
- **BREAKING: `ModeDefinition.artifacts` is now `list[Artifact]`, not `list[dict]`.** Every mode's `artifacts:` list is parsed into typed `Artifact` dataclass instances during metadata load. Consumers must use attribute access (`artifact.file`, `artifact.action`) instead of dict access (`artifact["file"]`). No CLI/runtime code in this package consumed the old dict shape, so this is only visible to tests and any future external integrations. Pre-release (Phase K) acceptable churn.
- **`metadata.py` validates artifact action values at load time** — any `action:` field on an artifact must be one of `ActionType.{CREATE,MODIFY,ARCHIVE}`. Artifacts without an `action:` field continue to be tolerated (legacy form). Typos like `action: arhive` now fail at metadata load time with a helpful error message listing valid values.

### Tests
- New `tests/test_actions.py` — 30 tests covering: ActionType enum and StrEnum behavior, Artifact dataclass parsing (file/webpage/framework targets, missing action, unknown action, non-mapping input), version/phase/future detection (including negative cases and base-26 ordering), fresh-render behavior, and a real-file round-trip against `.archive/stories-v2.0.20.md` (the Phase J archive).
- Updated tests in `tests/test_metadata.py` — 4 new tests verifying `action: archive` parses to `ActionType.ARCHIVE`, `action: create`/`modify` still parse, missing `action:` yields `artifact.action is None`, and unknown actions raise `MetadataError`. Existing tests updated to use attribute access on `Artifact`.
- **168 tests pass** (up from 133).

### Notes
- This story adds the action **type** only. Wiring the action into a CLI-invocable `archive_stories` mode (new mode template, metadata entry, and the mode command routing it to `perform_archive`) is the next story, K.d.
- The `ActionType`/`Artifact` refactor replaced an earlier in-progress design using bare string constants (`ACTION_CREATE`, `ACTION_MODIFY`, `ACTION_ARCHIVE`, `VALID_ARTIFACT_ACTIONS` frozenset) after a mid-story decision to prioritize code clarity over backward compatibility. No releases shipped with the string-constant form.

## [2.1.1] - 2026-04-10

### Added
- **Phase and Story ID Scheme shared include** (Story K.b) — new template `project_guide/templates/project-guide/templates/modes/_phase-letters.md` documents the base-26-no-zero phase letter scheme (`A`–`Z`, `AA`–`ZZ`, `AAA`–…), the matching story sub-letter scheme, and the rule that letters continue across `archive_stories` boundaries by consulting `docs/specs/.archive/`. The include is now rendered once inside both `plan_stories` and `plan_phase` so the rules live in one place.
- **`## Future` section in the stories artifact template** — `project_guide/templates/project-guide/templates/artifacts/stories.md` now renders a `## Future` section after `{{phases_and_stories}}` with an inline note describing what belongs there (deferred stories, future phases, project-level out-of-scope items). This gives `archive_stories` a canonical place to preserve the "carry-over" section across archive cycles.
- **Tests**: two new tests in `tests/test_render.py` verify the artifact template renders a `## Future` section when `phases_and_stories` is empty and when it is populated (with the Future section appearing after the phases content). 133 tests pass.

## [2.1.0] - 2026-04-10

### Added
- **Spike: archive_stories pipeline** (Story K.a) — throwaway script `scripts/spike_archive_stories.py` exercises the full archive flow end-to-end (latest-version detection, latest-phase-letter detection, `## Future` extraction, archive move, fresh `stories.md` re-render). Validates the critical path before the productionized `archive_stories` mode lands in K.c/K.d. Verified round-trip against a copy of `.archive/stories-v2.0.20.md` (Phase J file): archived file byte-matches the original, fresh `stories.md` contains the carried `## Future` section. Will be deleted in K.d once superseded.

## [2.0.20] - 2026-04-10

### Changed
- **Renamed Jinja2 template source** `templates/go.md` → `templates/llm_entry_point.md`. The rendered output is still `go.md` (unchanged). This eliminates confusion when @-mentioning files in an LLM chat — there's now only one `go.md` (the rendered entry point the LLM reads).

### Added
- **Shell completion for `project-guide mode <TAB>`** — dynamically completes mode names from the active project's `.metadata.yml`. Click's built-in shell completion handles command names and flags automatically.
- Setup instructions for bash, zsh, and fish in [Installation Options](https://pointmatic.github.io/project-guide/user-guide/install-options/).

## [2.0.19] - 2026-04-10

### Changed
- **`update` no longer prompts for modified files** — files whose content differs from the bundled template are now auto-backed-up (`.bak.<timestamp>`) and overwritten without asking. The previous prompt was misleading because hash-based sync can't distinguish "user modified the file" from "the bundled template changed in this version" — both look identical.
- Use `project-guide override <file> <reason>` to lock files that should not be touched by `update`.
- Removed "Modified files detected" / "Skipped (user declined)" / "Updated (approved by user)" output sections.

### Removed
- `sync_files()` no longer returns a `modified` list — its 5-tuple is now a 4-tuple `(updated, skipped, current, missing)`. Files that previously went into `modified` now go into `updated` (with backups).
- `apply_file_update` is no longer used in `cli.py` (still exported from `sync.py` for internal use)

## [2.0.18] - 2026-04-10

### Fixed
- **`go.md` is no longer gitignored** — agentic LLMs that respect gitignore patterns couldn't read the rendered entry point, breaking the entire workflow. The file is now tracked in git, which also gives mode switches a useful git history footprint.
- **Mode heading bug** — planning mode templates rendered `# concept.md — {{ project_name }}` (with the literal Jinja2 placeholder, since `project_name` was never defined). Replaced with a single mode heading in `_header-common.md` that uses actual metadata: `# {{ mode_name }} mode ({{ sequence_or_cycle }})` followed by a `> {{ mode_info }}` blockquote.

### Changed
- `_ensure_gitignore_entry()` no longer adds `go.md` to `.gitignore` (only `*.bak.*` patterns remain)
- All 14 mode templates stripped of their individual H1 headings in favor of the centralized mode heading from `_header-common.md`

## [2.0.17] - 2026-04-09

### Changed
- **Renamed `project_setup` mode to `project_scaffold`** — "setup" was too generic; "scaffold" matches the mode's actual purpose (creating project files) and industry conventions. Breaking change for anyone using `project-guide mode project_setup`.
- Renamed template file: `project-setup-mode.md` → `project-scaffold-mode.md`
- Slimmed down `docs/site/user-guide/workflow.md` from 376 lines to ~85 lines, removing duplication with getting-started, commands, and overrides pages

### Added
- `docs/site/user-guide/modes.md` — comprehensive reference for all 15 modes with type, prerequisites, artifacts, and Mode Flow diagram
- "When to Switch Modes" table and "The HITLoop Cycle" section in workflow guide

## [2.0.13] - 2026-04-09

### Changed
- `status` command redesigned with grouped sections: Mode (with prerequisites), Guide, Files — each with contextual action prompts
- File sync now uses content hash comparison instead of version comparison — a version bump no longer marks unchanged files as stale
- `(installed: vX.X.X)` only shown in status when it differs from package version
- Prerequisites line omitted when the mode has none
- Renamed `go-project-guide.md` → `go.md` — shorter, easier to autocomplete

### Removed
- Version-based file freshness check — `compare_versions` no longer used by `status` or `sync_files`

## [2.0.12] - 2026-04-08

### Changed
- `status` command redesigned: compact summary by default, per-file list only when problems exist
- Status header now shows `Target:` directory, mode on one line with description
- Added `--verbose` / `-v` flag to force full per-file list
- Status footer shows `Run 'project-guide mode' to see available modes.`
- Renamed "guides" to "files" throughout: the sync system tracks files, not guides
  - `--guides` CLI flag → `--files`
  - `GuideNotFoundError` → `ProjectFileNotFoundError`
  - `GuideOverride` → `FileOverride`
  - sync.py: `get_all_guide_names` → `get_all_file_names`, `copy_guide` → `copy_file`, `backup_guide` → `backup_file`, `apply_guide_update` → `apply_file_update`, `sync_guides` → `sync_files`
  - All user-facing strings updated

## [2.0.11] - 2026-04-08

### Changed
- Rendered `go-project-guide.md` now outputs to `docs/project-guide/` instead of `docs/specs/` — it's mode instructions, not a spec artifact
- Entry point template moved from `project-guide/go-project-guide.md` to `project-guide/templates/go-project-guide.md`
- Jinja2 loader simplified to search only the `templates/` subdirectory
- Developer instruction in `_header-common.md` updated to `Read docs/project-guide/go-project-guide.md`
- `.gitignore` entry updated to `docs/project-guide/go-project-guide.md`
- `target_dir` now available as a Jinja2 context variable in templates

## [2.0.10] - 2026-04-08

### Fixed
- `init` now starts in `default` mode instead of `plan_concept`
- `files_exist` prerequisites no longer include template paths that resolve to repo-internal locations; only user-created spec artifacts are checked

### Changed
- Renamed metadata file from `project-guide-metadata.yml` to `.metadata.yml` (hidden, shorter — already scoped by `project-guide/` directory)
- Added `metadata_file` field to `.project-guide.yml` config — CLI reads the metadata filename from config instead of hardcoding it
- Render errors now show actionable guidance: run `project-guide status` and `project-guide update`
- `sync.py` guide discovery now includes dotfiles (`.*.yml` pattern)

### Added
- Parametrized test that renders every mode from the bundled metadata — proves a fresh install works and catches regressions

## [2.0.9] - 2026-04-07

### Added
- New `refactor_plan` cycle mode — migrate planning artifacts (concept, features, tech-spec) to v2.x artifact template format
- New `refactor_document` cycle mode — migrate documentation artifacts (descriptions, landing page, MkDocs) to v2.x format
- v1.x → v2.x migration notice in `status` command when config version is "1.0" or target_dir is "docs/guides"

## [2.0.8] - 2026-04-07

### Added
- New `project_setup` mode -- one-time project scaffolding (LICENSE, copyright headers, package manifest, README with badges, CHANGELOG, .gitignore)
- `project-setup-mode.md` template with step-by-step setup instructions and approval checklist

### Changed
- `default-mode.md` slimmed to pure navigation -- project lifecycle overview with mode table, no setup instructions
- Mode flow updated: `default` -> `project_setup` -> `plan_concept` -> ... -> `code_velocity`
- `project_setup` added to `project-guide-metadata.yml` between `default` and `plan_concept`

## [2.0.7] - 2026-04-07

### Added
- 5 new tests for `mode` command (no config, list modes, invalid name, config update, render output)
- `mode` command added to README Command Reference

### Changed
- README updated for v2.0: new Quick Start with mode workflow, Available Modes table, updated config example, corrected test stats (112 tests, 92% coverage)
- Test coverage increased from 90% to 92% (112 tests, up from 107)

## [2.0.6] - 2026-04-07

### Changed
- `default-mode.md` rewritten as a full project lifecycle overview (setup, planning, implementation) with links to specific modes -- serves as a friendly starting point for new users
- Distributed prerequisites from old default mode into appropriate planning modes:
  - Project idea -> `plan-concept-mode.md`
  - License preference, target audience, constraints -> `plan-features-mode.md`
  - Language/runtime, preferred frameworks -> `plan-tech-spec-mode.md`
- Added `default` mode to `project-guide-metadata.yml`

### Removed
- `best-practices-guide.md` -- content absorbed into `code-velocity-mode.md` and `code-test-first-mode.md`

## [2.0.5] - 2026-04-07

### Added
- Brand descriptions artifact template (`templates/artifacts/brand-descriptions.md`)

### Fixed
- Renamed `brand-mode.md` to `document-brand-mode.md` and `document-mode.md` to `document-landing-mode.md` to match metadata definitions
- Added missing `mode_template` field to `document_landing` mode in metadata
- Escaped GitHub Actions `${{ }}` syntax in `document-landing-mode.md` to prevent Jinja2 conflict
- Converted `{info}` / `{description}` placeholders in brand mode to Jinja2 `{{ mode_info }}` / `{{ mode_description }}`

## [2.0.4] - 2026-04-07

### Added
- Complete `code-velocity-mode.md` -- velocity coding workflow with cycle steps, practices, and mode switching guidance
- Complete `code-test-first-mode.md` -- TDD workflow with red-green-refactor cycle, test writing guidelines, and test hierarchy
- `debug-mode.md` already complete from prior work (retained as-is)
- All cycle mode templates include `{% include "modes/_header-cycle.md" %}`

## [2.0.3] - 2026-04-07

### Added
- Complete planning mode templates: `plan-features-mode.md`, `plan-tech-spec-mode.md`, `plan-stories-mode.md`, `plan-phase-mode.md`
- Artifact templates: `features.md`, `tech-spec.md`, `stories.md`
- All mode templates now include appropriate header partials (`_header-sequence.md` or `_header-cycle.md`)

### Fixed
- Entry point template renamed to `go-project-guide.md.j2` to prevent rendered output from overwriting the Jinja2 source template
- Explicit `encoding="utf-8"` in Jinja2 `FileSystemLoader` and `write_text()` to fix Windows cp1252 corruption of em-dash characters

### Changed
- Monolithic Steps 0-4 content removed from `go-project-guide.md.j2` — entry point is now a thin shell (header + mode include)

## [2.0.2] - 2026-04-07

### Changed
- `update` command re-renders `go-project-guide.md` after syncing template files that affect the rendered output
- Override/unoverride work on template-relative paths (e.g., `templates/modes/plan-concept-mode.md`)
- Guide discovery in `sync.py` fully scans new directory structure (old `guides/` references removed)

## [2.0.1] - 2026-04-07

### Changed
- `status` command now shows current mode name, description, guide path, and prerequisite status before guide sync details
- Windows cross-platform fix: guide names in `sync.py` always use forward slashes via `as_posix()`

## [2.0.0] - 2026-04-07

### Added
- **Mode-driven template system** — `project-guide mode <name>` sets the active development mode and renders `go-project-guide.md` via Jinja2
- New `mode` CLI command: set mode with argument, list available modes without argument
- New module `metadata.py` — parses `project-guide-metadata.yml`, resolves `{{var}}` placeholders, provides mode lookup
- New module `render.py` — Jinja2 template rendering pipeline for `go-project-guide.md`
- New runtime dependency: `jinja2>=3.1`
- New exception types: `MetadataError`, `RenderError`
- `go-project-guide.md` automatically added to `.gitignore` on init (it is a rendered artifact)
- 11 foundation mode templates: `default`, `plan_concept`, `plan_features`, `plan_tech_spec`, `plan_stories`, `plan_phase`, `code_velocity`, `code_test_first`, `debug`, `document_brand`, `document_landing`
- Artifact templates directory (`templates/artifacts/`) for LLM output formatting
- Header partials (`_header-common.md`, `_header-sequence.md`, `_header-cycle.md`) included via Jinja2

### Changed
- **Breaking:** Default target directory changed from `docs/guides/` to `docs/project-guide/`
- **Breaking:** Config schema version bumped to `2.0` with new `current_mode` field
- `init` now copies the full template tree (modes, artifacts, metadata, developer guides) and renders `go-project-guide.md`
- Template discovery in `sync.py` updated for new directory structure
- Old static guide files (`project-guide.md`, `debug-guide.md`, `documentation-setup-guide.md`) replaced by mode templates
- Config migration: v1.0 configs load with `current_mode: "default"` added automatically
- Test suite expanded to 102 tests (up from 87), coverage at 87%

## [1.5.2] - 2026-04-05

### Added
- 28 new CLI tests covering error paths, edge cases, and user prompts (87 total, up from 59)
- Codecov badge added to README.md

### Changed
- Test coverage increased from 79% to 94% (cli.py: 72% → 97%)
- Minimum coverage threshold raised from 75% to 85% (`--cov-fail-under`)

## [1.5.1] - 2026-04-04

### Changed
- **Renamed Python module directory from `project_guides/` to `project_guide/`**
  - All internal imports updated to `project_guide.*`
  - `importlib.resources` package paths updated to `project_guide.templates.*`
  - All test imports updated
  - GitHub Actions workflows updated (`--cov=project_guide`, `mypy project_guide/`, `ruff check project_guide/`)
  - `pyproject.toml` entry point updated to `project_guide.cli:main`

## [1.5.0] - 2026-04-03

### Changed
- **Removed `project-guides` CLI entry point** — only `project-guide` is now installed
  - Existing users must reinstall: `pip install project-guide`
- Updated all user-facing CLI messages to reference `project-guide`
- Updated guide template to reference `pip install project-guide` and `project-guide init`

### Breaking Change
- The `project-guides` command is no longer installed. Replace all uses with `project-guide`.

## [1.4.1] - 2026-04-03

### Changed
- **Renamed config file from `.project-guides.yml` to `.project-guide.yml`**
  - All CLI commands now read and write `.project-guide.yml`
  - Automatic one-time migration: if `.project-guides.yml` exists and `.project-guide.yml` does not, the file is renamed on next command run with a printed notice
  - Template updated to `.project-guide.yml.template`

## [1.4.0] - 2026-04-03

### Added
- **Reserved `project-guide` package name on PyPI**
  - Added `project-guide` as a second CLI entry point (maps to the same `project_guides.cli:main`)
  - Both `project-guides` and `project-guide` commands work identically
  - Existing users are unaffected; new users should install `project-guide`
  - The old `project-guides` entry point will be removed in v1.5.0

## [1.3.1] - 2026-03-25

### Added
- **Prompt before overwriting user-modified guides**
  - `update` command now prompts `Overwrite <guide>? [y/N]` for each modified file
  - User can accept or decline per-file — declined files are reported as skipped
  - `--force` flag skips the prompt, creates a `.bak` backup, and overwrites automatically
  - `--dry-run` shows modified files with a note that they would be prompted

### Changed
- `sync_guides()` now returns 5-tuple `(updated, skipped, current, missing, modified)`
  - `modified`: files with user edits detected but not yet acted on (caller decides)
  - `--force` moves modified files directly to `updated` list after creating backup
- `update` output now shows "Updated (backed up):" label when `--force` is used
- Test suite expanded to 59 tests with `test_sync_guides_force_overwrites_modified_with_backup`

## [1.3.0] - 2026-03-25

### Added
- **Content-based change detection** in `update` command
  - New `file_matches_template()` function uses SHA-256 hash to compare file content with templates
  - Detects user modifications even when version numbers match
  - `status` command now shows "(modified)" for files with user edits
- **Missing file detection** in `update` command
  - Missing files are now properly detected and reported separately
  - `update` command displays missing files in cyan with "+" indicator
  - Missing files are always created, even if version numbers match

### Fixed
- **Critical bug**: `update` command incorrectly reported "all guides are up to date" when files were missing
- **Critical bug**: `update` command didn't detect user modifications to guide files
- `sync_guides()` now returns 4-tuple `(updated, skipped, current, missing)` instead of 3-tuple

### Changed
- Enhanced `status` command output to differentiate between:
  - Outdated version: "(update available)"
  - User modifications: "(modified)"
  - Missing files: "(missing)"
- Test suite expanded from 53 to 58 tests with 5 new comprehensive tests

## [1.2.7] - 2026-03-10

### Fixed
- **README banner image URL**
  - Changed from relative path to absolute GitHub URL for PyPI compatibility
  - Banner now displays correctly on https://pypi.org/project/project-guides/

## [1.2.6] - 2026-03-10

### Fixed
- **Version comparison bug in sync_guides**
  - Fixed logic to properly mark guides as "current" when installed_version matches package_version
  - Added check for non-existent files when versions match
  - Updated test to use dynamic version import instead of hardcoded value

## [1.2.5] - 2026-03-10

### Changed
- **Updated README.md** with comprehensive documentation integration
  - Added header banner image
  - Updated description with Two-clause Technical Description
  - Added Documentation badge linking to GitHub Pages
  - Added dedicated Documentation section with links to full docs
  - Updated "Why project-guides?" with Friendly Brief Description and HITLoop explanation
  - Updated Key Features with content from Feature Cards
- **Updated pyproject.toml** metadata
  - Added project.urls section (Homepage, Documentation, Repository, Issues, Changelog)
  - Expanded keywords to 18 items matching descriptions.md

## [1.2.4] - 2026-03-10

### Added
- **GitHub Actions workflow** for automated documentation deployment
  - `.github/workflows/deploy-docs.yml` for deploying to GitHub Pages
  - Triggers on push to main branch and manual workflow_dispatch
  - Builds with strict mode to fail on warnings
  - Deploys to https://pointmatic.github.io/project-guides/

## [1.2.3] - 2026-03-10

### Added
- **Comprehensive documentation pages** in `docs/site/`
  - Getting Started: installation.md, quick-start.md, configuration.md
  - User Guide: commands.md, workflow.md, overrides.md
  - Developer Guide: contributing.md, development.md, testing.md
  - About: license.md, changelog.md
- All pages include cross-references and internal links
- Documentation verified with `mkdocs build --strict`

## [1.2.2] - 2026-03-10

### Added
- **Custom branded landing page** at `docs/site/index.html`
  - Dark theme with teal accent colors
  - Hero section with tagline and banner image
  - Friendly Brief Description explaining HITLoop workflow
  - Quick Start section with 7-step workflow
  - 15 Feature Cards organized into 3 categories (Core, Operational, Philosophy)
  - Responsive design with navigation and footer

## [1.2.1] - 2026-03-10

### Added
- **MkDocs documentation infrastructure**
  - `mkdocs.yml` configuration with Material theme
  - Dark/light mode toggle with teal accent
  - Navigation structure for all documentation sections
  - Markdown extensions (admonition, superfences, highlight, etc.)
  - Plugins: search, git-revision-date-localized
  - `docs/site/.gitignore` for MkDocs cache
  - Updated root `.gitignore` to ignore `/site/` build output
  - Added `[docs]` optional dependency group in pyproject.toml

## [1.2.0] - 2026-03-10

### Added
- **Canonical project descriptions** in `docs/specs/descriptions.md`
  - Project name, taglines (short and long), one-liner
  - Friendly Brief Description explaining HITLoop workflow
  - Two-clause Technical Description
  - Benefits list (10 items)
  - Technical Description (3 paragraphs)
  - Keywords (18 items including HITLoop)
  - Quick Start section (7 essential steps)
  - Feature Cards (15 cards in 3 categories)
  - Usage Notes mapping descriptions to consumer files

### Changed
- **Updated README.md** with canonical descriptions
  - Line 8: Two-clause Technical Description
  - Line 12: Friendly Brief Description (first sentence)
- **Updated pyproject.toml**
  - Description field: Long Tagline
- **Updated docs/specs/features.md**
  - Line 11: Two-clause Technical Description
- **Enhanced project-guide.md template**
  - Added "How to Use This Guide" section
  - Clarified "proceed" language for step-by-step workflow

## [1.1.3] - 2026-03-09

### Added
- **GitHub repository setup section** in `production-mode.md` guide
  - Branch protection rules with UI-matching checklist format
  - Security settings: Dependency graph, Dependabot alerts, security updates, grouped updates
  - GitHub Actions permissions guidance (Read-only by default)
  - Uses `default` branch for flexibility (works with `main` or `master`)

### Changed
- **Updated `project-guide.md` prerequisites**
  - Clarified developer must provide OR LLM must ask for requirements
  - Documented that project idea is often in `docs/specs/concept.md`
- **Updated `templates/guides/README.md`**
  - Added production mode workflow to developer guide list
  - Clarified LLMs may reference developer guides for step-by-step instructions

## [1.1.2] - 2026-03-09

### Changed
- **Modernized Git commands** in `production-mode.md` guide template
  - Updated `git checkout` to `git switch` for switching branches
  - Updated `git checkout -b` to `git switch -c` for creating branches
  - Updated `git branch -d` to `git branch --delete` for clarity
  - Updated `git branch -D` to `git branch --delete --force` for explicit force deletion
  - All workflow examples, quick references, and troubleshooting sections updated
- **Refactored test suite** to eliminate version number scatter
  - Tests now use `__version__` import instead of hardcoded version strings
  - Makes tests self-maintaining across version bumps
  - Only `version.py` needs updating for future releases

## [1.1.0] - 2026-03-03

### Added
- **`purge` command** to remove all project-guides files from a project
  - `--force` flag to skip confirmation prompt
  - Removes `.project-guides.yml` and guides directory
  - Handles missing files gracefully
  - Comprehensive error handling
- 5 new tests for purge command (total: 53 tests)

### Changed
- Updated README with purge command documentation
- Command count increased from 6 to 7

## [1.0.0] - 2026-03-03

### Added
- First stable release! 🎉
- Production-ready with 48 tests and 82% coverage
- Complete documentation and guides
- GitHub Actions CI/CD workflows
- Automated PyPI publishing on release

### Changed
- Development status updated to Production/Stable
- All features complete and tested

## [0.15.0] - 2026-03-03

### Added
- Comprehensive README with badges, installation instructions, and full command reference
- Quick start guide with 4-step workflow
- Troubleshooting section with common issues and solutions
- Contributing guidelines and development setup instructions
- Support links for issues, discussions, and documentation

### Changed
- Enhanced documentation throughout

## [0.14.0] - 2026-03-03

### Added
- Code quality tools: ruff linter and mypy type checker
- Comprehensive linting rules (E, W, F, I, N, UP, B, C4, SIM)
- Type hints throughout codebase
- `types-PyYAML` for type stubs
- GitHub Actions workflows (ci.yml, publish.yml, test.yml)
- Dependabot configuration for automated dependency updates
- GitHub Sponsors funding configuration placeholder
- Open Source Sustainability section in best-practices-guide.md

### Changed
- All code passes ruff and mypy checks with zero errors
- Line length configured to 100 characters

## [0.13.0] - 2026-03-03

### Added
- Integration tests for end-to-end workflows
- Test for full init → override → update workflow
- Test for version upgrade scenarios
- Test for force update with backups
- Test for multiple projects in isolation
- Test for dry-run mode
- Test for specific guide updates

### Changed
- Test coverage increased to 82% (48 tests total)

## [0.12.0] - 2026-03-03

### Added
- Colored CLI output using `click.secho()`
- Explicit exit codes for different error types:
  - 0 for success
  - 1 for general errors
  - 2 for file I/O errors
  - 3 for configuration errors
- Formatted tables with proper alignment in status output

### Changed
- All CLI commands now use colored output for better UX
- Error messages are more visually distinct

## [0.11.0] - 2026-03-03

### Added
- Custom exception classes for structured error handling:
  - `ProjectGuidesError` - Base exception
  - `ConfigError` - Configuration-related errors
  - `SyncError` - Sync operation failures
  - `GuideNotFoundError` - Missing guide templates
- Helpful error messages with actionable suggestions
- Error handling for missing config files
- Error handling for invalid YAML
- Error handling for permission errors
- Error handling for invalid guide names

### Changed
- All modules updated to use custom exceptions
- CLI commands catch and format errors appropriately

## [0.10.0] - 2026-03-03

### Added
- `overrides` command to list all overridden guides
- Display override reason, version, and last updated date

## [0.9.0] - 2026-03-03

### Added
- `override` command to mark guides as customized
- `unoverride` command to remove override status
- Override tracking in configuration with reason and metadata

### Changed
- Update command now skips overridden guides by default
- Force flag creates backups when updating overridden guides

## [0.8.0] - 2026-03-03

### Added
- `update` command to sync guides to latest version
- `--guides` flag to update specific guides only
- `--force` flag to update even overridden guides (with backups)
- `--dry-run` flag to preview changes without applying

## [0.7.0] - 2026-03-03

### Added
- `status` command to show guide installation status
- Display current vs. installed version
- Show which guides are current, outdated, or overridden
- Color-coded status indicators

## [0.6.0] - 2026-03-03

### Added
- `sync_guides()` orchestration function
- Override checking during sync
- Version comparison logic
- Dry-run mode support
- Force update with automatic backups

### Changed
- Sync module now handles complex update scenarios

## [0.5.0] - 2026-03-03

### Added
- `backup_guide()` function with timestamp-based naming
- `compare_versions()` function using `packaging.version`
- Version comparison for update detection

## [0.4.0] - 2026-03-03

### Added
- `copy_guide()` function to copy templates to target directory
- Force flag to overwrite existing files
- Subdirectory support for developer guides
- Permission error handling

## [0.3.0] - 2026-03-03

### Added
- Template bundling as package data
- `get_template_path()` function using `importlib.resources`
- `get_all_guide_names()` function to list available guides
- Support for developer subdirectory guides

## [0.2.0] - 2026-03-03

### Added
- Configuration model with dataclasses
- `Config.load()` and `Config.save()` methods
- YAML serialization/deserialization
- Override tracking in configuration
- `GuideOverride` dataclass for metadata

## [0.1.0] - 2026-03-03

### Added
- Initial package structure with Hatchling
- Basic CLI framework with Click
- `init` command to initialize project guides
- `--target-dir` and `--force` flags
- Apache 2.0 license
- Core guide templates:
  - project-guide.md
  - best-practices-guide.md
  - debug-guide.md
  - documentation-setup-guide.md
  - developer/codecov-setup-guide.md
  - developer/github-actions-guide.md

[Unreleased]: https://github.com/pointmatic/project-guides/compare/v1.5.1...HEAD
[1.5.1]: https://github.com/pointmatic/project-guides/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/pointmatic/project-guides/compare/v1.4.1...v1.5.0
[1.4.1]: https://github.com/pointmatic/project-guides/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/pointmatic/project-guides/compare/v1.3.1...v1.4.0
[1.3.1]: https://github.com/pointmatic/project-guides/compare/v1.3.0...v1.3.1
[1.1.3]: https://github.com/pointmatic/project-guides/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/pointmatic/project-guides/compare/v1.1.0...v1.1.2
[1.1.0]: https://github.com/pointmatic/project-guides/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/pointmatic/project-guides/compare/v0.15.0...v1.0.0
[0.15.0]: https://github.com/pointmatic/project-guides/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/pointmatic/project-guides/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/pointmatic/project-guides/compare/v0.12.0...v0.13.0
[0.12.0]: https://github.com/pointmatic/project-guides/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/pointmatic/project-guides/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/pointmatic/project-guides/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/pointmatic/project-guides/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/pointmatic/project-guides/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/pointmatic/project-guides/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/pointmatic/project-guides/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/pointmatic/project-guides/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/pointmatic/project-guides/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/pointmatic/project-guides/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/pointmatic/project-guides/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pointmatic/project-guides/releases/tag/v0.1.0
