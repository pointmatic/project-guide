# Spec: `project-guide init --no-input` mode

> **Status:** Implemented in v2.2.0–v2.2.1 (2026-04-11). Drafted for the [`project-guide`](https://pointmatic.github.io/project-guide/) project, not pyve. Lives here as the upstream dependency spec for Phase G Story G.c (`pyve init` integration with `project-guide`). Idempotent re-run shipped in v2.2.0 (Story L.a); `--no-input` flag, env-var and non-TTY auto-detection, and the `_require_setting()` contract shipped in v2.2.1 (Story L.b).
>
> **Why this matters to pyve:** Pyve's G.c story wires `project-guide` installation into `pyve init` as a post-environment hook. Pyve cannot ship that integration until `project-guide init` has a `--no-input` mode — otherwise the post-hook hangs waiting for stdin in CI and in the no-TTY paths inside `pyve init`'s subprocess execution.

## Goal

Allow `project-guide init` to run unattended (in CI, scripts, or as a post-hook from `pyve init`) without hanging on prompts. Output is unaffected — this spec only changes whether the tool reads from stdin, not what it writes to stdout/stderr.

## Trigger logic (priority order — first match wins)

| Input | Behavior |
|---|---|
| `--no-input` flag | Do not read stdin |
| `PROJECT_GUIDE_NO_INPUT=1` env var | Do not read stdin |
| `CI=1` env var | Do not read stdin (auto-detect) |
| `stdin` not a TTY (`sys.stdin.isatty() == False`) | Do not read stdin (auto-detect) |
| Otherwise | Interactive (current behavior) |

The auto-detection cases (CI, non-TTY stdin) make this a "just works" experience for `pyve init` and pretty much every CI system without requiring users to remember a flag.

**Naming rationale — why `--no-input`, not `--yes` or `--non-interactive`.** Two problems with the alternatives:

1. **`--yes` encodes an assumption** that every future prompt's expected answer will be affirmative — which breaks the moment a prompt has a sensible "no" default (e.g., `Overwrite existing files?`) or a free-form value (e.g., `Project name?`). `--no-input` describes the *mechanism* (don't read stdin) rather than the *answer* (always yes), so it scales to any prompt regardless of the shape of its default.
2. **`--non-interactive` is ambiguous.** Some readers understand it to mean "don't read stdin"; others hear it as "suppress output too." This spec only affects input, not output. `--no-input` removes the ambiguity — the flag name says precisely what the flag does, matches [`pip`'s precedent](https://pip.pypa.io/en/stable/cli/pip/#cmdoption-no-input) (which `project-guide` sits next to in users' workflows), and shares one conceptual model with the non-TTY stdin auto-detect.

## Behavior when `--no-input` is active

- **Intent:** run without a human at the keyboard. Do not block on stdin. Do not change stdout/stderr behavior.
- **Core rule:** use defaults where sensible; provide CLI flags, env vars, or config-file settings for cases that require parameters.
  - Every interactive prompt resolves to its default value. Defaults may be Y, N, a string, or anything else — `--no-input` is agnostic about *what* the default is, it only asserts that one exists and will be used.
  - For prompts that collect user-specific values without a sensible default (project name, author, license, etc.), add a corresponding CLI flag, env var, or config-file setting so the user has a way to provide the value without stdin. Auto-derivation from `pyproject.toml`, git config, etc. is also acceptable where reliable.
  - If a required value is missing *and* has no defaulted/derived source, exit non-zero with a precise error stating *which* setting is missing and *how* to provide it. Don't guess, don't force an affirmative answer, don't silently invent values.

## CLI surface

```
project-guide init [OPTIONS]

Options:
  --target-dir TEXT     Target directory for the guide
  --force               Overwrite existing files
  --no-input            Do not read from stdin; use defaults where sensible.
                        Fail loudly if any prompt has no default.
                        (Also auto-enabled by CI=1 or non-TTY stdin.)
  --help                Show this message and exit
```

No short form for `--no-input` — explicit is better for a flag that changes execution semantics.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Initialized successfully (or already initialized — idempotent no-op) |
| 1 | Required setting missing when `--no-input` is active (with clear remediation hint) |
| 2 | Other initialization error (filesystem, permissions, etc.) |

## Idempotency

A second `project-guide init` (with or without `--no-input`) on an already-initialized project must be a no-op success, unless `--force` is given. This is critical for the `pyve init` post-hook — re-running `pyve init` shouldn't re-prompt or re-overwrite.

## Failure surface

| Failure | Behavior |
|---|---|
| Required setting missing with `--no-input` active | Exit 1 with `ERROR: <setting> is required when --no-input is active. Provide via --<flag> or PROJECT_GUIDE_<VAR>.` |
| Target directory unwritable | Exit 2 with the OS error message |
| `--force` not given but files exist | Exit 0 silently (idempotent) — only the *forced* path overwrites |

## Examples

```bash
# Pyve post-hook (auto-detects no TTY → uses defaults, no flag needed)
pyve init                              # internally calls: project-guide init

# Explicit CI use
project-guide init --no-input

# CI auto-detected
CI=1 project-guide init

# Specify target dir with --no-input
project-guide init --no-input --target-dir docs/

# Force re-init with --no-input
project-guide init --no-input --force
```

## Open question for project-guide implementation

**What does `project-guide init` prompt for today?** Specifically — are any of the prompts for values that *can't* be defaulted (project name, license choice, author, etc.)? That answer determines whether the spec needs to add config-file fallback for those settings, or whether "just use defaults" is enough.

- If the prompts are all "yes/no, default Y" style, the spec above is complete and can be implemented as-is.
- If any prompts collect free-form values without sensible defaults, those need a parallel CLI flag (or env var, or config file lookup) so users have a way to provide them when `--no-input` is active.

## Pyve integration plan (downstream consumer)

Once `project-guide` ships this change, Pyve's G.c story (FR-G2 in [phase-g-ux-improvements-plan.md](phase-g-ux-improvements-plan.md)) will:

1. Install `project-guide` into the project env via `pip install project-guide` (idempotent: no-op if `python -c 'import project_guide'` succeeds).
2. Run `project-guide init` as a subprocess. Since pyve invokes it without a TTY (no `bash -i`, no piped stdin), the non-TTY auto-detect kicks in and defaults are used. **Pyve does not need to pass `--no-input` explicitly** — the auto-detect handles it.
3. If `project-guide init` exits 1 (missing required setting), pyve treats it the same as a failed `pip install project-guide`: warn with the underlying stderr and a `--no-project-guide` hint, then continue. `pyve init` itself still exits 0.

**No version coupling.** Pyve will not pin a `project-guide` version. The non-TTY auto-detect is a behavior change in `project-guide`, not a CLI surface change pyve depends on, so older `project-guide` versions just degrade gracefully (they prompt, the prompt fails on closed stdin, pyve catches the non-zero exit and warns).
