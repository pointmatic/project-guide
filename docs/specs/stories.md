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

### Story R.c: `completion` command group scaffold + `show` [Done]

The read-only slice: everything needed to *produce* a correct script, with no filesystem writes. Establishes the group, shell detection, and the post-processing proven in R.b.

- [x] Add the `completion` Click group with `--shell auto|zsh|bash` resolution (`auto` reads `$SHELL`, falling back to an explicit error rather than a guess) — `resolve_shell` in the new `project_guide/completion.py`
- [x] Implement script generation via Click's `_PROJECT_GUIDE_COMPLETE=<shell>_source` protocol — `generate_script` calls the protocol's `ShellComplete` class in-process (same template, no subprocess). The supported set is project-guide's, not Click's: fish is refused because the group cannot yet *install* what it would generate
- [x] Apply the R.b post-processing so the emitted script does not depend on `PATH` — one generator for both shells (R.b Amendment 1); each substitution must match **exactly once** or hard-error naming the failed pattern (no Click version guard, per the R.b stability finding) — `postprocess_script`; the callback is checked first so an unrecognizable script fails on the pattern both shells share
- [x] Implement `--bin` resolution: explicit flag → project-guide's own resolved absolute path → bare-name `PATH` fallback. Post-process **only** when the result is absolute; on the bare-name fallback emit Click's script verbatim (R.b Amendment 3 — the baked guard is a filesystem test) — `resolve_bin`; symlinks deliberately unresolved (the shim is the stable handle), and argv[0] is used only when it *is* the console script, so `python -m project_guide` falls through to the `PATH` lookup
- [x] `completion show` prints the post-processed script to stdout; no writes, no prompts
- [x] Tests: per-shell generation, `--bin` resolution order, `--shell auto` detection, unsupported-shell error — 48 new tests in `tests/test_completion.py` (684 passed total)
- [x] Verify `--quiet` / `--no-input` interaction is coherent for a stdout-producing command — **took neither flag** (`--quiet` would make the command a no-op; `--no-input` would imply a prompt that does not exist), and closed two stdout leaks the verification surfaced: the auto-heal hook's `Update?` confirm and the legacy-config `Migrated` notice both wrote to **stdout** ahead of every subcommand, so `eval "$(project-guide completion show)"` would have evaluated them as shell code. Both moved to stderr, matching the rest of the hook

End-to-end verified with the shipped code, binary off `PATH`: bash rc-eval yields 13 completions, zsh fpath autoload yields the full list under a real interactive shell.

No version bump — Subphase R-1 ships bundled as `v2.19.0` at R.i, which owns the CHANGELOG entry.

### Story R.d: `completion install` / `uninstall` — bash rc-block route [Done]

The rc-block writer and its sentinel machinery. This is the first project-guide code that writes **outside the project directory**, so the safety contract is the story.

- [x] Write a sentinel-bracketed block to the resolved rc file (`--rc` override; default `~/.bashrc`) — `SENTINEL_START` / `SENTINEL_END` (conda-style pair, the shape pyve's legacy block already uses) plus `build_block`, which stamps the generating version so an old block is identifiable on sight
- [x] Idempotent: re-running with an already-current block is a no-op — no write, no backup, reported as `RcOutcome.UNCHANGED`. An existing block is refreshed **where it sits** rather than moved to the tail, so a user who repositioned it keeps their layout
- [x] `uninstall` removes the block **byte-clean**, so `install` → `uninstall` round-trips the rc file exactly — including the blank separator line `install` inserted, which is reclaimed only when it is genuinely adjacent slack (block at EOF, or a second blank line follows), never a blank line structuring the user's own content
- [x] Ours-vs-foreign predicate: only project-guide's own sentinel is touched; foreign content under a similar header is left alone with a stderr warning (mirrors `_ensure_gitignore_entry()`) — `_foreign_warnings`; pyve's legacy block is reported and survives both `install` and `uninstall` untouched. Ours is installed **alongside** it, which is the duplicate-registration state R.g exists to resolve
- [x] Back up the rc file before first modification — `.bak.<timestamp>` beside the rc file, on every content-changing write (install *and* uninstall), skipped on the no-op path
- [x] Degrade silently at shell startup — a broken or stale block must never print. Also silent **at completion time**: the R.b Amendment 2 `[[ -x <bin> ]]` guard, or bash prints `env: …: No such file or directory` on every TAB against a stale `--bin` — nothing is *executed* at startup at all: the script is written **inline** rather than as an `eval "$(…)"`, so a stale install cannot print and no Python subprocess runs per shell start
- [x] Decide whether to strip `complete -o nosort` (bash ≥ 4.4) so completion registers at all on macOS system bash 3.2 — R.b Amendment 4; verified that stripping restores registration, at the cost of Click's unsorted ordering — **decided: neither strip nor keep, but fall back at runtime.** `apply_bash_compat` rewrites the line to `complete -o nosort -F … 2>/dev/null || complete -F …`, so bash ≥ 4.4 keeps Click's ordering and 3.2 swallows the error and registers via the fallback. Applied independently of `--bin` (the defect is in Click's template, not the callback's binary resolution)
- [x] Tests: fresh install, idempotent re-install, round-trip byte-equality, foreign-block refusal, missing rc file — 32 new tests in `tests/test_completion.py` (716 passed total), including two that source the installed block in a **real bash** to pin registration (3.2 and 5.x alike) and silence against a dead `--bin`

**Two implementation decisions worth flagging.** (1) The plan's "rc-block eval" is implemented as the script's **bytes inline** in the sentinel block, not `eval "$(project-guide completion show)"` — same rc-time evaluation, but no Python subprocess on every interactive shell start and nothing that can print when the install goes stale. (2) `install --shell zsh` **refuses** rather than writing the bash-shaped block into `~/.zshrc`; the zsh route needs its own fpath artifact and `compinit` bootstrap (R.e).

Verified end-to-end with the shipped code, binary off `PATH`: **13 completions on bash 3.2.57 and 5.3.15** — the first time completion has registered at all on stock macOS bash. Byte-clean round-trip and stale-install silence confirmed against a real rc file.

No version bump — Subphase R-1 ships bundled as `v2.19.0` at R.i, which owns the CHANGELOG entry.

### Story R.e: `completion install` / `uninstall` — zsh fpath route [Done]

The asymmetric half. zsh gets the autoload file its `#compdef` header is designed for, which means two on-disk artifacts instead of one.

- [x] Write the post-processed script to a zsh autoload directory as `_project-guide` — `install_autoload_file`; the directory defaults to `$XDG_DATA_HOME/project-guide/zsh-completions` (`~/.local/share/…` fallback), overridable with a new `--dir`. A project-guide-owned directory was chosen over a shared one like `/usr/local/share/zsh/site-functions` precisely so `uninstall` can remove it without wondering whose files it is deleting. No backup for this artifact — unlike the rc file, it is entirely our own regenerable output
- [x] Add the `fpath` line plus the `compinit` bootstrap to the rc file, sentinel-bracketed — `build_zsh_bootstrap`, carried by R.d's existing block machinery unchanged
- [x] Bootstrap shape: `(( $+functions[compdef] )) || { autoload -Uz compinit && compinit -i; } 2>/dev/null` — leave an existing `compinit` alone — **the planned shape proved insufficient; see the amendment below.** Shipped shape guards on the autoload file being readable, then branches: `compdef` exists → `autoload -Uz _project-guide && compdef _project-guide project-guide`; otherwise → `autoload -Uz compinit && compinit -i`. The `2>/dev/null` silence and the leave-an-existing-`compinit`-alone intent are both preserved
- [x] `uninstall` removes **both** the autoload file and the rc block — `remove_autoload_file`; the default (project-guide-owned) directory is `rmdir`'d when emptying it leaves nothing behind, while a user-supplied `--dir` is always left in place
- [x] Idempotency and byte-clean round-trip hold across both artifacts — "already current" requires *both* to be unchanged, so a deleted autoload file with an intact rc block still reports a refresh rather than a spurious no-op
- [x] Tests: fresh install, re-install, round-trip, partial state (file present but rc line absent, and the reverse) — 21 new tests (737 passed total), including three that source the generated block in a **real zsh** and assert on `$_comps`, the table `compinit` actually consults

**Amendment — the planned bootstrap misses the common case.** The plan's two-liner handles only "`compinit` never ran" (field defect 1). It does not handle "`compinit` already ran," which is what happens for most users, because the block lands at the *end* of `~/.zshrc` — after oh-my-zsh or a hand-rolled `compinit`. An `fpath` entry added at that point is never scanned. Verified directly rather than reasoned about: with `fpath` extended *before* `compinit`, `_comps[project-guide]` is `_project-guide`; extended *after*, it is unset. Hence the explicit-registration branch. A third requirement fell out of the same investigation: registering a `compdef` against a deleted autoload file defers its failure to TAB time, so the whole block is wrapped in `[[ -r <file> ]]` and a half-uninstalled state is inert rather than noisy.

**Also in this story:** `--dir` is refused for bash (it names an fpath directory bash's single-block route has no use for) — silently ignoring it would let a user believe they had placed the script somewhere. R.d's `install --shell zsh` refusal is gone.

Verified end-to-end with the shipped code, binary off `PATH`: a real interactive zsh (scrubbed environment, `env -i`) reports `_comps[project-guide] = _project-guide`; the autoload file loads cleanly under `autoload -Uz +X`; the baked callback returns 13 candidates. Idempotent re-install, partial-state repair, byte-clean rc round-trip and autoload-file removal all confirmed against real files.

No version bump — Subphase R-1 ships bundled as `v2.19.0` at R.i, which owns the CHANGELOG entry.

### Story R.f: `completion status` [Done]

Makes failure inspectable — the surface whose absence let both field defects hide.

- [x] Report per shell: **absent** / **installed** / **stale** — `inspect_shell` returns a `ShellStatus`; **both** shells are reported unless `--shell` narrows it, deliberately: the field defect was a user whose zsh worked and whose bash did not, which a current-shell-only report would hide
- [x] **Stale** = a baked `--bin` path that no longer resolves — the pyve-toolchain-bump case — tested with `os.access(path, os.X_OK)`, the *same* predicate the installed script bakes in, so `status` and the shell cannot disagree. A file that exists but lost its executable bit reads as stale here exactly as it fails at TAB time; an `exists()` check would have diverged
- [x] Detect partial installs (zsh file without rc line, or the reverse) and report them distinctly — a distinct `partial` state naming which half is missing and what that means ("the autoload file is missing, so the rc block does nothing")
- [x] Exit-code semantics consistent with the existing CLI conventions — **0** everything absent or current, **1** any shell stale/partial/damaged, **2** I/O error. Absent is deliberately **0**: an uninstalled convenience is not drift, the same rule R.h inherits for `heal`'s silence
- [x] Tests: each state per shell, including partial and stale — 22 new tests (759 passed total)

**Two states beyond the checklist, both found by running the surface rather than by reading it.** (1) A **`damaged`** state for a sentinel block that cannot be parsed: `_read_block_body` degrades to reporting instead of raising, because a reporting surface that crashes on the damage it exists to report is useless. Its remedy line is *suppressed* — `install` refuses to guess where an unterminated block ends and fails with the identical error, so suggesting it would send the user in a circle (`reinstall_fixes_it`, pinned by a test that asserts the suggestion would in fact have failed). (2) A **note when a foreign block is present** — pyve's legacy wiring shows up as `absent` + a note, which is honest (project-guide's own wiring *is* absent) and is the state R.g resolves.

Also handled: a bare-name install bakes no guard at all, so the dead-path test cannot apply — reported as `installed` with a note that the callback resolves through `PATH`, never as stale. And for zsh the autoload directory is read out of the installed `fpath` line rather than assumed from the default, since the shell obeys the rc file and a report about a directory nothing consults would be worse than no report.

**Known gap, deliberately not closed here.** Staleness is the dead-path test only. A block generated by an older project-guide whose template has since changed is *not* detected, even though the version stamp R.d put in the block would make it detectable. Widening the definition would change what R.h's `heal` warning fires on, so it stays out of this story's scope; flagged for R.h/R.i.

Refactor pass tightened two output defects the first green revealed: the `stale` detail no longer repeats the path already shown as `binary:`, and the foreign-block notice is phrased neutrally for a read-only report rather than reusing `install`'s "leaving it untouched" wording (`_foreign_block_headers` now returns bare headers, framed by each caller).

No version bump — Subphase R-1 ships bundled as `v2.19.0` at R.i, which owns the CHANGELOG entry.

### Story R.g: Legacy pyve sentinel adoption [Done]

Users already carry pyve's block. Without this, `install` produces a second block registering the same completion.

- [x] Detect pyve's exact legacy sentinel pair (`# >>> project-guide completion (added by pyve) >>>` … `# <<< project-guide completion <<<`) — `_find_pyve_block_span`, keyed on the **header**: pyve's terminator is byte-identical to ours, so a search anchored on the closing sentinel could not tell the two blocks apart
- [x] Replace it with project-guide's own block and report the replacement in one line — `RcResult.adopted_legacy` drives `Replaced pyve's completion block (it registered the same completion)`. Replacement happens **at pyve's position**, which is a correctness requirement rather than a nicety (see below)
- [x] Belt-and-braces with pyve's own upgrade-path cleanup — the two tools upgrade independently, so neither may assume the other ran — adoption is unconditional on every `install`, so it fires whether or not pyve has cleaned up, and re-fires if pyve re-adds its block later. Recognition spans pyve *generations*: both the current `_pyve_pg_bin` form (bash and zsh variants) and the older `command -v project-guide && eval …` form
- [x] Tests: legacy block present alone, legacy + project-guide block both present, legacy block hand-modified — 14 new tests (771 passed total)

**Why replacement must happen in place.** pyve does not append its block — `add_project_guide_completion` calls `insert_text_before_sdkman_marker_or_append`, deliberately placing the block *above* SDKMan's "must be at the end of the file" marker. Removing pyve's block and appending ours at the tail would move project-guide's wiring past that marker. Verified against a realistic rc file carrying the real pyve block plus an SDKMan footer: the adopted block lands exactly where pyve's was, SDKMan stays last, and completion still returns 13 candidates in a real bash with the binary off `PATH`.

**The adoption boundary, kept explicit.** R.d's rule was "only project-guide's own sentinel is touched." R.g is the single sanctioned exception, and it is bounded twice over: by pyve's exact header, *and* by `_is_pyve_generated`, which requires every body line to be plausibly pyve's output. A block someone has since edited is foreign again — left untouched with the usual warning, ours installed alongside. That boundary is stated in the code next to the token list so it does not erode later.

**Two consequences worth noting.** (1) When both blocks are present, ours is refreshed in place and pyve's duplicate is deleted — and the result is never reported as `UNCHANGED`, because removing the duplicate is a write even when our own block is byte-identical. (2) Two R.d tests were retargeted: they asserted "a foreign block is left untouched" using pyve's genuine block, which is now correctly *adopted*. Their intent is intact, exercised against hand-rolled wiring that is nobody's generated output.

Refactor pass extracted `_drop_separator_blank`, now shared by `remove_block` and the duplicate-deletion path rather than duplicated.

No version bump — Subphase R-1 ships bundled as `v2.19.0` at R.i, which owns the CHANGELOG entry.

### Story R.h: `heal` stale-completion warning [Done]

Follows the established warn-don't-auto-fix pattern (tracked-`go.md`, local-install-under-pyve). Catches the pyve toolchain-version bump that rots a baked path.

- [x] `heal` warns on stderr when completion is installed but **stale** — `_warn_if_completion_stale` in `cli.py`, consuming R.f's `inspect_shell`. Warns on **partial** too: a half-installed zsh pair is just as silently broken, and surfacing that is the same job. Silent on **damaged** — only a human can repair an unparseable block, and `install` fails with the same parse error, so there would be nothing actionable to say
- [x] Warning names the dead path and gives the copyable remedy (`project-guide completion install`) — per shell, so a user whose zsh works and whose bash does not sees exactly which one to fix
- [x] **Never auto-repairs** — writing to a user's rc file without being asked is out of bounds, same constraint that bounds the `git-push` wrapper — pinned by a test asserting the rc file is byte-identical afterward *and* that no `.bak.*` was written
- [x] Silent when completion is absent (an uninstalled convenience is not drift) and when current
- [x] Preserves the auto-hook's steady-state silence — pinned by a test asserting `--version` emits **empty stderr** with completion installed and healthy
- [x] Tests: stale warns, current silent, absent silent, `--no-input` unaffected — 12 new tests in `tests/test_cli.py` (783 passed total)

**Fires from the hook, not from `heal`.** The warning is registered in `_run_pre_invoke_hook` only. That is what makes it catch a toolchain bump without the user thinking to run `heal` — matching the Subphase Q-4 split, where the local-install *warning* fires from both surfaces and only the interactive *offer* is `heal`-scoped. There is no offer here; this is warn-only, so one call site gives complete coverage (the hook runs ahead of every subcommand, `heal` included).

**Observed while wiring it up — pre-existing, not fixed here.** The two older warnings *are* registered at both call sites, so `project-guide heal` prints each of them **twice** (verified: the tracked-`go.md` warning appears 2× in a real run). This story does not propagate that — a test pins the completion warning at exactly one occurrence during `heal` — but the sibling duplication is untouched, since fixing it means editing behavior outside this story's scope. **Recommend a small follow-up story** to de-duplicate `_warn_if_go_md_tracked` and `_warn_if_local_install_under_pyve` the same way.

**`--no-input` is silent**, matching both siblings rather than the non-suppressible auto-heal notice. Completion is an interactive-shell convenience; a CI run has no shell to repair, so the warning would be pure log noise. The story's "`--no-input` unaffected" is satisfied in the stronger sense: no new prompts, no change to auto-yes semantics, and no new CI output.

**Inherited gap, still open.** Staleness remains R.f's dead-path test only, so a block generated by an older project-guide with a since-changed template does not warn. Flagged in R.f, flagged again here as the last story where it would naturally land before R.i documents the behavior.

No version bump — Subphase R-1 ships bundled as `v2.19.0` at R.i, which owns the CHANGELOG entry.

### Story R.h.1: De-duplicate the pre-invoke warnings [Done]

Surfaced by R.h. `_warn_if_go_md_tracked` and `_warn_if_local_install_under_pyve` are each registered at **two** call sites — the pre-invoke hook *and* the `heal` command — so `project-guide heal` prints both warnings **twice**. Verified in a real run: the tracked-`go.md` warning appears 2×. R.h avoided propagating the pattern (its warning fires from the hook only, pinned by a test), leaving these two as the remaining offenders.

The hook's coverage is already complete for both. Every path where `heal` reaches its warning calls is one where `.project-guide.yml` existed and `Config.load` succeeded — exactly the condition under which the hook ran its own warnings a moment earlier. The recursion-guard and `should_skip_input` gates are checked inside each warning, so they behave identically at either site.

**The two warnings are not symmetric, and that is the whole design problem:**

- `_warn_if_go_md_tracked` is a **pure duplicate** — drop `heal`'s call, exactly as R.h did.
- `_warn_if_local_install_under_pyve` is **not**: `heal` passes `offer_provision=True`, and the interactive provisioning offer is deliberately `heal`-scoped (a Subphase Q-4 invariant — the auto-hook warns but never prompts). Deleting `heal`'s call would delete the offer with it. What must be suppressed is the *warning body* on the second call, not the call.

- [x] Remove `heal`'s `_warn_if_go_md_tracked` call; the hook already covers it
- [x] Make the local-install warning body emit once per process while `heal` keeps its provisioning offer — either a once-per-process emit guard (a module-level set, which generalizes to any future warning) or an explicit "offer only, already warned" parameter. Prefer whichever keeps the Q-4 invariant legible in the code — **chose the parameter** (`already_warned`). The function already takes `offer_provision`, so the two flags sit together and read as one statement about who warns and who prompts; a module-level guard would have added process-global mutable state to buy generality for warnings that do not exist yet
- [x] If a once-per-process guard is chosen, add a test fixture that resets it, and make sure the reset is automatic rather than something each test must remember — **not applicable**: the parameter approach carries no cross-invocation state, which was a large part of why it won
- [x] Preserve every existing gate unchanged: recursion guard, `should_skip_input`, and the Q-4 rule that `pip uninstall` advice is emitted **only** on `pyve self provision --status` exit 0 — untouched; `already_warned` gates *printing*, never *deciding*, so no branch condition moved
- [x] Tests: each warning appears exactly once during `heal`; each still appears from the hook on a non-`heal` subcommand; the provisioning offer still appears under `heal`; steady-state silence preserved — 7 new tests in `tests/test_cli.py` (790 passed total), including one asserting the hook alone still never prompts

**Both exit branches needed the suppression, not just one.** The readiness-first branch is the one carrying the offer, so it was the obvious case — but the exit-0 branch duplicated too, and that is the branch carrying the destructive `pip uninstall` advice. Printing removal advice twice is the worse of the two defects. It takes an early return rather than a skipped `secho`, since that branch has no offer to fall through to.

**`heal` now calls one warning instead of three.** `_warn_if_go_md_tracked` and `_warn_if_completion_stale` are not called from `heal` at all; `_warn_if_local_install_under_pyve` is called solely for its heal-scoped offer. The comment at the call site states the invariant that makes this safe — the hook fires ahead of every subcommand and reaches its warnings under exactly the conditions `heal` does (config present and loadable) — so a future maintainer adding a fourth warning knows not to re-register it here.

Verified in a real run, not just under the test runner: `project-guide heal` with `go.md` tracked prints the warning **once** (it printed twice before this story), and `project-guide status` still prints it once from the hook.

**Scope note.** This is `heal`-warning hygiene rather than shell completion, so it sits slightly outside Subphase R-1's theme. It is placed here because R.h discovered it and it is small enough to ride the same release; move it out of the subphase if you would rather keep R-1 thematically pure.

No version bump — Subphase R-1 ships bundled as `v2.19.0` at R.i, which owns the CHANGELOG entry.

### Story R.i: `v2.19.0` Subphase R-1 bundled release [Planned]

Documentation and the single release tag for the subphase.

- [ ] Rewrite `features.md` FR-7 — replace the hand-copied-snippet framing with the `completion` command group; remove the "Known limitations" block added in R.z's `features.md` pass, now that both defects are closed; **state the fish gap explicitly** so the docs stop over-promising
- [ ] Document the implementation in `tech-spec.md` — the two route mechanisms, post-processing, sentinel machinery, and rc-file safety contract
- [ ] Update `README.md` and `docs/site/user-guide/commands.md` with the new command group; revise the Shell Completion sections in `README.md` and `docs/site/user-guide/install-options.md`
- [ ] Record the macOS system-bash 3.2 limitation accurately — **narrowed by R.d**: the registration half is *closed* (the emitted `complete -o nosort … 2>/dev/null || complete …` fallback registers on 3.2), so what remains is only `compopt` (bash ≥ 4.0) breaking **dir/file** completions there. Document the residual limitation, not the pre-spike "nothing works" wording and not R.b Amendment 4's "nothing registers at all," which R.d superseded
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
