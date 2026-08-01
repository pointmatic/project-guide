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

## Phase R: (Theme TBD)

---

### Story R.a: v2.18.1 Gitbetter `git-commit` subcommand [Done]

Gitbetter just added a `git-commit` subcommand to allow iterations on commits locally and then pushing a batch to GitHub, which will save substantially on GitHub Actions CI minutes. 

This new `project-guide git-commit` subcommand is nearly identical to its sibling `project-guide git-push`. From the Project Guide perspective, the two commands have the identical interface and behavior. 

- [x] Add `project-guide git-commit` subcommand that mirrors `project-guide git-push` functionality — both share `_run_gitbetter_wrapper(tool_name, …)` in `cli.py`
- [x] Update tests to cover the new command — 8 new `test_git_commit_*` tests (636 passed total)
- [x] Update documentation to reflect the new command — README, site commands.md, concept/features/tech-spec/project-essentials
- [x] Bump patch version to `v2.18.1` — `version.py`, `pyproject.toml`, CHANGELOG dated 2026-08-01

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
