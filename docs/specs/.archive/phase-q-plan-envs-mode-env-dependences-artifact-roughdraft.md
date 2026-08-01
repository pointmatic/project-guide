# env-dependencies-template.md - <repo_name>

This is a **template**. It defines the *structure* of a pyve environment-dependencies
document. To produce the concrete document for a repository, copy this file to
`pyve-environment-dependencies-repo_<repo_name>.md` and fill in every `<placeholder>`,
replacing the instructional `<!-- HOW TO FILL -->` comments with real content.

The purpose of the concrete document is to formally enumerate:

1. The **root development environment** required to develop the repo (the environment a
   contributor or LLM must stand up before doing anything else).
2. One or more **named test environments** (the first defaults to `testenv`) required to
   *efficiently, effectively, and completely* test the codebase.

A secondary purpose is to surface **environment requirements that pyve does not yet
materialize** (advisory backends) and **mechanisms missing from the closed vocabulary
entirely** (Pyve change-requests), so the Pyve-owned backend vocabulary can grow over time.
See [§3 Backend Catalog](#3-backend-catalog) and [§8 Backend Gaps & Pyve
Change-Requests](#8-backend-gaps--pyve-change-requests).

> **Related docs**
> - `features.md` — what the project does (scope, requirements, behavior).
> - `tech-spec.md` — how the project is built (architecture, dependencies, testing strategy).
> - `pyve-environment-dependencies-repo_<repo_name>.md` — the filled-in instance of this template.
> - Pyve backends reference: <https://pointmatic.github.io/pyve/backends/>

---

## 0. How To Use This Template

<!-- HOW TO FILL: Remove this entire section from the concrete document. It is guidance only. -->

- Every section below is **required** unless explicitly marked *(optional)*.
- Replace `<placeholder>` tokens and resolve every `<!-- HOW TO FILL -->` comment.
- Keep section numbering and headings stable so instances are diffable against each other.
- Prefer **declarative facts** (pinned versions, exact commands, file paths) over prose.
- If a section does not apply, keep the heading and write `N/A — <one-line reason>`.
- The document is **source-controlled** and **change-controlled**: update §9 on every edit.

---

## 1. Document Metadata

| Field | Value |
|-------|-------|
| **Repo name** | `<repo_name>` |
| **Primary language(s)** | `<e.g. Bash 4.0+, Python 3.14>` |
| **Pyve version** | `<pyve version X.Y.Z>` |
| **Doc status** | `Draft` \| `In Review` \| `Approved` |
| **Last updated** | `<YYYY-MM-DD>` |
| **Author / maintainer** | `<name>` |

---

## 2. Conventions & Terminology

<!-- HOW TO FILL: This section is mostly boilerplate. Keep it verbatim unless the repo
     introduces new terms. Add repo-specific terms at the end. -->

- **Environment** — a named, isolated dependency space materialized by a backend. Every
  environment has exactly one **purpose** (surface), one **backend**, and a structured
  attribute set (`app_type`, `frameworks`, `languages`, `packaging`). Environments are
  enumerated machine-readably in [§4.0](#40-environment-surface-enumeration).
- **Purpose (surface)** — the single role an environment serves. Exactly one of:

  | `purpose` | Meaning |
  |-----------|---------|
  | `run` | The deployable/executable artifact's **runtime** — "the thing that ships or executes in production." Its dependency closure is the app's runtime deps, not dev/test tooling. This is the surface `pyve package` / `pyve deploy` (future) operate on. *Disambiguator:* if you would ship or execute it in production, it is `run`; if it only supports development, it is `utility`. |
  | `test` | Hosts **test runners and test-only dependencies**; the env where a class of tests executes. `pyve test --env <name>` gates on `purpose == test`. *Disambiguator:* pytest / vitest / bats and their fixtures live here, never in `run`. |
  | `utility` | Hosts **development / orchestration tooling that is neither the app nor its tests** — formatters, linters, codegen, the `project-guide` host, LLM CLIs. The `root` env defaults to `utility`. *Disambiguator:* it makes development easier but never ships and is not a test surface. *Intended lifecycle (not yet wired):* survives `pyve purge` — it is your tooling, not the project's materialized output. |
  | `temp` | A **declared, reproducible, disposable** workspace that is part of a defined workflow (e.g. the `mktemp -d` sandbox a test harness spins up per run). Concretely: contents are **volatile**, the env is **safe to delete at any time**, and pyve may **prune** it. *The line is declared-vs-ad-hoc:* a reproducible part of a defined workflow → model it as `temp` and enumerate it; a one-off "hello world" poke → do **not** model it at all. *Intended lifecycle (not yet wired):* auto-prune. Today `temp` carries no special runtime behavior — it is a recognized value awaiting its lifecycle. |

  One environment = one purpose. If a single backing directory genuinely serves two
  purposes, declare two environments. (Lists are intentionally **not** supported — forcing
  a single choice keeps each environment's intent unambiguous. Revisit only if real
  friction cases emerge.)
- **Root development environment** — the environment activated at the repo root (pyve's
  primary environment, e.g. `.venv/` for the `venv` backend). Its purpose is typically
  `utility` — it hosts tooling, not necessarily the app or the tests.
- **Named test environment** — a `purpose: test` environment. The first/default is named
  `testenv`. Additional environments use distinct names (e.g. `testenv-integration`,
  `testenv-min`). Each maps to exactly one backend.
- **Backend** — the environment-management mechanism pyve uses to materialize an
  environment. Values are a **closed, Pyve-owned set** of specific mechanism names, never
  generic categories, and fall into three S6 categories: *project-virtualized* (`venv`,
  `micromamba`, `pnpm`, `npm`, `yarn`, `uv`, `poetry`, `conda`, `bun`, `deno` — per-project
  state + PATH activation), *cache-backed* (`cargo`, `go`, `bundler`, `swiftpm`, `xcode`,
  `android_sdk`, `gradle`, `maven`, `sbt`, `dotnet`, `conan`, `cmake` — shared cache +
  lockfile + a CLI build tool; an un-installable toolchain such as Xcode is recorded via the
  advisory `require_min_version` field, not by demoting the backend), and *check-only*
  (`homebrew`, `apt`, `docker`, `podman` — presence-verified, no pyve build). Closely-related
  mechanisms with leaky behavioral differences are kept as **separate flavored values** (e.g.
  `docker` vs `podman`, `npm` vs `pnpm` vs `yarn`) so each flavor's quirks are codified once
  instead of patched per repo. The special value **`none`** means there is no formal
  configuration mechanism — the environment is the bare OS, the implicit default for any
  surface pyve does not materialize. See [§3](#3-backend-catalog).
- **Structured attributes** — fixed-vocabulary descriptors recorded per environment. Each is
  a **closed set** (Pyve-owned, versioned); a value outside it is a spec violation. Values are
  either *implemented* (pyve acts on them today) or *advisory* (recorded + surfaced, never
  materialized):

  | Attribute | Closed vocabulary (use `none` when not applicable) |
  |-----------|----------------------------------------------------|
  | `app_type` | `api`, `cli`, `service`, `library`, `desktop`, `mobile`, `embedded`, `script`, `web`, `none` |
  | `packaging` | `container`, `static`, `server`, `serverless`, `package`, `binary`, `mobile_app`, `lock_bundle`, `none` |
  | `frameworks` (kind: app) | `sveltekit`, `flask`, `fastapi`, `django`, `react`, `vue`, `jupyter`, `marimo`, `spring`, `j2ee`, `kotlin_multiplatform`, `rails`, `sinatra`, `swiftui`, `uikit`, `none` |
  | `frameworks` (kind: test) | `pytest`, `vitest`, `jest`, `mocha`, `playwright`, `cypress`, `bats`, `rspec`, `minitest`, `xctest`, `junit` |
  | `frameworks` (kind: lint) | `ruff`, `mypy`, `black`, `isort`, `flake8`, `pylint`, `eslint`, `prettier`, `shellcheck`, `shfmt`, `ktlint`, `detekt`, `scalafmt`, `scalafix`, `google_java_format`, `rustfmt`, `clippy`, `gofmt`, `golangci_lint`, `rubocop`, `swiftlint`, `swiftformat`, `clang_format`, `clang_tidy` |
  | `languages` | `python`, `javascript`, `typescript`, `bash`, `c`, `cpp`, `c_sharp`, `java`, `kotlin`, `scala`, `go`, `swift`, `objective_c`, `rust`, `ruby` |

  Each framework's `kind` (app/test/lint) is *intrinsic* — looked up, not an authoring choice;
  one env's `frameworks` list may mix kinds. Two **advisory** fields may also appear per
  environment: **`require_min_version`** (`{ <tool>: "<ver>" }` — un-installable-toolchain
  pins, e.g. `{ xcode = "15.0" }`) and **`manual_steps`** (a string list of human-only seams
  pyve cannot drive, e.g. iOS signing). Both are surfaced in `pyve check` / `status`, never
  materialized.
- **Value class — *implemented* vs *advisory*.** Every value in every closed vocabulary is
  exactly one of two classes. **Implemented** = pyve has a real integration that acts on it
  today (materializes a backend, runs a verb, detects a framework). **Advisory** = recognized
  in the vocabulary but pyve takes no materializing action — it is *recorded* in `pyve.toml`
  and *surfaced* in `pyve check` / `pyve status`, never built, never an error. "Advisory" is
  the single home for every not-yet-implemented value (the runtime trichotomy's "known +
  no-op" class); an **unknown** value — outside the closed set — is a spec violation that
  hard-errors. Distance from Python/Node is irrelevant to the class; only whether pyve acts
  on it.
- **Framework `kind` (app / test / lint)** — every framework carries one *intrinsic* kind,
  looked up in Pyve's registry (never an authoring choice), governing which verb consumes it:
  - **app** — defines the application's serve/build shape; supplies the `serve` / `package`
    command (e.g. `flask` → `flask run`, `sveltekit` → the adapter build). A framework that
    supplies no command (a plain library) is **not** an app framework — it belongs in a
    dependency manifest, not here.
  - **test** — supplies the `test` command for a class of tests (e.g. `pytest`, `vitest`,
    `bats`).
  - **lint** — supplies a read-only code-quality command (linter, format-check, or
    type-check) for `pyve lint`, plus its fixable subset for `pyve lint --fix` (e.g. `ruff`,
    `mypy`, `eslint`, `shellcheck`).

  `none` = no framework activation (framework-less envs are first-class).
- **`packaging` — the artifact kind a materialize step produces** for an env (the *form*, not
  the destination):

  | `packaging` | Meaning |
  |-------------|---------|
  | `container` | An OCI image (Docker/Podman) — the deployable is a container. |
  | `static` | A static asset bundle (HTML/JS/CSS/Wasm) served by any web server / CDN — e.g. a SvelteKit static build, a Kotlin/JS or Compose-Web bundle. |
  | `server` | A long-running server process/artifact (a runnable app that listens), not containerized. |
  | `serverless` | A function/handler package for a serverless platform (zip / layer / bundle). |
  | `package` | A language package for a registry — a Python wheel, an npm tarball, a Ruby gem, a JVM jar. |
  | `binary` | A compiled standalone executable (a Rust/Go binary, a native CLI). |
  | `mobile_app` | A mobile app bundle — an iOS `.app`/`.ipa`, an Android `.apk`/`.aab`. (Absorbs the former `ios_app`/`android_app` framework entries.) |
  | `lock_bundle` | The deployable *is* the pinned lock set (the materialized dependency closure), not a built artifact. |
  | `none` | The env produces no materialized artifact (e.g. a `utility` tooling env). |

  Two things pyve deliberately does **not** model: **`build_target`** (the platform/runtime
  you build *for* — `linux/amd64`, a Rust target triple, a SvelteKit adapter) and
  **`deploy_target`** (the *destination* you ship to — GHCR, Vercel, PyPI). Pyve materializes
  the form; external CD ships it.
- **`app_type` — advisory descriptor of what the env's code *is*** (never materialized;
  surfaced in `check` / `status`):

  | `app_type` | Meaning |
  |------------|---------|
  | `api` | An HTTP/RPC API service consumed by other programs. |
  | `cli` | A command-line tool. |
  | `service` | A long-running non-web backend (worker, daemon, queue consumer). |
  | `library` | An importable package with no app of its own. |
  | `desktop` | A desktop GUI application. |
  | `mobile` | A mobile application. |
  | `embedded` | Firmware / a hardware-deployed artifact. |
  | `script` | A standalone script or automation. |
  | `web` | A browser-delivered web app/site. |
  | `none` | Not applicable (e.g. a tooling env). |
- **Dependency source class** — where a dependency comes from and how it is installed.
  This document recognizes the following classes (a single environment may mix several):

  | Class | Examples | Manifest / install mechanism |
  |-------|----------|------------------------------|
  | `pip` (PyPI) | `pytest`, `ruff`, `mypy` | `requirements.txt` / `requirements-dev.txt` |
  | `conda` (conda-forge) | `numpy`, `gdal` | `environment.yml` → `conda-lock.yml` |
  | `system` (OS / Homebrew / apt) | `shellcheck`, `bash`, `git` | `brew install` / `apt-get install` |
  | `vendored` (git-clone / submodule) | `bats-support`, `bats-assert` | `git clone` into a known path |
  | `runtime` (language interpreter) | `python`, `bash` | `.tool-versions` (asdf) / system |

- **Canonical backend** — a backend pyve materializes today (the *implemented* class).
  **Currently `venv` (default) and `micromamba` (Python plugin), plus `pnpm` / `npm` / `yarn`
  (Node plugin).** Every other value in the closed vocabulary is *advisory*: pyve records and
  surfaces it but does not yet materialize it. Advisory backends are **not** "proposed by the
  author" — the vocabulary is Pyve-owned and closed (see [§8](#8-backend-gaps--pyve-change-requests)).
- `<add repo-specific terms here, or write "None">`

---

## 3. Backend Catalog

<!-- HOW TO FILL: Keep the two canonical rows. Add a row for any non-canonical mechanism
     this repo actually relies on (e.g. "homebrew", "asdf-only"), marked status=proposed,
     and cross-reference §8. -->

| Backend | Status | Env location | Dependency manifest | Lock artifact | Init command |
|---------|--------|--------------|---------------------|---------------|--------------|
| `venv` | **canonical (default)** | `.pyve/envs/<name>/venv/` | `requirements.txt` | `requirements.txt` w/ `--hash` (pip-tools) | `pyve init` |
| `micromamba` | **canonical** | `.pyve/envs/<name>/conda/` | `environment.yml` | `conda-lock.yml` (`pyve lock`) | `pyve init --backend micromamba` |
| `pnpm` / `npm` / `yarn` | **canonical** (Node plugin) | `node_modules/` (+ store) | `package.json` | `pnpm-lock.yaml` / `package-lock.json` / `yarn.lock` | `pyve init` (Node-detected) |
| `<advisory-id>` | `advisory` | `<n/a — not materialized>` | `<manifest>` | `<lock>` | recorded + surfaced; see §8 |

**Default-backend assumption:** any environment may benefit from the `venv` backend, since
Python is a general-purpose workhorse for scripting/automation even in non-Python repos.
Choose a non-`venv` backend only with a stated reason (recorded per environment in §5).

**On `none`:** an environment whose dependencies have no formal configuration mechanism
(installed ad-hoc on the host, or materialized at runtime) uses backend `none` — the bare
OS. Use a specific name (`homebrew`, `apt`, ...) instead whenever a real mechanism exists,
even if pyve does not yet materialize it — it is an *advisory* value in the closed vocabulary
(record it in §4 with its advisory status; see §8 only if the mechanism is missing entirely).

**On container flavors:** `docker` and `podman` are **distinct backends that share a single
OCI `Dockerfile`** manifest — they diverge in *runtime behavior* (socket path, mount/SELinux
flags, rootless/userns, compose provider, BuildKit vs Buildah), not in the manifest. Pick
the flavor that matches the target host; pin the image by digest (`@sha256:...`) for
reproducibility. A container backend is also an *isolation level* and may nest another
backend (e.g. a `Dockerfile` that runs `pip install` or `apt-get`).

**Backend tiers (for orientation):** backends fall into rough tiers — *language-env*
(`venv`, `micromamba`, `npm`, `pnpm`, `yarn`: a project-local dependency dir + a runtime +
a lockfile), *host-package* (`homebrew`, `apt`: OS-level tools), and *isolation*
(`docker`, `podman`: an OS boundary that may nest the others). Node flavors `npm`/`pnpm`/
`yarn` share a `package.json` declaration but diverge in **both** lockfile
(`package-lock.json` / `pnpm-lock.yaml` / `yarn.lock`) and `node_modules` layout (hoisted vs
pnpm's symlinked store vs Yarn PnP), which is why they are separate flavors.

---

## 4. Environment Inventory

### 4.0 Environment Surface Enumeration

<!-- HOW TO FILL: This machine-readable block is the spine of the document. Enumerate
     EVERY environment surface the repo exposes — run, test, utility, temp. The root dev
     env is usually `utility`. List each environment exactly once; the §4.1 table and §5
     specs expand these entries. Use `none`/`N-A` for attributes that do not apply. -->

```yaml
spec_version: "3.0"                 # Pyve-owned; matches the template version
project: <repo_name>
description: <one-line description of the repo>
envs:
  <env_name>:                       # e.g. root, testenv, testenv-integration
    purpose: <run | test | utility | temp>
    backend: <venv | micromamba | pnpm | cargo | xcode | ...>   # closed vocabulary (§2)
    default: <true | false>         # true only for the default test env
    path: "."                       # plugin root; polyglot sub-path allowed (e.g. "src/frontend")
    languages: [<python | swift | ...>]
    frameworks: [<none | pytest | swiftui | ...>]
    packaging: <container | mobile_app | binary | none>
    app_type: <api | cli | mobile | ... | none>
    require_min_version: { <tool>: "<ver>" }   # optional, advisory (e.g. { xcode = "15.0" })
    manual_steps: ["<human-only step>"]        # optional, advisory (e.g. iOS signing)
```

### 4.1 Inventory Table

<!-- HOW TO FILL: One row per environment from §4.0. The root env is always first. Justify
     the TOTAL COUNT of test environments below; the per-category mapping lives in §6. -->

| # | Environment name | Purpose | Backend | Default? | App type | Frameworks | Languages |
|---|------------------|---------|---------|----------|----------|------------|-----------|
| 0 | `<root / repo root>` | `utility` | `<backend>` | n/a | `<app_type>` | `<frameworks>` | `<languages>` |
| 1 | `testenv` | `test` | `<backend>` | yes | `<app_type>` | `<frameworks>` | `<languages>` |
| 2 | `<testenv-...>` | `<purpose>` | `<backend>` | no | `<app_type>` | `<frameworks>` | `<languages>` |

**Why this many test environments:** `<1–3 sentences justifying the count: which axes of
variation (dependency set, framework, integration vs unit, runtime version, OS) require
separation, and why fewer environments would be insufficient or more would be redundant.>`

---

## 5. Environment Specifications

<!-- HOW TO FILL: Duplicate the entire "### 5.x" block once per environment listed in §4,
     including the root environment. Keep every subsection; use "N/A — reason" when empty. -->

### 5.0 Environment: `<root / repo root>` (purpose: `utility`)

- **Purpose (surface):** `utility` — `<what tooling it hosts>`.
- **Attributes:** app_type `<...>`; frameworks `<...>`; languages `<...>`.
- **Backend & rationale:** `<backend>` — `<why this backend>`.
- **Language runtime / pins:** `<interpreter + version, source: .tool-versions / system>`.
- **Bootstrap (one-time):**
  ```bash
  <commands to create the env, e.g. `pyve init`>
  ```
- **Install dependencies:**
  ```bash
  <commands, e.g. `pyve run pip install -r requirements.txt`>
  ```
- **Managed dependencies (`pip` / `conda`):**

  | Package | Version pin | Source class | Purpose |
  |---------|-------------|--------------|---------|
  | `<pkg>` | `<==x.y.z>` | `<pip/conda>` | `<why>` |

- **System / external dependencies (`system` / `vendored` / `runtime`):**

  | Dependency | Version | Source class | Install method | Why not in the managed env |
  |------------|---------|--------------|----------------|----------------------------|
  | `<tool>` | `<x.y>` | `<system/vendored/runtime>` | `<brew/apt/git clone/asdf>` | `<reason>` |

- **Lock / reproducibility strategy:** `<how exact versions are frozen & committed>`.
- **Verification (smoke test):**
  ```bash
  <command(s) proving the env is correctly provisioned, e.g. `pyve run project-guide --version`>
  ```
- **CI parity notes:** `<how CI reproduces this env, or "not used in CI">`.

---

### 5.1 Environment: `testenv` (purpose: `test`)

- **Purpose (surface):** `test` — default test environment.
- **Attributes:** app_type `<...>`; frameworks `<...>`; languages `<...>`.
- **Backend & rationale:** `<backend>` — `<why>`.
- **Test categories covered:** `<e.g. unit, lint>` (see §6).
- **Language runtime / pins:** `<...>`.
- **Bootstrap (one-time):**
  ```bash
  <e.g. `pyve testenv init`>
  ```
- **Install dependencies:**
  ```bash
  <e.g. `pyve testenv install -r requirements-dev.txt`>
  ```
- **Managed dependencies (`pip` / `conda`):**

  | Package | Version pin | Source class | Purpose |
  |---------|-------------|--------------|---------|
  | `<pkg>` | `<==x.y.z>` | `<pip/conda>` | `<why>` |

- **System / external dependencies (`system` / `vendored` / `runtime`):**

  | Dependency | Version | Source class | Install method | Why not in the managed env |
  |------------|---------|--------------|----------------|----------------------------|
  | `<tool>` | `<x.y>` | `<system/vendored/runtime>` | `<brew/apt/git clone>` | `<reason>` |

- **Lock / reproducibility strategy:** `<...>`.
- **How to run the tests this env owns:**
  ```bash
  <e.g. `bats tests/` or `pyve test`>
  ```
- **Verification (smoke test):**
  ```bash
  <command proving the test tooling is present, e.g. `bats --version && shellcheck --version`>
  ```
- **CI parity notes:** `<how CI reproduces this env — link to workflow steps>`.

<!-- HOW TO FILL: copy the 5.1 block as 5.2, 5.3, ... for every additional test env. -->

---

## 6. Test Coverage Matrix

<!-- HOW TO FILL: Map each test CATEGORY to the environment that owns it. Every category
     the codebase needs must map to exactly one environment. This is the evidence that the
     environment set is COMPLETE (every category covered) and EFFICIENT (no category is
     split across redundant envs). -->

| Test category | Tooling | Owning environment | Covered? | Notes |
|---------------|---------|--------------------|----------|-------|
| Static analysis / lint | `<e.g. shellcheck>` | `<env>` | `<yes/no>` | `<...>` |
| Unit tests | `<e.g. bats>` | `<env>` | `<yes/no>` | `<...>` |
| Integration tests | `<...>` | `<env>` | `<yes/no/N-A>` | `<...>` |
| Formatting | `<e.g. shfmt>` | `<env>` | `<yes/no/N-A>` | `<...>` |
| Packaging / distribution | `<e.g. brew audit>` | `<env>` | `<yes/no/N-A>` | `<...>` |
| `<other category>` | `<...>` | `<env>` | `<...>` | `<...>` |

**Completeness statement:** `<assert that every category the codebase requires is covered
by exactly one environment, and that no required category is missing.>`

---

## 7. Reproducibility & Bootstrapping

<!-- HOW TO FILL: Provide the minimal, copy-pasteable command sequence that takes a fresh
     clone to a fully testable state. This should be derivable directly from §5. -->

```bash
# Fresh-clone → fully testable, from the repo root:
<step 1: root env>
<step 2: testenv init + install>
<step 3: system/vendored deps>
<step 4: run verification smoke tests>
```

- **Files that must be committed for reproducibility:** `<requirements*.txt, environment.yml,
  conda-lock.yml, .tool-versions, .envrc, ...>`.
- **Files that must NOT be committed:** `<.venv/, .pyve/envs/, .pyve/testenv/, .env, ...>`.

---

## 8. Backend Gaps & Pyve Change-Requests

<!-- HOW TO FILL: The backend vocabulary is Pyve-owned and CLOSED — do NOT invent a backend
     value here. Three cases:
       1. The mechanism is in the closed vocabulary but still *advisory* (not yet
          materialized — e.g. `cargo`, `bundler`, `xcode`): record it in §4 with its advisory
          status; pyve surfaces it and you provision it manually for now. No §8 entry needed.
       2. The mechanism is NOT in the closed vocabulary at all: that is a Pyve change-request.
          File it against the pyve repo — pyve must add the value before any spec may use it.
       3. Neither applies: write "None — the closed vocabulary covers all needs." -->

| Need | In closed vocab? | Status today | Action |
|------|------------------|--------------|--------|
| `<mechanism>` | `<yes / no>` | `<advisory / absent>` | `<provision manually / file a pyve change-request>` |

---

## 9. Change Log & Approval

| Date | Version | Author | Change | Status |
|------|---------|--------|--------|--------|
| `<YYYY-MM-DD>` | `0.1` | `<name>` | Initial draft | `Draft` |
