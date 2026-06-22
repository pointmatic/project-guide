> ⚠️ **FROZEN — DO NOT USE.** This mode is stale and not currently useful: improving it is **blocked on upstream Pyve work**, and its `env-dependencies.md` output does not round-trip through current Pyve. **Skip it** — go straight from `plan_tech_spec` to `plan_stories`. The mode stays listed (and this banner stays) until Pyve unblocks it and the mode is updated to match Pyve's current functionality and capabilities. See `docs/specs/project-essentials.md` → "`plan_envs` is frozen".

Define the **named environments** a Pyve-managed repo needs — the root development environment plus one or more test environments — enumerating each environment's purpose, backend, languages, frameworks, packaging, and advisory fields. The output is `docs/specs/env-dependencies.md`, the point-in-time env-spec artifact (a peer of `features.md` and `tech-spec.md`).

The high-level concept (why) lives in `concept.md`. The requirements and behavior (what) live in `features.md`. The architecture (how) lives in `tech-spec.md`. This mode adds **environment topology** — how many environments, with what backends and dependencies — as a discrete planning decision rather than something bootloaded into `plan_tech_spec` or discovered mid-implementation.

## Prerequisites

The approved `docs/specs/features.md` and `docs/specs/tech-spec.md` must exist before starting this mode. The mode infers environment requirements from those specs plus the codebase.

## Steps

1. **Read the existing specs.** Read `docs/specs/features.md` and `docs/specs/tech-spec.md` to understand scope, behavior, architecture, dependencies, and testing strategy. Also skim, where present, `README.md`, `CONTRIBUTING.md`, CI/CD workflows, and any container or packaging manifests. Infer env-shape signals from the codebase where docs are absent — test directories, build artifacts, the language mix, integration-test needs.

2. **Determine the environment topology.** Decide how many named environments the repo needs to develop, test, and deploy efficiently, effectively, and completely:
   - The **root** environment is the default first environment (purpose typically `utility` — it hosts tooling, not necessarily the app or the tests).
   - Add **test** environments for distinct dependency sets, frameworks, or integration-vs-unit separation. The first/default test env is usually named `testenv`.
   - Add **run** / **temp** environments only when a real, declared, reproducible surface calls for them.
   - For each environment, fix its `purpose`, `backend`, `languages`, `frameworks`, `packaging`, and `app_type` from the **closed vocabulary** (see the discipline note below). Prefer fewer environments; justify the count.

3. **Generate `docs/specs/env-dependencies.md`** using the artifact template at `docs/project-guide/templates/artifacts/env-dependencies.md` (installed by `project-guide init`; refreshed by `project-guide update`). Fill every `<placeholder>`, resolve every `<!-- HOW TO FILL -->` comment, and **omit the template's §0 How-To section** from the rendered output (same convention as `concept.md` / `features.md` / `tech-spec.md`).

4. **Present** the complete document to the developer for approval. Iterate as needed.

5. Done — proceed to the next mode (`plan_stories`). Environment decisions inform story scoping (which stories run in which environment), so implementation breakdown is the natural next step.

## Closed-vocabulary discipline

The `backend`, `languages`, `frameworks`, `packaging`, and `app_type` values come from the bundled template's §2 glossary, which is **vendored from Pyve at `spec_version: "3.0"`**. This vocabulary is **Pyve-owned and closed**:

- A value **outside** the closed set is a **spec violation**, not a creative choice. Never invent a value.
- Every in-vocabulary value is either *implemented* (Pyve materializes it today) or *advisory* (Pyve records and surfaces it but does not yet materialize it). When a requirement is met only by an *advisory* value, use it and record its advisory status — do not demote to a different backend to force materialization.
- If a needed mechanism is **missing from the vocabulary entirely**, that is a **Pyve change-request** (see the artifact's §8 Backend Gaps & Pyve Change-Requests) — file it against the Pyve repo; do not invent a value to paper over the gap.

See `docs/specs/project-essentials.md` → "Pyve env-spec vendored-template contract" for the cross-repo invariant governing this vocabulary and how it is refreshed when Pyve bumps `spec_version`.

{% include "modes/_header-sequence.md" %}
