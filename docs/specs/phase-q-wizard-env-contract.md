# Change request: env-spec contract — Pyve-owned, versioned, closed vocabulary + the `plan_envs` handoff

**Target repo:** [`project-guide`](https://github.com/pointmatic/project-guide)
**Consumption:** `pyve` keys cross-stack behavior off `.project-guide.yml` and consumes the env-dependencies spec that `project-guide`'s drafted `plan_envs` mode authors. Surfaced by Spike [N.ao](../spike-n-ao-project-guide-provisioning.md).

---

## Problem statement

Three cross-repo couplings are currently informal and need to be contracts:

1. **Who owns the env vocabulary.** `purpose`, `backend`, `languages`, `frameworks`, `packaging` (plus advisory `app_type`) values flow from a `project-guide`-authored spec into `pyve.toml`. Without a single owner of the *closed set* of legal values, every consumer hits the "unknown entity — now what?" branch and either guesses or silently drops it.
2. **`.project-guide.yml` is load-bearing for pyve, not just `project-guide`'s own state.** Pyve treats its *presence* as the canonical "project-guide is installed" signal and — as of Story N.aj — as a **Python-active signal** (`python_plugin_is_active_in_project` returns active when `.project-guide.yml` exists). A filename/shape change is a **coordinated breaking change**.
3. **The `plan_envs` ↔ pyve handoff has no agreed boundary** — what each side authors, validates, and how drift is reconciled.

---

## A. Pyve owns the env spec and its versioning

**Pyve is the sole owner of the env-spec schema, its version, and the closed vocabulary for every axis** (`purpose`, `backend`, `languages`, `frameworks`, `packaging`, `app_type`). `project-guide` **consumes** this vocabulary; it never invents values.

**The vocabulary is forward-looking.** Pyve's published vocabulary enumerates *every value Pyve recognizes* — including ones it does **not yet implement**, documented explicitly as **no-ops**. This gives a rich declarative spec paired with a deliberately lagging implementation tool, and it **forces `project-guide` to track Pyve's development** (new values appear only when Pyve publishes them).

**The trichotomy — every value at every axis is exactly one of:**

| Class | Meaning | Pyve behavior |
|-------|---------|---------------|
| **known + implemented** | Pyve materializes it | normal lifecycle (init/check/run/purge) |
| **known + no-op** *(a.k.a. advisory)* | recognized in the spec version, not yet implemented | **recorded** in `pyve.toml` + **advisory** surfaced; **not materialized**; never an error |
| **unknown** | not in the spec version's vocabulary | **spec violation = bug → hard error + abort** (both in `pyve.toml` validation and in `pyve env sync` ingestion) |

There is no fourth "guess / best-effort" branch. That is the whole point: a nonconformant value is loud, not silent.

**Versioning.** The env spec carries a Pyve-owned `spec_version`. It tracks the env-spec/template format and aligns with `pyve_schema`'s major (`3.x`); the **env spec is a superset of `pyve.toml`'s schema** (it carries no-op vocabulary and richer human attributes `pyve.toml` does not model). Adding a no-op value within a major is published via the template without a `pyve.toml` schema bump; a §4-shape change bumps `spec_version`.

**Authoritative source.** Pyve owns [`docs/specs/project-guide-requests/env-dependencies-template.md`](env-dependencies-template.md) — the versioned schema + vocabulary + blank structure. `project-guide`'s `plan_envs` fills it; **bumping the template is how new values propagate to `project-guide`.**

**Current enforcement state (honest).** Today only `purpose` is enforced as a closed set (`VALID_PURPOSES = (run, test, utility, temp)` in [`lib/pyve_toml_helper.py`](../../lib/pyve_toml_helper.py)). `backend`/`languages`/`frameworks`/`packaging` are not yet closed-set-validated, and the no-op-vs-error machinery does not exist yet. Implementing the trichotomy (closed-set validation + no-op recording/advisory + hard-error abort) for all axes is a **Pyve follow-up (F6, below)**. Until it lands, unknown `backend`/`language` values are accepted leniently; the contract's *target* state is hard-error.

---

## B. The env-spec schema (concrete)

**§4 of `docs/specs/env-dependencies.md` is a single machine-readable YAML document** — the only machine surface of the doc. (§5–§9 — dependency source classes, lock strategy, proposed backends, test-coverage matrix, changelog — are human narrative and are **never** parsed or diffed by pyve.)

```yaml
spec_version: "3.0"          # Pyve-owned; matches the template version
project: <name>
description: <one line>
envs:
  <env-name>:
    purpose: run | test | utility | temp
    backend: <backend>           # from the closed backend vocabulary below
    default: true | false
    path: "."                    # plugin root; polyglot sub-path allowed (e.g. "src/frontend")
    languages: [<language>, ...]  # closed vocabulary
    frameworks: [<framework>, ...]# closed vocabulary (intrinsic kind: app | test | lint)
    packaging: <packaging>       # artifact kind Pyve materializes (closed vocabulary)
    app_type: <app_type>         # advisory metadata (closed vocabulary)
    require_min_version: { <tool>: "<ver>", ... }  # advisory: un-installable-toolchain pins
    manual_steps: ["<human-only step>", ...]       # advisory: seams Pyve cannot CLI-drive (e.g. iOS signing)
```

**Recognized §4 fields (spec_version 3.0):** `purpose`, `backend`, `default`, `path`, `languages`, `frameworks`, `packaging`, `app_type`, `require_min_version`, `manual_steps`. `purpose`/`backend`/`default`/`path`/`languages`/`frameworks`/`packaging` are the **pyve.toml-projectable subset** (they map 1:1 to an `[env.<name>]` block); `app_type`, `require_min_version`, and `manual_steps` are recognized **advisory** metadata (surfaced in `check`/`status`, never materialized). An **unrecognized field** is treated like an unknown value → error.

### Closed vocabulary (spec_version 3.0)

The authoritative enumeration is **Pyve-owned**, published in [`env-dependencies-template.md`](env-dependencies-template.md) §2 and reproduced here; **per-value definitions** (what each `purpose` / `packaging` / `app_type` value means, plus framework-`kind` and implemented-vs-advisory semantics) live in that same template §2 glossary — this contract reproduces the *enumeration*, not the definitions. (`pyve_toml_helper.py`'s `VALID_*` sets — F6 — are the runtime-enforced machine mirror and MUST stay in lockstep with the template; one is generated from or asserted against the other, never independently edited.) Each axis is a **closed set** — a value outside it is unknown → hard error + abort. Each value is exactly one of two classes: **implemented** (a real Pyve-surface integration exists today) or **advisory** (recorded + surfaced in `check`/`status`, never materialized, never an error). "Advisory" is the single home for every not-yet-implemented value, regardless of roadmap status (the trichotomy's "known + no-op" class).

| Axis | Implemented (integrated with a Pyve surface) | Advisory (recorded + surfaced, never materialized) |
|------|----------------------------------------------|-----------------------------------------------------|
| `purpose` | `run`, `test`, `utility`, `temp` | — |
| `backend` · project-virtualized | `venv`, `micromamba`, `pnpm`, `npm`, `yarn` | `uv`, `poetry`, `conda`, `bun`, `deno` |
| `backend` · cache-backed | — | `cargo`, `go`, `bundler`, `swiftpm`, `xcode`, `android_sdk`, `gradle`, `maven`, `sbt`, `dotnet`, `conan`, `cmake` |
| `backend` · check-only / special | — | `homebrew`, `apt`, `docker`, `podman`, `none` |
| `languages` | `python`, `javascript`, `typescript` | `bash`, `c`, `cpp`, `c_sharp`, `java`, `kotlin`, `scala`, `go`, `swift`, `objective_c`, `rust`, `ruby` |
| `frameworks` · app | `sveltekit` | `flask`, `fastapi`, `django`, `react`, `vue`, `jupyter`, `marimo`, `spring`, `j2ee`, `kotlin_multiplatform`, `rails`, `sinatra`, `swiftui`, `uikit` |
| `frameworks` · test | — | `pytest`, `vitest`, `jest`, `mocha`, `playwright`, `cypress`, `bats`, `rspec`, `minitest`, `xctest`, `junit` |
| `frameworks` · lint | — | `ruff`, `mypy`, `black`, `isort`, `flake8`, `pylint`, `eslint`, `prettier`, `shellcheck`, `shfmt`, `ktlint`, `detekt`, `scalafmt`, `scalafix`, `google_java_format`, `rustfmt`, `clippy`, `gofmt`, `golangci_lint`, `rubocop`, `swiftlint`, `swiftformat`, `clang_format`, `clang_tidy` |
| `frameworks` · special | — | `none` |
| `packaging` | — | `container`, `static`, `server`, `serverless`, `package`, `binary`, `mobile_app`, `lock_bundle`, `none` |
| `app_type` | — (advisory metadata) | `api`, `cli`, `service`, `library`, `desktop`, `mobile`, `embedded`, `script`, `web`, `none` |

- **`node` is the plugin/runtime, not a language** — the languages it backs are `javascript` / `typescript`.
- **Backend categories** follow the S6 taxonomy: *project-virtualized* (per-project state + PATH activation), *cache-backed* (shared cache + lockfile + a CLI build tool — includes `xcode`/`swiftpm`/`android_sdk` per **S16**; the un-installable-toolchain fact rides `require_min_version`, not the category), *check-only* (presence-verified, Pyve runs no build).
- **`frameworks` carry an intrinsic `kind`** (app / test / lint, per S14) — looked up in Pyve's registry, never an authoring choice. One env's `frameworks` list may mix kinds; the plugin hook dispatches by reading them.
- The empty/not-applicable value is `none` (machine §4); the template's human prose may also use `N-A`.
- A value **outside** its column set → unknown → hard error + abort. A value in the **advisory** column → recorded + surfaced, never blocks.

### No-op semantics (concrete)

- **No-op `backend`** (`homebrew`/`apt`/`docker`/`none`/…): `pyve env sync` writes the `[env.<name>]` block to `pyve.toml` (it is schema-valid); `pyve init` / materialization **skips** it with an advisory — *"env `<name>` declares backend `homebrew`, which pyve does not yet materialize; provision it manually per the env spec."* This exactly matches the worked example ([env-dependencies-repo_gitbetter.md](env-dependencies-repo_gitbetter.md) §8): gitbetter's real test toolchain (`bats`, `shellcheck`) is `homebrew`/`apt`, so its `testenv` is a declared-but-unmaterialized surface.
- **No-op `language` / `framework` / `app_type`**: advisory metadata only — surfaced in `pyve check` / `pyve status`, never materialized.

---

## C. The `plan_envs` ↔ pyve handoff

- **`project-guide plan_envs` authors `docs/specs/env-dependencies.md`**, filling §4 from Pyve's template at the current `spec_version`.
- **`plan_envs` reads `pyve.toml` as one input** (what is currently materialized) but §4 reflects the **analyzed ideal** (from `features.md` / `tech-spec.md` / the codebase). The two legitimately differ when reality lags the design — that divergence is the reason the drift surface (§D) exists. `plan_envs` must **not** merely mirror `pyve.toml` back into §4 (that would make the diff perpetually empty and add nothing).
- **`plan_envs` regenerates the whole doc fresh from the blank template each run.** This self-heals when Pyve bumps the template (new vocabulary / new §4 shape): re-running reformats the doc to the current template and rewrites the narrative sections.
- **No `project-guide`-side automation, hashing, or timestamping.** `env-dependencies.md` is a **point-in-time artifact**, exactly like `features.md` / `tech-spec.md`: the live config may drift from it, and that is expected and fine.
- **`project-guide` emits only `spec_version`-conformant values.** A nonconformant value is a `project-guide` bug that Pyve hard-errors on (§A trichotomy) — drift cannot enter silently.

---

## D. Drift reconciliation (Pyve side)

**Stateless live diff.** Pyve stores no baseline and no fingerprint. The diff is computed live: parse §4 → project to the `[env.*]` shape (the projectable subset only) → diff against the **current `pyve.toml`**. `pyve.toml` *is* the baseline; "new or changed spec" reduces to "§4 ≠ `pyve.toml` right now."

- **`pyve check`** — surfaces a new/changed env spec and prints the diff if non-empty. **`warn` severity (exit 0)** on the composed severity ladder — never fails CI, because an intentionally spec-ahead project (envs planned but not yet materialized) is a legitimate steady state.
- **`pyve env sync`** (developer-initiated) — ingests §4, **validates against `pyve_schema`** (unknown value → error/abort; no-op value → accepted), presents the diff, and confirms `[Y/n]`:
  - **Default `Y`** — env config is low-volatility and the diff is shown before applying.
  - **Writes `pyve.toml` only — does not materialize.** Env build/teardown stays in the explicit lifecycle commands, so a `Y` is never destructive *to disk*.
  - **Destructive diffs default to `N`** (or require explicit confirm): dropping an `[env.<name>]` block whose env exists on disk, or a `backend` flip implying a rebuild — mirroring how `pyve init --force` prompts while `pyve update` does not.
- **Projectable subset only.** `name`, `purpose`, `backend`, `default`, `path`, `languages`, `frameworks`, `packaging` are diffed/synced; `app_type`, `require_min_version`, `manual_steps`, and §5–§9 prose are never diffed (advisory/prose edits must not trigger reconciliation noise).
- **Spec discovery.** Pyve reads `env_spec_path` from `.project-guide.yml` (tool-state pointer), defaulting to `docs/specs/env-dependencies.md`.

---

## E. `.project-guide.yml` contract

- **Load-bearing marker.** Pyve keys behavior off the file's *presence* (install marker; N.aj Python-active signal). Filename/shape is a stable public contract.
- **Tool-state only — never the env model.** `pyve.toml` is the single authority for env config; `.project-guide.yml` must not carry an env mirror. It **may** carry `env_spec_path: <path>` as the spec-discovery pointer (§D).
- **Breaking-change protocol.** A rename/reshape is a **major** `project-guide` change that MUST (a) ship behind a deprecation window where the old marker still resolves, and (b) be paired with a pyve story updating the marker check + the N.aj gate. Pyve's **F5** contract-guard test trips a red build on an unannounced change.

---

## Motivation

- **One owner of the vocabulary** eliminates the "unknown entity" branch: known-implemented, known-no-op, or hard error — nothing else.
- **A forward-looking spec with a lagging implementation** lets the declarative surface be rich now while Pyve implements backends/languages on its own cadence, and keeps `project-guide` aligned to Pyve releases.
- **A point-in-time spec + stateless live diff** gives drift *awareness* without sync machinery, timestamps, or a second source of truth — `pyve.toml` stays canonical.

## Compatibility notes

- **`plan_envs` is unreleased** — the handoff + the Pyve-owned vocabulary can be designed in now at zero compat cost.
- **Additive marker contract** — ratifying `.project-guide.yml`'s current shape constrains only *future* changes.
- **Pyve adoption** carries a **minimum `project-guide` version** once `plan_envs` ships, pinned at the implementing pyve story (F4), alongside the existing `--no-input ≥ 2.2.3` precedent.

## Pyve-side follow-up

Extends Spike N.ao §5 (F1–F5):

- **F4** — `pyve env sync`: ingest §4, validate, diff, `[Y/n]`-apply to `pyve.toml` (gated on the upstream `plan_envs` release + this contract).
- **F5** — `.project-guide.yml` contract-guard test + min-version pin + `env_spec_path` discovery.
- **F6 (new)** — closed-vocabulary + no-op trichotomy: extend `pyve_toml_helper.py` with `VALID_BACKENDS` / `VALID_LANGUAGES` / `VALID_FRAMEWORKS` / `VALID_PACKAGING` / `VALID_APP_TYPES` (implemented + advisory sets, versioned), recognize the advisory fields `require_min_version` / `manual_steps`, the no-op recording + advisory path in materialization, and hard-error abort on unknown values. Frameworks carry an intrinsic `kind` (app/test/lint, S14); backends carry an S6 category (project-virtualized/cache-backed/check-only, incl. S16). Also lands `pyve check`'s live-diff (warn-severity) surface.
