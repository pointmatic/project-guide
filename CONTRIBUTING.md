<!--
Copyright (c) 2026 Pointmatic

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Contributing to project-guide

Thanks for your interest in contributing! This document covers everything
you need to set up a working development environment, run the test suite,
and submit a pull request that lands cleanly.

The README's Development and Contributing sections are quick-reference
summaries; this file is the canonical source for everything below.

---

## Dev environment

`project-guide` uses [pyve](https://pointmatic.github.io/pyve/) to manage
Python environments. The project follows pyve's **two-environment pattern**:
the runtime venv at `.venv/` holds the package itself, and a separate dev
testenv at `.pyve/testenv/venv/` holds test/lint tools (pytest, ruff,
mypy). Mixing the two creates subtle drift, so use the canonical commands
below — see `docs/project-guide/pyve-essentials.md` for the full rationale.

```bash
git clone https://github.com/pointmatic/project-guide.git
cd project-guide

# Main environment: editable install of the package itself.
pyve run pip install -e .

# Dev testenv: pytest, ruff, mypy, etc.
pyve testenv init                                    # one-time
pyve testenv install -r requirements-dev.txt
```

After this you can run the package as a CLI (`project-guide --version`)
and run the test suite (`pyve test`).

> **Why two environments?** Test tooling pollutes the runtime venv and
> breaks reproducibility ("works on my machine"). Keeping them separate
> means `pip install project-guide` produces the same environment every
> consumer gets, and `pyve test` always exercises the package against a
> known dev-tool set.

---

## Code style

- **Linting**: `ruff check` must pass. Use `ruff check --fix` for auto-fixable issues.
- **Formatting**: `ruff format` for consistent style.
- **Type checking**: `mypy` must run clean.

```bash
pyve testenv run ruff check project_guide tests
pyve testenv run ruff format project_guide tests
pyve testenv run mypy project_guide
```

---

## Tests

Run the full suite with `pyve test`:

```bash
pyve test                              # all tests
pyve test tests/test_cli.py            # one file
pyve test -k heal                      # name pattern
pyve test --cov=project_guide --cov-report=term-missing
```

**Coverage**: maintain at least **85%** line coverage for changed code.
The CI workflow uploads coverage to codecov on every push; PRs that drop
coverage substantially will get a comment.

**Mode-render regression test**: `tests/test_render.py::test_every_mode_renders_successfully`
is parametrized over every mode in `.metadata.yml` and renders each one
end-to-end. If you add a new mode template, add the mode to `.metadata.yml`
and this test will pick it up automatically — but please verify locally
before opening a PR.

---

## Pull request process

1. **Fork** the repository on GitHub.
2. **Branch** off `main` (e.g., `feat/heal-command`, `fix/gitignore-block`).
3. **Implement** the change. Keep PRs focused — one logical change per PR.
4. **Test** locally: `pyve test` must pass, and `ruff check` must be clean.
5. **PR**: open against `pointmatic/project-guide:main` with a description
   that explains the *why*, not just the *what*. Reference the issue or
   story it addresses if applicable.
6. **CI**: the GitHub Actions workflows (`ci.yml` and `test.yml`) run on
   every PR. **All checks must be green** before review.
7. **Review**: a maintainer will review, request changes if needed, and
   merge once approved.

> Branch protection on `main` is **not yet enabled** — the project is still
> in solo-maintainer mode. The PR workflow is the expected path for outside
> contributors regardless, and branch protection will flip on as soon as
> there are multiple regular contributors.

---

## Substantive contributions

For non-trivial changes (new features, refactors, behavioral changes), the
recommended path is to **scope the work via stories** before opening a PR.
`project-guide` uses itself to plan its own work — the cycle modes
`code_direct` and `code_test_first` walk through:

1. Read `docs/specs/stories.md` for the next planned story.
2. If the change isn't covered, draft a story (or a phase plan if it spans
   multiple stories) and discuss in an issue first.
3. Implement against the story's checklist; submit the PR with the story
   ID in the commit message and PR title.

This is not a hard requirement for small fixes (typos, doc tweaks, obvious
bugs), but it's strongly recommended for anything that touches the CLI
surface, the mode metadata schema, or the rendering pipeline.

---

## Release process

Releases are cut by the maintainer at end-of-phase per the **Version
Cadence** rule documented at the top of `docs/specs/stories.md`:

1. Land all stories in the phase via direct commits or merged PRs.
2. Run `project-guide bump-version <X.Y.Z>` — this updates
   `pyproject.toml`, `project_guide/version.py`, and adds the
   `## [X.Y.Z] - <date>` heading to `CHANGELOG.md`.
3. Use `project-guide mode plan_production_phase` (post-1.0) to negotiate
   the bump magnitude when applicable.
4. Tag and push: `git tag vX.Y.Z && git push origin vX.Y.Z`.
5. Create a GitHub Release from the tag — this triggers
   `.github/workflows/publish.yml`, which builds and uploads the package
   to PyPI.

Phase-bundled releases (the current default for Phase P) ship one version
at end-of-phase. The story that owns the bump is marked in
`docs/specs/stories.md`; intermediate stories run unversioned.
