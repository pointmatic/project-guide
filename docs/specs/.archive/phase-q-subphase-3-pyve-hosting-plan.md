# phase-q-subphase-3-pyve-hosting-plan.md — project-guide (Python)

Subphase Q-3 plan: **Pyve-managed-hosting cross-repo contract.**

Subphase Q-3 of [Phase Q (DX Improvements & Subphase Support)](phase-q-dx-subphases-plan.md). Pins four cross-repo contracts that let Pyve host project-guide as a globally-shimmed tool in its toolchain venv (Pyve Story N.aw), and adds pyve-managed-hosting awareness to project-guide's user-facing surfaces so installation advice and status output reflect the hosted model when pyve is detected.

Companion input digested for this planning session: [`phase-q-pyve-toolchain-hosting.md`](phase-q-pyve-toolchain-hosting.md) — the cross-repo contract from Pyve's perspective. Three of its four "Project-guide side" requirements describe already-correct behavior that needs to be pinned as a tested contract; the fourth is genuinely new behavior gated on pyve detection.

---

## Gap Analysis (Subphase Q-3)

### Three contracts hold today but are unpinned

A code-grounding audit during Q-3 planning confirmed three of the four cross-repo contracts already hold:

- **Install-location independence.** `project_guide/cli.py` and `project_guide/runtime.py` use `Path.cwd()` uniformly for project state — config discovery ([runtime.py:142](../../project_guide/runtime.py)), project-name resolution ([cli.py:209](../../project_guide/cli.py)), archive-stories ([cli.py:1035](../../project_guide/cli.py)). Nothing reads from the package install location for per-project state.
- **`--version` surface.** Wired at [cli.py:89](../../project_guide/cli.py) via Click's `@click.version_option(version=__version__)`. Standard Click output format (`"project-guide, version X.Y.Z"`) — pinnable.
- **`.project-guide.yml` marker.** Filename hard-coded in `Config.load()` / `Config.save()`; written at project root; carries `installed_version` and `target_dir` plus the other Schema-2.0 fields.

What's missing is the **tested contract** — no `tests/test_cli.py` assertion currently codifies "init invoked from a temp cwd writes config to that cwd, not to the package install location"; no test pins the `--version` output format against a regex; no test asserts the `.project-guide.yml` filename literal + required-field set as the cross-repo marker shape. Pyve Story N.aw will pin a minimum project-guide version once this subphase ships; tests pinning the contract surface are what make that pin meaningful.

### Pyve-managed-hosting awareness is not yet wired

`pyve_installed` is detected at `init` time ([cli.py:251–262](../../project_guide/cli.py)) and cached in `.project-guide.yml` as `pyve_version`. Today the flag's only consumer is `render.py:_read_pyve_essentials()` — it gates auto-rendering of `pyve-essentials.md` into `go.md`. The flag is **not** consumed by:

- Onboarding install advice in the rendered `go.md` (`_header-common.md` says "After installing project-guide (`pip install project-guide`)..." unconditionally).
- The developer-reference page (`developer/project-guide.md` says the same thing, plus a pre-existing `project-guides` typo).
- The top-level `README.md` install section.
- `project-guide status` output (no footer naming the host).

Under Pyve's planned toolchain-venv hosting, `pip install project-guide` is wrong advice for users with pyve installed — the user runs `pyve self install` and pyve manages the install path. Without pyve-aware branching at these surfaces, the rendered guidance contradicts the hosted reality.

### No defensive guard against local-install drift

If a user adopts pyve-managed hosting *after* having previously run `pip install project-guide` into a project-local venv, both installs coexist. `which project-guide` resolves to whichever is first on `PATH`, which can be either; behavior diverges silently with version drift. Project-guide has no diagnostic surfacing this state to the user. Defensive guard at `status` time would catch the case and prompt for `pip uninstall project-guide`.

---

## Feature Requirements (Subphase Q-3)

### Q-3-FR-1: Cross-repo contract pinning (tests)

Three new test surfaces in `tests/test_cli.py` (or a new `tests/test_cross_repo_contract.py` — author chooses during implementation):

- **Install-location independence test.** `CliRunner().isolated_filesystem()` invokes `project-guide init` from a temp cwd; asserts `(tmp / ".project-guide.yml").exists()` and `(tmp / "docs/project-guide/go.md").exists()`; asserts no writes to the package install location. Same shape for `update` and `mode`.
- **`--version` output format test.** Invokes `project-guide --version`, asserts output matches `r"project-guide, version \d+\.\d+\.\d+\n?"`. The regex is the cross-repo contract Pyve pins against; changing the format requires a coordinated breaking change.
- **`.project-guide.yml` marker shape test.** After `init`, asserts the file is named exactly `.project-guide.yml` (no rename, no extension drift) at project root, and that `yaml.safe_load()` of its contents yields a dict containing **at minimum** `version` (schema), `installed_version`, `target_dir`, `current_mode`. The asserted fields are the **cross-repo-contract subset** — additional fields may exist (e.g., `pyve_version`, `metadata_overrides`); their absence is not a contract violation.

### Q-3-FR-2: Cross-repo contract documentation

Two doc surfaces:

- **New `features.md` section.** "Cross-Repo Contracts" subsection under the existing Configuration / Acceptance Criteria neighborhood, enumerating the four contracts (cwd-relative operation, `--version` stability, `.project-guide.yml` marker stability, pyve-managed-hosting awareness). Each item names the surface, the asserted invariant, and the test guarding it (or "implementation only — no test" for the awareness case where the test is template-render assertions).
- **New `project-essentials.md` section.** "Pyve cross-repo contracts" appended after the (Q-2-installed) "Pyve env-spec vendored-template contract" section. Documents the four contracts as architectural invariants future LLMs must respect. The two new Q-3 invariants beyond what's documented in features.md: **(a) any rename of `.project-guide.yml` or removal of the contract fields is a coordinated breaking change** requiring a paired Pyve story; **(b) pyve detection is cached in `.project-guide.yml`'s `pyve_version` field at init time and not re-run at every CLI invocation** — `status`, help, and template branches read the cached value, keeping commands cheap and predictable.

### Q-3-FR-3: Pyve-managed-hosting awareness in templates

Two bundled-template files branch their install-advice content on `pyve_installed`:

- **`project_guide/templates/project-guide/templates/modes/_header-common.md`.** Current text at line 6 ("After installing project-guide (`pip install project-guide`) and running `project-guide init`, instruct your LLM as follows...") branches via Jinja:
  - `pyve_installed=True`: "Pyve manages project-guide for you. From your project root, run `project-guide init` to scaffold the docs, then instruct your LLM as follows..."
  - `pyve_installed=False`: existing text preserved.
- **`project_guide/templates/project-guide/developer/project-guide.md`.** Same branch shape. Also corrects the existing `project-guides` typo (singular form) inline — drift catch-up since we're touching the file.

Branch logic uses the existing `pyve_installed` Jinja context variable already threaded by `render.py`; no new render-pipeline plumbing needed.

### Q-3-FR-4: Pyve-managed-hosting awareness in README

A new "Installation via pyve (recommended)" section added to the top-level `README.md` above the existing pip-install section. One short paragraph: "If you use [pyve](https://pointmatic.github.io/pyve/), let pyve install project-guide globally for you — `pyve self install` provisions project-guide in pyve's toolchain venv and creates a `~/.local/bin/project-guide` shim. Otherwise, `pip install project-guide` per the section below." Standalone pip-install advice preserved as-is — non-pyve users see no breaking change.

### Q-3-FR-5: Pyve-managed-hosting awareness in `project-guide status`

When `config.pyve_version is not None`, `project-guide status` appends a one-line footer to the existing output: `Managed by pyve v<version> (detected at init time).` The footer is dim-styled (matches the existing "Run 'project-guide update' to sync" hint convention) so it doesn't dominate the section layout.

**No runtime re-detection.** The status footer reads the cached `config.pyve_version`; it does **not** re-invoke `pyve --version` per status call. Trade-off:
- **Pro**: status stays cheap (no subprocess).
- **Pro**: predictable behavior — pyve detection is a one-time decision at init.
- **Con**: a user who installs pyve *after* `project-guide init` won't see the footer until they run `project-guide init --force` (or, in a future story, a `project-guide refresh-detection` surface).

This trade-off is recorded in `project-essentials.md` per Q-3-FR-2 invariant (b).

### Q-3-FR-6: Defensive local-install guard in `heal`

When `config.pyve_version is not None` AND the running project-guide's distribution location resolves to a project-local path, `project-guide heal` (and its auto-hook on every CLI invocation) emits a stderr warning:

```
⚠ Local project-guide install detected at <path>.
  Pyve is configured to manage project-guide globally.
  Remove the local install with: pip uninstall project-guide
```

**Why `heal`, not `status`.** Mirrors the P.o `go.md`-tracked warning pattern exactly — `heal` detects a state that requires a user-initiated `pip` operation, emits a warning, and never auto-fixes. Two structural advantages over a status-only surface:
- **Per-invocation visibility via the auto-hook.** The warning fires on every `project-guide` command including `--help` / `--version` (per FR-14's auto-hook contract), so the user sees it until they resolve it — not just when they remember to run `status`.
- **Existing precedent.** `heal` already warns about another `pip`-/`git`-resolvable state (tracked `go.md`); adding the local-install warning to the same surface keeps `heal`'s job (detect drift-from-canonical-install-state, warn the user, never auto-fix) coherent.

**Detection logic.** Use `importlib.metadata.distribution("project-guide")` to get the install location of the currently-running project-guide. If that path is a descendant of `Path.cwd()` (e.g., under `<cwd>/.venv/`, `<cwd>/.pyve/envs/<name>/`, or any other project-local subdirectory) → warn. Pure-Python; no subprocess; cheap.

**Silent-when-clean preserved.** When no local install is detected, `heal` stays silent on this axis (matches the existing FR-14 contract: silent-when-clean, prompt/warn-when-dirty).

**Why no auto-uninstall.** Project-guide does not call `pip uninstall` on the user's behalf — same wrapper-initiates-side-effects constraint that bounded the P.k `git-push` wrapper and the P.o `go.md`-tracking guard. The user runs `pip uninstall project-guide` on their own schedule.

**Status footer (Q-3-FR-5) coexists.** The status footer is informational ("Managed by pyve v…") — a one-time read-out of the cached host state when the user deliberately checks. The heal warning is defensive — a per-invocation diagnostic of a drift state requiring user action. They surface different things at different lifecycle points; both stay.

---

## Technical Changes (Subphase Q-3)

- **Edits only to templates, README, CLI status output, and tests.** No `.project-guide.yml` schema change; no metadata schema change; no new CLI subcommand; no new runtime dependencies.
- **Files touched** (source of truth, not installed copies):
  - **Edited**: `project_guide/templates/project-guide/templates/modes/_header-common.md` (pyve_installed branch)
  - **Edited**: `project_guide/templates/project-guide/developer/project-guide.md` (pyve_installed branch + typo fix)
  - **Edited**: `README.md` (Installation via pyve section)
  - **Edited**: `project_guide/cli.py` (`status` command: pyve-detected footer; `_apply_heal()` / drift-detection path: local-install warning following the P.o `go.md`-tracked precedent)
  - **Edited**: `docs/specs/features.md` (Cross-Repo Contracts section)
  - **Edited**: `docs/specs/project-essentials.md` (Pyve cross-repo contracts section)
  - **Created/Edited**: `tests/test_cli.py` or new `tests/test_cross_repo_contract.py` (contract-pinning tests + status footer/warning tests)
  - **Bumped**: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` — once, at the end of Q-3's release story (Q.n).
- **Installed-copy propagation.** After editing source-of-truth templates the developer runs `pyve run project-guide update` to propagate to `docs/project-guide/`; auto-heal hook covers fresh clones.
- **Test impact.** Adding ~6–8 new test cases (3 contract-pinning + 2 template-branch + 1 status-footer + 1 heal-local-install-warning + 1 heal-silent-when-clean). The parametrized render-mode regression remains green since the template branches preserve existing rendering when `pyve_installed=False`.

---

## Production Concerns

**None for Subphase Q-3.** No new runtime dependencies, no I/O / network surface, no security boundary changes. Status's local-install warning uses `importlib.metadata` (stdlib) — no subprocess. Pyve detection at status time reads cached config, not live subprocess.

---

## Anticipated Breaking Changes

**None for Subphase Q-3.** Walked at Step 5 — fully additive:

- **Template branches** preserve existing output for `pyve_installed=False`. Non-pyve users see no change.
- **README addition** appends a new section above the existing pip-install section; pip-install advice stays as-is.
- **Status footer** is a one-line addition, gated on pyve detection. Non-pyve users see no change.
- **Local-install warning** is a one-line addition, gated on pyve detection AND project-local path resolution. Users without the local-install footgun see no change.
- **Cross-repo contract documentation** describes already-correct behavior; the *contract* publication is the new surface, but the *behavior* is unchanged.
- **Tests** are additive — they pin already-correct behavior without changing it.

No version-bump escalation triggered.

---

## Anticipated Version Bump Target

**v2.13.0 — minor.** New behavior (pyve-managed-hosting awareness, defensive local-install guard) plus newly-published cross-repo contracts. Per Version Cadence "Feature or improvement → minor."

Bundled release at end of Subphase Q-3; bumped exactly once on the last story (Q.n).

Subphase Q-1 = v2.11.0; Q-2 = v2.12.0; Q-3 = v2.13.0.

---

## Out of Scope

Walked at the gate; deferred items:

- **Pyve-side Story N.aw work.** Toolchain-venv install, `~/.local/bin/project-guide` shim, `DEFAULT_PYTHON_VERSION`-bump reconcile, removal of pyve's per-project `install_project_guide` venv-targeting — all live in the Pyve repo. Project-guide's deliverable is the contract surface; Pyve consumes.
- **Runtime pyve re-detection.** `status` reads cached `config.pyve_version` per Q-3-FR-5. A hypothetical `project-guide refresh-detection` subcommand to re-run `pyve --version` and update the cached value is deferred (YAGNI until a user reports the cache-staleness footgun in practice).
- **Auto-uninstall of local project-guide.** The defensive guard warns and hints; it does not invoke `pip uninstall` itself. Same wrapper-initiates-side-effects discipline as P.k / P.o.
- **Detection of conflicting pyve-managed installs across multiple toolchain venvs.** Out of scope — Pyve owns the toolchain-venv path policy; project-guide trusts it.
- **Help-text expansion.** No `project-guide --help` text changes in Q-3. The pyve-managed-hosting awareness is surfaced via the rendered `go.md` (template branches) and the README, which are the natural onboarding surfaces. Help text stays terse.
- **Backfilling `docs/specs/cross-repo-contracts.md` as a dedicated file.** The four contracts live in `features.md` (functional surface) and `project-essentials.md` (architectural invariant), not in a new artifact. Spinning a separate doc would create a third place to update on contract changes.
- **Subphase Q-4 and beyond.** Each future Q-N subphase planned via its own `plan_production_phase` session.

---

## Implementation Strategy

Three stories in Subphase Q-3, executed in document order:

1. **Q.l — Cross-repo contract pinning (tests + documentation).** Pins already-correct behavior via new tests; publishes the contracts in `features.md` and `project-essentials.md`. No CLI or template changes. Lands first so Q.m's new behavior has a documented contract to satisfy.
2. **Q.m — Pyve-managed-hosting awareness (templates + README + CLI + tests).** Adds pyve-aware branching to `_header-common.md`, `developer/project-guide.md`; adds README "Installation via pyve" section; adds status footer + local-install warning; adds template-branch and status-output tests.
3. **Q.n — v2.13.0 Subphase Q-3 bundled release.** Bumps `project_guide/version.py`, `pyproject.toml`, adds `## [2.13.0]` CHANGELOG entry covering Q.l + Q.m. Closes Subphase Q-3.

Stories within Subphase Q-3 carry **no version in their title** until Q.n.

**Story-letter continuity** across the Q-2 → Q-3 boundary: Q-2's release closed at `Q.f` (v2.12.0), then `Q.g`–`Q.k` landed as post-release `code_direct` doc-fix tail stories appended under Q-2's heading. Q-3 picks up at **`Q.l`** — the next monotonic letter. Per the (Q-1-installed) `_phase-letters.md` Subphases rule, no reset across subphase boundaries.

**No upstream dependency.** Q-1 (v2.11.0) and Q-2 (v2.12.0) have both shipped at the time of this planning session, as have the Q.g–Q.k tail stories. Q-3's implementation can begin immediately after approval — no waiting on a prior bundle.

---

## Acceptance Criteria (Subphase Q-3)

1. New tests pin install-location independence, `--version` output format, and `.project-guide.yml` marker shape; all pass on the v2.13.0 commit.
2. `features.md` carries a "Cross-Repo Contracts" section enumerating the four contracts with their guarding tests.
3. `project-essentials.md` carries a new "Pyve cross-repo contracts" section after the "Pyve env-spec vendored-template contract" section, documenting the architectural invariants.
4. The rendered `go.md` shows pyve-aware install advice when `pyve_installed=True` and the pre-Q-3 text when `pyve_installed=False`. The parametrized render-mode regression remains green.
5. `README.md` carries a "Installation via pyve (recommended)" section above the existing pip-install section.
6. `project-guide status` shows a one-line footer naming the pyve-managed host when pyve is detected.
7. `project-guide heal` (and its auto-hook on every CLI invocation) emits a stderr warning when pyve is detected AND the running project-guide is installed under the current project tree (cwd descendant), with a `pip uninstall project-guide` hint. The warning is silent when no local install is detected (auto-hook stays silent-when-clean).
8. `pyve test` and `pyve testenv run ruff check project_guide/ tests/` both pass on the v2.13.0 commit.
9. `CHANGELOG.md` `## [2.13.0]` entry dated, describes the cross-repo contract publication and pyve-managed-hosting awareness as one bundled release; cross-references [`phase-q-pyve-toolchain-hosting.md`](phase-q-pyve-toolchain-hosting.md).
