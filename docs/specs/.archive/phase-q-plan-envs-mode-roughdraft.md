I am defining a formal process for a Pyve-managed Git repository (also supported with `project-guide`) to improve the structured configuration and management of its multiple exposure surfaces. The goal is to formalize dependencies into separate "named environments". Each environment is a distinct context with one purpose (`run`, `test`, `utility`, `temp`) — a "surface" in the Pyve framework, with its own set of dependencies, that can be exposed and exercised in isolation.

The default, first environment is the `root` environment. Additional environments are optional; the first test environment is often named `testenv` (a Python `venv` by default), but may use a different name and a non-`venv` backend.

Review whatever development, testing, and deployment documentation the repo provides — e.g. `docs/specs/features.md`, `docs/specs/tech-spec.md`, `README.md`, `CONTRIBUTING.md`, CI/CD workflows, and any container or packaging manifests — and infer from the codebase where such docs are absent. This Pyve capability is not yet released and the repo's existing test/sandbox setup may be incomplete; regardless, treat comprehensive develop/test/deploy isolation as the goal and determine how many named environments (by dependencies, frameworks, and integration-test needs) are necessary to develop, test, and deploy the codebase efficiently, effectively, and completely. The backend vocabulary is Pyve-owned and closed: where a requirement is not met by an *implemented* (canonical) backend, use the closed vocabulary's matching *advisory* value if one exists (template §2) and record it with its advisory status; only if no vocabulary value fits at all is it a Pyve change-request (template §8) — never invent a backend value.

Generate the following document using `path/to/env-dependencies-template.md` as the structure, inserting the repository's name (from the repo directory / `.project-guide.yml` / `pyve` config) into the filename:
- `docs/specs/env-dependencies.md`

Fill every `<placeholder>`, resolve every `<!-- HOW TO FILL -->` comment, and omit the template's How-To section.

Two phases:
1. Generate the dependency doc for this repo from the template.
2. I review the doc and we iterate, if needed, until it is "approved".