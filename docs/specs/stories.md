# stories.md -- project-guide (python)

This document breaks the `project-guide` project into an ordered sequence of small, independently completable stories grouped into phases. Each story has a checklist of concrete tasks. Stories are organized by phase and reference modules defined in `tech-spec.md`.

Put **`vX.Y.Z` in the story title only when that story ships the package version bump** for that release. Doc-only or polish stories **omit the version from the title** (they share the release with the preceding code story, or use your project’s doc-release policy). **One semver bump per owning story** — extra tasks on the *same* story share that bump; see `project-essentials.md`. Semantic versioning applies to the package. Stories are marked with `[Planned]` initially and changed to `[Done]` when completed.

For a high-level concept (why), see [`concept.md`](concept.md). For requirements and behavior (what), see [`features.md`](features.md). For implementation details (how), see [`tech-spec.md`](tech-spec.md). For project-specific must-know facts, see [`project-essentials.md`](project-essentials.md) (`plan_phase` appends new facts per phase). For the workflow steps tailored to the current mode (cycle steps, approval gates, conventions), see [`docs/project-guide/go.md`](../project-guide/go.md) — re-read it whenever the mode changes or after context compaction.

---

## Version Cadence

Standard semantic versioning, with these conventions:

- **Every story belongs to a phase.** Bugfix stories included. No orphan stories.
- **Per-story bumping** (when a story owns its own release):
  - Bugfix or trivial change → **patch** (`vX.Y.Z+1`)
  - Feature or improvement → **minor** (`vX.Y+1.0`)
  - Breaking change → **major** (`vX+1.0.0`). Post-1.0 only, and only via the `plan_production_phase` mode, which negotiates with the developer about whether the breakage is substantively user-facing or technically-but-trivially breaking (example: a log-format change is technically breaking, but if logs aren't a core consumer capability, the developer may judge it minor or even patch).
- **Phase-bundling option:** a phase can run unversioned during work and ship a single release/tag at end-of-phase. Stories within the phase carry no version in their title; the phase's last story owns the bump (magnitude determined by the highest-impact change in the bundle).
- **No out-of-order implementation.** Story order in this file is the order of execution. If work order needs to change, **reorganize/renumber here first** — don't skip ahead and create version-number gaps.
- **Pre-1.0:** standard semver applies; version starts at `v0.1.0` (Story A.a).
- **Post-1.0:** every phase must go through `plan_production_phase` (the lighter `plan_phase` is pre-1.0 only). Major bumps only happen through that mode's negotiation step.

This is the authoritative cadence rule. **Do not extrapolate the bump magnitude from `pyproject.toml`'s current version** — re-read this section whenever you're about to assign a version to a story.

---

## Phase R: Quality of Life Improvements and Bug Fixes

---

### Story R.a: v2.18.1 Gitbetter `git-commit` subcommand [Done]

Gitbetter just added a `git-commit` subcommand to allow iterations on commits locally and then pushing a batch to GitHub, which will save substantially on GitHub Actions CI minutes. 

This new `project-guide git-commit` subcommand is nearly identical to its sibling `project-guide git-push`. From the Project Guide perspective, the two commands have the identical interface and behavior. 

- [x] Add `project-guide git-commit` subcommand that mirrors `project-guide git-push` functionality — both share `_run_gitbetter_wrapper(tool_name, …)` in `cli.py`
- [x] Update tests to cover the new command — 8 new `test_git_commit_*` tests (636 passed total)
- [x] Update documentation to reflect the new command — README, site commands.md, concept/features/tech-spec/project-essentials
- [x] Bump patch version to `v2.18.1` — `version.py`, `pyproject.toml`, CHANGELOG dated 2026-08-01

---

## Subphase R-1: Shell Completion Fixes

Shell completion is not working properly from a bare install. This needs to be corrected, as documented in `docs/specs/shell-completion-ownership.md`.

project-guide gains a `completion` command group and takes ownership of the protocol it generates, replacing the block pyve hand-writes into the user's rc file today. Full plan, decisions, and out-of-scope negotiation: [`phase-r-subphase-1-shell-completion-plan.md`](phase-r-subphase-1-shell-completion-plan.md). Ships as one bundled release, **`v2.19.0`** (Story R.i); stories before it run unversioned.

**Route decisions** (from the plan): **zsh** uses the fpath autoload file its `#compdef` script is built for; **bash** uses an rc-block eval, the only route available to it. Shell scope is zsh + bash — fish is deferred.

---

### Story R.b: Integration spike — off-`PATH` completion [Done]

**Spike — time-boxed, throwaway. The deliverable is a documented decision, not production code.**

Inspecting Click's generated scripts revealed that the change request's central claim — *"`--bin` is the whole of the interface"* — is incomplete. Every generated callback embeds the **bare command name** and resolves it through `PATH` **at completion time**, long after the rc block ran:

```zsh
(( ! $+commands[project-guide] )) && return 1
response=(... $(env COMP_WORDS=... _PROJECT_GUIDE_COMPLETE=zsh_complete project-guide))
```

Baking an absolute path into the rc block fixes only the *generation* call at shell startup. With the binary off `PATH`, zsh's `$+commands` guard returns empty before it even tries; bash's `$1` lookup fails equivalently. project-guide must therefore **post-process** Click's output rather than emit it verbatim — and that is unproven.

Everything downstream depends on the answer: if post-processing is infeasible, `--bin`'s contract with pyve changes and R.c–R.g are written differently.

- [x] Reproduce the failure: binary off `PATH`, completion installed by absolute path, confirm zsh and bash both yield nothing — zsh driven end-to-end through `zsh/zpty` with a real TAB; both shells yield nothing, bash additionally prints `env: project-guide: No such file or directory`
- [x] Prototype post-processing for zsh — substitute the absolute path, neutralize the `(( ! $+commands[...] ))` guard; confirm completion works off `PATH` — guard replaced with `[[ -x <bin> ]] || return 1`; 12 completions off `PATH`
- [x] Prototype the bash equivalent — substitute for `$1` in the `env ... $1` invocation — plus an **added** `[[ -x <bin> ]]` guard bash doesn't ship with (Amendment 2)
- [x] Determine whether post-processing must differ between the zsh fpath route and the bash rc route — it does not; Click's `loadautofunc` branch handles registration, so one generator serves both (Amendment 1)
- [x] Check whether Click's generated output is stable enough to post-process by pattern, or whether a version guard against the installed Click is needed — byte-identical across Click 8.1.8 → 8.4.0 (8.4.2 differs by one blank line); no version guard, assert each substitution matches exactly once instead
- [x] Write the outcome into the subphase plan as a **Spike result** section — the chosen approach, what was rejected, and any revision to `--bin`'s contract — [`phase-r-subphase-1-shell-completion-plan.md`](phase-r-subphase-1-shell-completion-plan.md) § "Spike result (Story R.b)"
- [x] Discard the prototype code — scratchpad only; nothing landed in the repo

**Outcome: post-processing is viable.** `--bin`'s contract with pyve holds, and R.c–R.i proceed as planned with four amendments recorded in the plan: (1) the transformation is route-independent; (2) bash needs an executable guard project-guide *adds*, or a stale install prints on every TAB; (3) post-process only when `--bin` is absolute, else emit Click's script verbatim; (4) macOS bash 3.2 registers **nothing** (`complete -o nosort` is bash ≥ 4.4), which is worse than the `compopt` limitation currently recorded as out of scope. No version bump — spike, no shipped code.

### Story R.c: `completion` command group scaffold + `show` [Planned]

The read-only slice: everything needed to *produce* a correct script, with no filesystem writes. Establishes the group, shell detection, and the post-processing proven in R.b.

- [ ] Add the `completion` Click group with `--shell auto|zsh|bash` resolution (`auto` reads `$SHELL`, falling back to an explicit error rather than a guess)
- [ ] Implement script generation via Click's `_PROJECT_GUIDE_COMPLETE=<shell>_source` protocol
- [ ] Apply the R.b post-processing so the emitted script does not depend on `PATH` — one generator for both shells (R.b Amendment 1); each substitution must match **exactly once** or hard-error naming the failed pattern (no Click version guard, per the R.b stability finding)
- [ ] Implement `--bin` resolution: explicit flag → project-guide's own resolved absolute path → bare-name `PATH` fallback. Post-process **only** when the result is absolute; on the bare-name fallback emit Click's script verbatim (R.b Amendment 3 — the baked guard is a filesystem test)
- [ ] `completion show` prints the post-processed script to stdout; no writes, no prompts
- [ ] Tests: per-shell generation, `--bin` resolution order, `--shell auto` detection, unsupported-shell error
- [ ] Verify `--quiet` / `--no-input` interaction is coherent for a stdout-producing command

### Story R.d: `completion install` / `uninstall` — bash rc-block route [Planned]

The rc-block writer and its sentinel machinery. This is the first project-guide code that writes **outside the project directory**, so the safety contract is the story.

- [ ] Write a sentinel-bracketed block to the resolved rc file (`--rc` override; default `~/.bashrc`)
- [ ] Idempotent: re-running with an already-current block is a no-op
- [ ] `uninstall` removes the block **byte-clean**, so `install` → `uninstall` round-trips the rc file exactly
- [ ] Ours-vs-foreign predicate: only project-guide's own sentinel is touched; foreign content under a similar header is left alone with a stderr warning (mirrors `_ensure_gitignore_entry()`)
- [ ] Back up the rc file before first modification
- [ ] Degrade silently at shell startup — a broken or stale block must never print. Also silent **at completion time**: the R.b Amendment 2 `[[ -x <bin> ]]` guard, or bash prints `env: …: No such file or directory` on every TAB against a stale `--bin`
- [ ] Decide whether to strip `complete -o nosort` (bash ≥ 4.4) so completion registers at all on macOS system bash 3.2 — R.b Amendment 4; verified that stripping restores registration, at the cost of Click's unsorted ordering
- [ ] Tests: fresh install, idempotent re-install, round-trip byte-equality, foreign-block refusal, missing rc file

### Story R.e: `completion install` / `uninstall` — zsh fpath route [Planned]

The asymmetric half. zsh gets the autoload file its `#compdef` header is designed for, which means two on-disk artifacts instead of one.

- [ ] Write the post-processed script to a zsh autoload directory as `_project-guide`
- [ ] Add the `fpath` line plus the `compinit` bootstrap to the rc file, sentinel-bracketed
- [ ] Bootstrap shape: `(( $+functions[compdef] )) || { autoload -Uz compinit && compinit -i; } 2>/dev/null` — leave an existing `compinit` alone
- [ ] `uninstall` removes **both** the autoload file and the rc block
- [ ] Idempotency and byte-clean round-trip hold across both artifacts
- [ ] Tests: fresh install, re-install, round-trip, partial state (file present but rc line absent, and the reverse)

### Story R.f: `completion status` [Planned]

Makes failure inspectable — the surface whose absence let both field defects hide.

- [ ] Report per shell: **absent** / **installed** / **stale**
- [ ] **Stale** = a baked `--bin` path that no longer resolves — the pyve-toolchain-bump case
- [ ] Detect partial installs (zsh file without rc line, or the reverse) and report them distinctly
- [ ] Exit-code semantics consistent with the existing CLI conventions
- [ ] Tests: each state per shell, including partial and stale

### Story R.g: Legacy pyve sentinel adoption [Planned]

Users already carry pyve's block. Without this, `install` produces a second block registering the same completion.

- [ ] Detect pyve's exact legacy sentinel pair (`# >>> project-guide completion (added by pyve) >>>` … `# <<< project-guide completion <<<`)
- [ ] Replace it with project-guide's own block and report the replacement in one line
- [ ] Belt-and-braces with pyve's own upgrade-path cleanup — the two tools upgrade independently, so neither may assume the other ran
- [ ] Tests: legacy block present alone, legacy + project-guide block both present, legacy block hand-modified

### Story R.h: `heal` stale-completion warning [Planned]

Follows the established warn-don't-auto-fix pattern (tracked-`go.md`, local-install-under-pyve). Catches the pyve toolchain-version bump that rots a baked path.

- [ ] `heal` warns on stderr when completion is installed but **stale**
- [ ] Warning names the dead path and gives the copyable remedy (`project-guide completion install`)
- [ ] **Never auto-repairs** — writing to a user's rc file without being asked is out of bounds, same constraint that bounds the `git-push` wrapper
- [ ] Silent when completion is absent (an uninstalled convenience is not drift) and when current
- [ ] Preserves the auto-hook's steady-state silence
- [ ] Tests: stale warns, current silent, absent silent, `--no-input` unaffected

### Story R.i: `v2.19.0` Subphase R-1 bundled release [Planned]

Documentation and the single release tag for the subphase.

- [ ] Rewrite `features.md` FR-7 — replace the hand-copied-snippet framing with the `completion` command group; remove the "Known limitations" block added in R.z's `features.md` pass, now that both defects are closed; **state the fish gap explicitly** so the docs stop over-promising
- [ ] Document the implementation in `tech-spec.md` — the two route mechanisms, post-processing, sentinel machinery, and rc-file safety contract
- [ ] Update `README.md` and `docs/site/user-guide/commands.md` with the new command group; revise the Shell Completion sections in `README.md` and `docs/site/user-guide/install-options.md`
- [ ] Record the macOS system-bash 3.2 limitation accurately: **`complete -o nosort` (bash ≥ 4.4) means nothing registers at all** unless R.d strips it, and `compopt` (bash ≥ 4.0) additionally breaks dir/file completion — the pre-spike wording understated this (R.b Amendment 4)
- [ ] `CHANGELOG.md` entry for `v2.19.0`, dated
- [ ] Bump `project_guide/version.py` and `pyproject.toml` to `2.19.0`
- [ ] Verification per CI-gate parity: `pyve test`, `pyve env run ruff check project_guide/ tests/`, `pyve env run mypy project_guide/`

---

## Subphase R-2: Pyve Detection & Render Gate

A single failed pyve detection at `init` permanently strips the entire Pyve guidance section (~80 lines) from `go.md`, and nothing ever re-detects. Every command exits 0; nothing warns. Documented in `docs/specs/pyve-detection-render-gate.md`.

The omitted content is the guardrail itself — use `pyve test` not `pyve run pytest`, the two-environment isolation rule, don't `pip install -e ".[dev]"` into the main venv. A project in this state hands its LLM a guide that never mentions pyve, so the LLM does the plausible wrong thing. Full plan, decisions, and out-of-scope negotiation: [`phase-r-subphase-2-pyve-detection-plan.md`](phase-r-subphase-2-pyve-detection-plan.md). Ships as one bundled release, **`v2.20.0`** (Story R.o); stories before it run unversioned.

**The load-bearing rule** (from the plan): **automatic detection may only ever set `pyve_installed` to `true`, never to `false`.** Once a project has seen pyve once, no later probe failure can strip the guidance again.

**Refresh sites:** `update` and an explicit `mode <name>` switch — **never `_apply_heal`**, which the pre-invoke auto-hook calls on every command. A pyve subprocess there is the Q.t (v2.15.1) hang class.

---

### Story R.j: Decouple the render gate — persist `pyve_installed` [Planned]

The core fix. Deriving `pyve_installed` from `config.pyve_version is not None` is what turns a *detection miss* into *content loss* — the two answer different questions ("should the guidance render?" vs. "which pyve was seen?") and must stop sharing one field.

- [ ] Add `pyve_installed: bool` to the `Config` dataclass with YAML round-trip
- [ ] Migration default on read: `pyve_version is not None`, so no existing project changes behavior at the moment of upgrade
- [ ] Confirm this is additive-with-default and therefore does **not** bump `SCHEMA_VERSION` (per the config-schema policy in `project-essentials.md`)
- [ ] Replace the derivation at all four render call sites — `init` (`cli.py:272`), `set_mode` (694), `update` (1136), `_apply_heal` (1216) — with `config.pyve_installed`
- [ ] Implement the **sticky-true** helper: a single function through which every automatic update flows, which can set the flag `true` but never `false`
- [ ] Tests: migration default for a legacy config, sticky-true holds across a failed probe, all four render sites read the persisted flag, an explicitly-`false` hand-edited config is respected

### Story R.k: Host-supplied pyve version — `--pyve-version` / `PYVE_VERSION` [Planned]

pyve invokes `project-guide init` and knows its own version with certainty. Accept it and skip the guess. Same shape as `--bin` in Subphase R-1: project-guide owns the rendering decision; the host tool supplies the fact it is uniquely positioned to know.

- [ ] Add `--pyve-version` to `init`, plus the `PYVE_VERSION` env-var equivalent
- [ ] Resolution chain mirrors `--project-name`: CLI flag → env var → `PATH` probe
- [ ] A supplied value wins outright and sets `pyve_installed=true` without probing
- [ ] `init` only — **not** elevated to `update` / `mode`; later changes are handled by re-detection (R.l), not by more flags
- [ ] Document the shared "host-supplied fact" pattern (`--bin`, `--pyve-version`, `--project-name`) so the three read as one idea
- [ ] Tests: flag wins over env, env wins over probe, supplied value skips the subprocess entirely, malformed value handling

### Story R.l: Re-detect on `update` and explicit `mode <name>` [Planned]

`pyve_version` is a cache, so treat it as one. This converts a permanent failure into a transient one.

- [ ] Refresh detection during `update` and during an explicit `mode <name>` switch; write the refreshed value back to `.project-guide.yml`
- [ ] **Do not** refresh in `_apply_heal` — it runs in the pre-invoke auto-hook on every command, including `--help` and `--version`
- [ ] Add a regression test asserting the auto-hook path performs **no** pyve subprocess. This is the Q.t (v2.15.1) hang class and the guard must be explicit, not incidental
- [ ] Inherit the Q.t probe discipline: bounded `timeout`, every exception class caught, failure degrades to "leave the cached value alone"
- [ ] A failed refresh is silent (absence is the steady state for non-pyve projects) and leaves `pyve_installed` untouched per sticky-true
- [ ] Tests: pyve appears after a bad init and the section returns on next `update`; same via `mode`; hook performs no probe; probe timeout does not fail the command

### Story R.m: Warn loudly on a detection miss at `init` [Planned]

A silent `null` is indistinguishable from a deliberate non-pyve project. This converts an invisible failure into a visible one.

- [ ] `init` emits a stderr warning when detection fails: pyve not found, the Pyve guidance will be omitted, and the remedy (`project-guide update` once pyve is available)
- [ ] Material warning per FR-9 — emitted on stderr even under `--quiet`
- [ ] Fires at `init` only (a once-per-project event), **not** on every refresh failure in R.l — the warning must not become startup noise
- [ ] Suppressed when the version was host-supplied (R.k), since no detection was attempted
- [ ] Tests: warning on miss, silence on success, silence when host-supplied, present under `--quiet`

### Story R.n: Store a bare version string with a tolerant reader [Planned]

The field currently holds the whole `pyve --version` line (`"pyve version 2.6.2"`), which is why `_pyve_version_token()` exists to re-parse it at display time.

- [ ] Normalize to a bare `"3.2.2"` on write, from both probe output and host-supplied values
- [ ] Reader keeps accepting the legacy raw-stdout form — existing `.project-guide.yml` files in the wild carry it
- [ ] Retire `_pyve_version_token()` (`cli.py:1281`) or reduce it to the legacy-compatibility path
- [ ] Verify the `status` "Managed by pyve vX.Y.Z" footer still renders correctly from both stored forms
- [ ] Confirm no coordinated pyve change is needed — `pyve_version` is not in the pinned cross-repo field subset (`version`, `installed_version`, `target_dir`, `current_mode`)
- [ ] Tests: bare round-trip, legacy-form read, status footer for both forms

### Story R.o: `v2.20.0` Subphase R-2 bundled release [Planned]

Documentation and the single release tag for the subphase.

- [ ] Update `features.md` FR-13 — the detection contract, the `pyve_installed` gate, sticky-true semantics, and the refresh sites
- [ ] **Amend invariant (b) in `project-essentials.md`** — record `update` / explicit `mode` as a second sanctioned refresh point alongside the existing Q-4 readiness-gate exception, and state that `_apply_heal` remains off-limits with the Q.t rationale
- [ ] Update `tech-spec.md` — reconcile the `Config` dataclass listing with the actual dataclass (it currently omits `project_name` as well as the new `pyve_installed`) and document the sticky-true helper
- [ ] Document the new config field and `--pyve-version` flag in `README.md` and `docs/site/user-guide/configuration.md`
- [ ] Confirm a re-render that newly *adds* the Pyve section is handled cleanly by the existing hash-comparison machinery, with no `.bak` proliferation
- [ ] `CHANGELOG.md` entry for `v2.20.0`, dated
- [ ] Bump `project_guide/version.py` and `pyproject.toml` to `2.20.0`
- [ ] Verification per CI-gate parity: `pyve test`, `pyve env run ruff check project_guide/ tests/`, `pyve env run mypy project_guide/`

---

### Story R.z: Refactor planning docs (artifact-role realignment + spec accuracy) [Planned]

Two problems surfaced while scoping a documentation refactor.

**Artifact roles have blurred.** `project-essentials.md` has accreted full behavioral and implementation contracts that belong in `features.md` (*what the system guarantees*) and `tech-spec.md` (*how it is built*). It is meant to be a map of where the skeletons are buried, not a description of each skeleton. Because its content is injected verbatim into every rendered `go.md`, the cost is paid in every mode: the file is 36,075 bytes — **50% of `go.md`'s 71,468** — and the `git-push` section alone is 10,484 bytes (15% of every `go.md`), describing in algorithmic detail a command the LLM is explicitly forbidden to initiate. Roughly 130 of its 213 lines duplicate content that already has a proper home. Relocate them; keep only the must-know facts and the pointers.

**`features.md` and `tech-spec.md` have drifted from the code.** FR-15 still documents the pre-v2.9.0 `git-push` error model, `features.md` contradicts itself on `go.md` tracking status, and both files carry stale inventories.

Verified against the code, the bundled template tree, and a full test run (636 passed, 91.51% coverage).

**Status — ON HOLD until all Phase R mechanics are settled (2026-08-12).** Deliberately parked at the end of the phase: the subphases ahead of it change the very surfaces this story documents, so refactoring them first would guarantee a second pass. Concretely — Subphase R-1 rewrites FR-7 and adds a `completion` command group to `features.md` / `tech-spec.md`, and R-1's own release story (R.i) removes the "Known limitations" block this story's `features.md` pass added. Run this **last**, once every subphase has landed.

The `features.md` pass is already complete and was presented at its per-document gate; `docs/specs/features_old.md` is the backup and can be deleted once the whole session closes. The `tech-spec.md` pass and the `project-essentials.md` revisit have not started — the relocation targets they were to receive are named in their task lines below. Resume with `project-guide mode refactor_plan`.

Renumbered `R.b` → `R.z` to park it behind the subphases. It is a **phase-level** story, not part of any subphase.

- [x] Refactor `features.md` — receive relocated *what* content (FR-15 branch-logic decision table: the 9 outcomes with exit codes, prompts, defaults, and `--no-input` behavior; `heal`/`update`/`init` division of labor into FR-14); fix the pre-v2.9.0 FR-15 error model; resolve the `go.md` tracked-vs-untracked self-contradiction (L132 / L140 vs FR-14 L395 — `tech-spec.md` L111 is the correct statement); add the missing `init` inputs `--test-first` and `--project-name`; add `developer/python-editable-install.md` and `templates/modes/_phase-letters.md` to the File Structure tree; add the missing `project_name` field to the `.project-guide.yml` schema block; refresh stale version examples; move `FR-7: Shell Completion` back into numeric sequence (it sat after FR-15); record FR-7's known zsh `compinit` / `PATH`-resolution limitations and point at the incoming [`shell-completion-ownership.md`](shell-completion-ownership.md) change request; repair the `phase-q-pyve-toolchain-hosting.md` link (moved to `.archive/`)
- [ ] Refactor `tech-spec.md` — receive relocated *how* content (gitbetter wrapper internals under § External CLI Dependencies: bundled-subject emit grammar, colon rule, whitespace collapse, the permissive-read/strict-emit parser asymmetry, header-filter predicate, committed-prefix→uncommitted-suffix partition, `_presume_committed_on_branch` anchor heuristics; reconcile rather than duplicate for gitignore / IDE-visibility / auto-heal-hook / schema-versioning detail already partly present); fix the entry-point template misnamed `templates/go.md` → `templates/llm_entry_point.md`; update the test inventory 629 → 636 in both places; extend the partials filename convention to cover `_phase-letters.md`
- [ ] Revisit `project-essentials.md` — trim ~213 lines to ~80 by relocating the ~130 duplicated lines above; retain the developer-lane rule, the genuinely non-obvious traps, the Pyve env-spec vendored contract (no other home), and pointers into `features.md` / `tech-spec.md`; verify no fact is lost in transit

`concept.md` needs no changes — its scope list, command inventory, and 17-mode count with the `plan_envs` frozen marker are all current.

No version bump: spec-accuracy correction and doc reorganization with no behavioral change. Rides the next code story's release per Version Cadence.

---

## Future

### Installation/Config Discovery Hierarchy (global vs. project context) [Deferred]

Model after `asdf` with no `.tool-versions`: context-free commands still work; project-scoped commands warn when there's no project. Today `project-guide` resolves its operating context only from a local `.project-guide.yml` in `Path.cwd()`, so commands run outside a project directory have no context and the pre-invoke hook stays silent (e.g., the Q-4 local-install readiness warning can't fire without a local config). Support a discovery hierarchy with a graceful global fallback:

- **Context-free commands** (`--version`, `status`, …) run against the global pyve toolchain-install context when no local `.project-guide.yml` is found — no project home required.
- **Project-scoped commands** (`mode`, …) warn "no project home" (no-op / non-zero exit) when no local `.project-guide.yml` is found, rather than silently doing nothing.

Resolution order: local `.project-guide.yml` first, then the global toolchain-install context. **Cross-repo contract implication:** the install-location-independence contract (Story Q.l, pinned by `tests/test_cross_repo_contract.py`) currently mandates per-project state is *always* resolved from `cwd`, never from the package install location — a global fallback is a coordinated evolution of that contract requiring a paired Pyve story (the global toolchain context is Pyve-owned). Defer until the need is concrete.

### Audit Modes [Deferred]

Future modes: `audit_security`, `audit_architecture`, `audit_performance`, `audit_best_practices`, `audit_modularity`, `audit_patterns`.

### Project Lifecycle Automation [Deferred]

- Release helper / version-bump / tag automation — developer works across multiple git flows and prefers tool-agnostic; no timeline.
- Migration tooling for `docs/guides/` → `docs/project-guide/` — future `refactor` mode; low demand.

### Advanced Project Essentials [Deferred]

- `create_or_modify` action type — revisit if multiple artifacts develop the need; not yet justified.
- Validation/linting of `project-essentials.md` content — freeform by design; template convention is sufficient.
- Auto-detection of stale `project-essentials.md` — git-log based; deferred until there is demand.

### CLI Edge Cases [Deferred]

- `--interactive` flag to force interactive mode over non-TTY stdin — not needed; `stdin` can always be re-attached.
- Legacy broken-state detection for `init` (`.project-guide.yml` absent but target dir populated) — unusual edge case; falls through to existing skip-with-warnings path.

### Integrity & Validation [Deferred]

- `project-guide check` command — dedicated integrity/audit surface with nonzero exit on failure, suitable for CI and pre-commit hooks. Candidate rules: `project_name` in config vs. `cwd.name` vs. `pyproject.toml` `[project] name`; artifact headers (`# stories.md -- <name> (<lang>)`) vs. `config.project_name`/`config.programming_language`; `SCHEMA_VERSION` surfacing; `installed_version` vs. `__version__`; `.archive/stories-vX.Y.Z.md` filenames parse cleanly; metadata override keys reference existing modes; unrendered `{{ var }}` placeholders across written artifacts (broadens the N.s `render_fresh_stories_artifact` guard to every written artifact). `project-guide status` runs a cheap subset and prints a one-line footer (`⚠ N integrity issues — run 'project-guide check' for details`) without changing its exit code. Precedent: `django check`, `brew doctor`, `cargo check`. Defer until there is a concrete second integrity rule worth shipping (N.s covers the first drift source inline with a warning).

### Template & Rendering [Deferred]

- Support for literal `{{ var }}` strings in template output — use `{% raw %}...{% endraw %}` on a case-by-case basis; bridge with a general solution only if the pattern becomes common.

### mypy `tests.*` unused-override cleanup [Deferred]

`mypy project_guide/` emits `note: unused section(s): module = ['tests.*']` on every run — the `[[tool.mypy.overrides]]` block targeting `tests.*` in `pyproject.toml` matches nothing, because the checked target is `project_guide/` only (tests are never passed to mypy). Harmless (a note, not an error — exit stays 0 on success) but it's noise on every type-check, and a dead config stanza invites confusion about whether tests are meant to be type-checked. Resolve by deciding intent, then either: (a) **remove** the dead `tests.*` override from `pyproject.toml` (if tests are intentionally out of mypy's scope), or (b) **bring `tests/` into the mypy target** (CI step + local convention) if the override implies test type-checking was once intended. Surfaced 2026-06-11 during the Q.u mypy CI fix. Low priority — cosmetic until someone wants test type-checking.
