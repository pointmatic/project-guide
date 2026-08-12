# Subphase R-1 Plan — project-guide owns its shell completion

**Phase:** R — Quality of Life Improvements and Bug Fixes
**Subphase:** R-1 — Shell Completion Fixes
**Change request:** [`shell-completion-ownership.md`](shell-completion-ownership.md) (incoming from the pyve repo)
**Planned:** 2026-08-12 via `plan_production_phase`
**Anticipated version bump target:** **`v2.19.0`** (minor — purely additive)

---

## Production-readiness waiver

The Step 2 checklist scored **6 of 8**:

| Item | Status |
|---|---|
| Mandatory CI (3 OS × 3 Python, mypy gate) | ✓ |
| `SECURITY.md` | ✓ |
| `CONTRIBUTING.md` | ✓ |
| `.github/dependabot.yml` | ✓ |
| Trusted publisher (`id-token: write`, no long-lived token) | ✓ |
| Bundled-release cadence understood | ✓ |
| Branch protection on main | ✗ waived |
| PR-based workflow | ✗ waived |

The two unmet items are **deliberately waived** for a sole-maintainer repo: `project-essentials.md` § Commit workflow documents "direct commits to main — no branches, no PRs" as a standing convention, and CI runs on every push to main, so the merge-gate value is partly captured already. Revisit if contributors join.

---

## Gap analysis

| What exists | What's needed |
|---|---|
| Click generates completion scripts on demand via `_PROJECT_GUIDE_COMPLETE=<shell>_source` | A `completion` command group that installs, removes, shows, and reports that wiring |
| FR-7 documents hand-copied snippets for bash / zsh / fish | project-guide installs its own completion; the snippets stop being the interface |
| pyve hand-writes a sentinel block into the user's rc file (`add_project_guide_completion` in `lib/utils.sh`) | pyve retires its block and shells out to `project-guide completion install --bin …` |
| Completion breaks silently in two known ways | Both closed, with a `status` surface so failure is inspectable rather than invisible |
| No command writes outside the project directory | A bounded, reversible, idempotent writer for `~/.zshrc` / `~/.bashrc` and a zsh autoload directory |

### The two field defects

Reported in [pyve#70](https://github.com/pointmatic/pyve/issues/70) — *"typing `project-guide <TAB>` offers nothing, and no error is printed."* Defect 1 masks defect 2, so neither surfaced.

1. **`compdef` precondition (zsh only).** Click's `zsh_source` output ends in `compdef`, which does not exist until `compinit` has run. On a shell whose startup files never run `compinit`, the eval dies with `command not found: compdef`.
2. **`PATH`-based binary resolution (all shells).** pyve hosts project-guide in a private toolchain venv behind a `~/.local/bin` shim, and that directory is not always on `PATH`. The `command -v project-guide` guard was simply false.

---

## Technical findings that change the design

These came out of inspecting the **actual** generated scripts, not the change request's description of them. Both alter the shape of the work.

### Finding 1 — `--bin` alone does not close defect 2

The change request asserts that *"`--bin` is the whole of the interface"* between pyve and project-guide. That is **incomplete**. Every generated callback embeds the **bare command name** and resolves it through `PATH` *at completion time*, long after the rc block ran:

```bash
# bash: $1 is the command word, resolved via PATH
response=$(env COMP_WORDS=... _PROJECT_GUIDE_COMPLETE=bash_complete $1)
```
```zsh
# zsh: hard PATH guard, then a bare command name
(( ! $+commands[project-guide] )) && return 1
response=(... $(env COMP_WORDS=... _PROJECT_GUIDE_COMPLETE=zsh_complete project-guide))
```

Baking an absolute path into the rc block fixes only the **generation** call at shell startup. With the binary off `PATH`, zsh's `$+commands` guard returns empty before it even tries, and bash's `$1` lookup fails the same way.

**Consequence:** project-guide must **post-process** Click's generated script — substitute the absolute path and neutralize the `$+commands` guard — rather than emit it verbatim. This is unproven and is the primary justification for the integration spike below.

### Finding 2 — the autoload route is not symmetric across shells

Only the **zsh** script carries a `#compdef project-guide` header and an explicit `loadautofunc` branch. The bash script has neither; it self-registers by calling `complete -o nosort -F …` at the end and is designed to be sourced.

| | zsh | bash |
|---|---|---|
| Autoload-file route | ✅ built in (`#compdef` + `loadautofunc`) | ❌ would require the `bash-completion` package's loader dir — standard on Linux, absent on stock macOS |
| rc-eval route | ✅ but needs the `compinit` bootstrap | ✅ always works; `complete` is a builtin with no preconditions |

**Consequence:** bash is rc-block eval regardless. Only zsh has a real choice.

### Finding 3 — defect 1 is zsh-only

bash needs no `compinit` equivalent. `complete` is always available in an interactive bash, so the bootstrap is zsh-specific code, not shared machinery.

---

## Decisions taken at planning time

| Decision | Choice | Rationale |
|---|---|---|
| **zsh route** | **fpath autoload file** + an `fpath` line in the rc file | Uses the route the generated script is explicitly built for; removes a subprocess from every shell start and sidesteps `compdef` ordering entirely |
| **bash route** | rc-block eval | The only route available (Finding 2) |
| **Shell scope** | zsh + bash | Both field defects live here; fish is a third mechanism and is deferred |
| **`heal` integration** | Warn on **stale** wiring | Follows the established warn-don't-auto-fix pattern (tracked-`go.md`, local-install). Catches pyve toolchain-version bumps that rot a baked path |
| **Legacy pyve block** | Detect, **replace**, and report in one line | Belt-and-braces with pyve's own cleanup; the user must never end up with two blocks registering the same completion |

The fpath choice means `install` / `uninstall` / `status` each handle **two on-disk shapes** — an autoload file plus an rc line for zsh, a sentinel block for bash. That asymmetry is accepted deliberately; it is the cost of the better zsh behavior.

---

## Spike result (Story R.b) — 2026-08-12

**Outcome: post-processing is viable. Finding 1 is closed; the planned decisions stand and R.c–R.i proceed as written**, with the four amendments recorded below.

Environment: zsh 5.9, bash 3.2.57 (macOS system) and bash 5.x (Homebrew), Click 8.3.2, project-guide 2.18.1. Reproduction used an off-`PATH` shim invoked through a scrubbed `env -i PATH=/usr/bin:/bin` environment; zsh was driven end-to-end through `zsh/zpty` (a real interactive shell receiving a literal TAB), bash by calling the registered function the way `complete -F` does (`$1` = the command word as typed).

### Failure reproduced, then closed

| Case | zsh (fpath autoload) | bash (rc eval) |
|---|---|---|
| Click script verbatim, binary **on** `PATH` | 12 completions | 12 completions |
| Click script verbatim, binary **off** `PATH` | **nothing, silently** | **nothing** + `env: project-guide: No such file or directory` |
| **Post-processed**, binary off `PATH` | **12 completions** | **12 completions** |

### The transformation

Two targeted line rewrites per shell — not a rewrite of the script, and never a blanket substitution of the command name (`#compdef project-guide` and `compdef … project-guide` must keep the *typed* name):

- **zsh** — replace the `PATH` guard `(( ! $+commands[project-guide] )) && return 1` with `[[ -x <bin> ]] || return 1`, and substitute `<bin>` for the bare command name in the `_PROJECT_GUIDE_COMPLETE=zsh_complete …` callback.
- **bash** — substitute `<bin>` for `$1` in the `_PROJECT_GUIDE_COMPLETE=bash_complete …` callback, and **insert** an `[[ -x <bin> ]] || return 1` guard above it (see Amendment 2).

`<bin>` is shell-quoted; a `--bin` path containing spaces was verified end-to-end in both shells.

**Rejected:** prepending the binary's directory to `PATH` inside the script (mutates the user's environment as a side effect of pressing TAB), and wrapping the callback in `command -v`-style discovery (re-introduces the `PATH` dependency the story exists to remove).

### Amendment 1 — the transformation is route-independent

Post-processing does **not** differ between the zsh fpath route and the bash rc route, and not between zsh's two routes either: Click's `zsh_eval_context[-1] == loadautofunc` branch at the tail of the script already picks the right registration path. The same post-processed zsh script was verified working both as an fpath autoload file and sourced from an rc file. **Consequence:** one generator; the routes differ only in *where the bytes land*, which is exactly the R.d / R.e split.

### Amendment 2 — bash needs a guard it doesn't ship with

zsh's `$+commands` guard is what makes a broken install silent; bash has no equivalent, so with a stale `--bin` the `env` call prints `No such file or directory` **on every TAB press**. That violates the plan's mandatory silent-degradation rule. The `[[ -x <bin> ]] || return 1` insertion above the callback closes it — verified silent on bash 3.2 and 5.x with a dead path. This is post-processing project-guide *adds*, not merely a substitution.

### Amendment 3 — `--bin` must be an absolute path, or post-processing is skipped

The baked guard is `[[ -x <bin> ]]`, which is a *filesystem* test. A bare-name fallback would make it test a file relative to `$PWD`. **Rule for R.c:** post-process only when `--bin` resolves to an absolute path; when it degrades to the bare-name `PATH` fallback, emit Click's script verbatim (the historical behavior). This refines, rather than breaks, the `--bin` contract with pyve — pyve passes its absolute `~/.local/bin/project-guide` shim, so the pyve path is always the post-processed one.

### Amendment 4 — macOS bash 3.2 is worse than "no dir/file completion"

Click's script ends in `complete -o nosort -F …`. `-o nosort` is bash ≥ 4.4; on stock macOS bash 3.2 the whole line fails with `complete: nosort: invalid option name` and **nothing registers at all** — `complete -p project-guide` reports "no completion specification". The `compopt` limitation already recorded in *Out of scope* is therefore not the whole story, and the R.i known-limitations note should say so. Stripping `-o nosort` was verified to restore registration on 3.2 (the only loss is Click's unsorted ordering). Whether to strip it — conditionally or always — is a **decision left to R.d**; the spike only establishes that the option is available and that the current wording understates the defect.

### Click output stability — no version guard needed

The generated scripts are **byte-identical across Click 8.1.8, 8.2.0, 8.2.1, 8.3.0, 8.3.2, 8.4.0** and differ from **8.4.2** only by a trailing blank line. The post-processor's patterns matched cleanly on every one, spanning both sides of the project's `click>=8.2` floor and the currently-unreleased-at-planning-time 8.4.x line.

**Consequence:** pin nothing. Instead, assert structurally — each substitution must match **exactly once**, and a miss is a hard error naming the failed pattern rather than a silently-unmodified script. That converts a future Click template change into a loud, testable failure at generation time, which is strictly better than a version ceiling that would have to be raised on every Click release.

### Follow-on: what R.f's "stale" check means, concretely

Stale = the baked `<bin>` no longer passes `[[ -x ]]`. That is the same predicate the installed script itself uses, so `status` and the script agree by construction. Both shells degrade silently in that state (bash only once Amendment 2 lands), which is precisely why the failure was invisible in the field and why R.f exists.

Prototype code was discarded per the spike contract.

---

## Feature requirements

```
project-guide completion install   [--shell auto|zsh|bash] [--bin <path>] [--rc <path>]
project-guide completion uninstall [--shell auto|zsh|bash] [--rc <path>]
project-guide completion show      [--shell auto|zsh|bash]
project-guide completion status
```

- **`install`** — idempotent; a no-op when project-guide's own sentinel/file is already current. Writes an absolute binary path (see `--bin`). zsh additionally gets the `compinit` bootstrap. Degrades silently: a broken or missing install must never emit noise at shell startup.
- **`uninstall`** — byte-clean, so `install` → `uninstall` round-trips the rc file exactly. For zsh this removes both the autoload file and the `fpath` line.
- **`show`** — print the post-processed script to stdout; no filesystem writes.
- **`status`** — report per shell: absent / installed / **stale** (a baked `--bin` path that no longer resolves).
- **`--bin`** — lets a host tool supply the stable handle. pyve passes `~/.local/bin/project-guide` (its shim), **not** the version-keyed `~/.local/share/pyve/toolchain/<PYTHON_VERSION>/venv/bin/project-guide`, which rots on every pyve Python bump. Resolution when absent: project-guide's own resolved absolute path, then a bare-name `PATH` fallback.

---

## Production concerns

- **First write outside the project.** Every existing command confines itself to the project directory and `.project-guide.yml`. This subphase writes to `~/.zshrc` / `~/.bashrc` and a zsh autoload directory. Sentinel bracketing, idempotency, and a byte-clean round-trip are the safety contract; a backup before first modification should be considered.
- **Silent degradation is mandatory.** Completion is a convenience. A broken install must never print at shell startup — that would be a worse regression than the missing completion it replaces.
- **Never edit a foreign block.** Only project-guide's own sentinel and pyve's exact known legacy sentinel are touched. Anything else is left alone with a warning — mirroring `_ensure_gitignore_entry()`'s ours-vs-foreign predicate.
- **Cross-repo release coupling.** pyve pins `project-guide >= 2.19.0` once this ships. That is a one-way pin; project-guide needs nothing new from pyve.

---

## Anticipated breaking changes

**None.** Purely additive — a new command group; no existing command, flag, output format, or config field changes. Consumers on older versions are unaffected.

Per Step 5 negotiation: no item is substantively *or* trivially breaking, so the target is a **minor** bump — **`v2.19.0`**.

**Multi-release note.** Phase R has already shipped `v2.18.1` (Story R.a, before this subphase existed), so the phase carries more than one release tag. This is the documented multi-release exception rather than the preferred single-bundle shape; R.a predates the subphase structure and its patch shipped independently.

---

## Story breakdown

Story letters continue monotonically from R.a. `R.z` is parked at the end of the file for the in-flight `refactor_plan` session and is **not** part of this subphase.

| ID | Story | Notes |
|---|---|---|
| **R.b** | **Integration spike** — off-`PATH` completion | Time-boxed, throwaway. Deliverable is a *documented decision*, not production code |
| **R.c** | `completion` group scaffold + `show` | Click group, `--shell auto` detection, generation + post-processing. No filesystem writes |
| **R.d** | `install` / `uninstall` — bash rc-block route | Sentinel machinery, idempotency, byte-clean round-trip, `--bin` / `--rc` |
| **R.e** | `install` / `uninstall` — zsh fpath route | Autoload file, `fpath` rc line, `compinit` bootstrap |
| **R.f** | `completion status` | Per-shell absent / installed / stale detection |
| **R.g** | Legacy pyve sentinel adoption | Detect the exact pair, replace, report |
| **R.h** | `heal` stale-completion warning | Warn-don't-auto-fix; no auto-repair |
| **R.i** | **`v2.19.0` Subphase R-1 bundled release** | FR-7 rewrite, tech-spec, README, site docs, CHANGELOG, version bump |

**Why the spike is first.** Finding 1 means the central mechanism — making completion function when the binary is off `PATH` — is unproven. Per `best-practices-guide.md` § "Hello World First," this is an **integration spike**: a new integration boundary (Click's completion protocol × two shells × an off-`PATH` host layout) whose viability should be established before the command surface is built against it. If post-processing turns out to be infeasible, `--bin`'s contract with pyve changes and R.c–R.g are all written differently.

---

## Out of scope

Each item below is deferred deliberately, not overlooked.

- **fish support.** Click supports it and FR-7 documents it, but fish uses a third mechanism (a file in `~/.config/fish/completions/`, no rc block). Deferred to a follow-on story or subphase; FR-7 must note the gap explicitly so the docs don't over-promise.
- **Whether `~/.local/bin` is on the user's `PATH`.** pyve chose that shim location, so pyve owns its reachability — tracked as a pyve-side story. This subphase only ensures completion does not *depend* on `PATH` resolution.
- **macOS system bash 3.2.** The generated bash script calls `compopt`, a bash ≥ 4.0 builtin, so dir/file completions would error on stock macOS bash. Linux bash and Homebrew bash are unaffected. Record as a known limitation rather than working around it.
- **PowerShell / Windows shells.** Click ships no generator for them; project-guide otherwise claims Windows support, so this is a documented asymmetry.
- **The pyve-side coordinating change.** Retiring `add_project_guide_completion` and calling `project-guide completion install --bin …` lands in the pyve repo, gated on the `v2.19.0` release.
- **Auto-installing completion during `init` or `heal`.** Tempting, but writing to a user's rc file without being asked is a different consent question than repairing files inside the project. `heal` only *warns* (R.h).
