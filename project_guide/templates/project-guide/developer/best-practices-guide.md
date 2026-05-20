# Best Practices Guide — LLM-Assisted Development

This guide documents key learnings and best practices for LLM-assisted software development. Keep this minimal and focused on actionable principles.

---

## Methodology — Extreme Programming (XP)

### Lineage

The practices in this guide — cycle modes with approval gates, mandatory test-first in `debug`, single-story-per-commit discipline, the spike concept, small steps with frequent verification, pair-style developer/LLM collaboration — derive from **Extreme Programming (XP)** as articulated by Kent Beck and the C3 team in the late 1990s. project-guide is not a from-scratch invention; it is an adaptation of XP to the specifics of working with an LLM as a collaborator.

### Why XP fits LLM-assisted development

Each core XP practice counters a known LLM failure mode:

- **Test-first** counters "looks right" hallucination. The test pins behavior before the code is written; "the code passes the tests" replaces "the code looks plausible" as the acceptance criterion.
- **Small steps with frequent verification** matches the LLM's context-window economics. Long uninterrupted runs accumulate drift; short steps with a checkpoint each (commit, test pass, approval gate) make the drift catchable.
- **Spikes for explicit uncertainty handling** give the LLM a legitimate action when the path forward is unknown. Without the spike concept, the LLM either fabricates a plausible-looking implementation or stalls. A spike is the structured "I don't know yet — let's find out" move.
- **Documented decisions (stories, ADRs, project-essentials)** forestall invisible scope creep. Each unit of work has a name and a checklist; "scope crept" is a divergence the developer can see at the approval gate.
- **Pair-style collaboration with rotating driver/navigator roles** is literally the developer/LLM relationship. The LLM drives at the keyboard; the developer navigates at the approval gate. Both roles are explicit, not aspirational.

The implication is conservative: when an XP rule feels inconvenient, the failure mode it counters is probably the reason it exists. Drifting back to non-XP defaults (skipping tests, batching work, implementing without a story) reintroduces the failure modes XP was designed to prevent.

### References

- Kent Beck, *Extreme Programming Explained: Embrace Change* (Addison-Wesley, 1st ed. 1999; 2nd ed. with Cynthia Andres 2004).
- Ron Jeffries, Ann Anderson, Chet Hendrickson, *Extreme Programming Installed* (Addison-Wesley, 2000).

---

## Development Modes

### Velocity Mode vs. Production Mode

**Problem:** Applying production-grade processes too early slows down initial development. Conversely, maintaining velocity practices in production projects creates security and quality risks.

**Best Practice:**

Recognize and adapt to two distinct development modes:

**Velocity Mode** (Early Development):
- **When:** Phases A-F (foundation through initial testing)
- **Practices:**
  - Direct commits to main branch
  - Minimal process overhead
  - Version bump per story (v0.1.0 → v0.2.0 → v0.3.0)
  - Focus on feature completion and iteration speed
  - Skip branch protection, PR reviews, security policies
- **Commit messages:** `"Story A.a: v0.1.0 Hello World"`

**Production Mode** (Mature Development):
- **When:** After CI/CD phase is complete and core functionality works
- **Practices:**
  - Branch protection enabled (PRs required)
  - CI checks mandatory before merge
  - Security hardening (Dependabot, SECURITY.md, CONTRIBUTING.md)
  - Bundled releases with multiple stories (v0.8.0 includes J.a-J.d)
  - Trusted publishers for package registries
  - Code review requirements
- **Commit messages:** `"Story J.c: Branch Protection & Repo Settings"`
- **Release process:** Tag-based automation with GitHub Releases

**The Switch:**
- Occurs when enabling branch protection (typically in the CI/CD phase)
- Marked by adding security and contribution policies
- From this point forward, all changes go through PRs
- Version numbers may skip (v0.7.1 → v0.8.0 bundling multiple stories)

**How to Audit:**
- Check if branch protection is enabled → should be ON for production projects
- Look for CONTRIBUTING.md and SECURITY.md → missing indicates velocity mode
- Review recent commits → direct to main = velocity, via PRs = production
- Check version history → incremental (v0.1→v0.2) = velocity, bundled releases = production

**Rationale:** Velocity mode maximizes learning and iteration speed when exploring solutions. Production mode maximizes stability and security when users depend on the project. Using the wrong mode at the wrong time either slows progress unnecessarily or creates technical debt.

**How project-guide enforces the switch:** the `plan_production_phase` mode (mandatory for every phase once the package is at v1.0.0+) walks the developer through the **Production-readiness checklist** above as step 2 — branch protection, SECURITY.md, CONTRIBUTING.md, Dependabot, trusted publisher, mandatory CI, bundled-release cadence. The mode does not proceed past unmet items without explicit developer override. `plan_phase` (pre-1.0 only) halts and recommends `plan_production_phase` if the manifest reports `version >= 1.0.0`. End-of-phase, the developer ships via `project-guide bump-version <X.Y.Z>` (the deterministic helper that updates `pyproject.toml` / `<package>/version.py` / `CHANGELOG.md`).

---

## Hello World First — Spike Early, Spike Often

"Spike" is a canonical XP practice (Beck 1999) — a **time-boxed, throwaway effort to reduce uncertainty**. The deliverable is the documented outcome (decision, path forward, ruled-out alternatives), not production code. Code produced during a spike is either deleted or quarantined in `scripts/` / `notebooks/` and never imported by the package.

Agile literature recognizes three structurally distinct spike flavors. Each addresses a different category of uncertainty; picking the right flavor depends on **what kind of question** you can't answer without running an experiment.

### Integration spike

**Question answered:** Will the external systems connect end-to-end?

Wires the full critical path together before any production modules are written. Hardcoded values, no abstraction, no config — the script's job is to prove the integration boundary actually works under realistic conditions (real credentials, real device, real network).

**Triggers** — add an integration spike whenever you introduce:

- A new external service or API
- A new hardware accelerator (GPU, MPS, TPU)
- A new async or concurrency framework
- A new ML framework or model serving path

**Placement in `stories.md`:**

- **A.c by default** — the third story of the project, after A.a (scaffolding) and A.b (Hello World). The three foundation stories are structurally distinct: A.a proves the **package** is wired up; A.b proves the **runtime** is wired up; A.c proves the **integration boundary** is wired up.
- **First story of any later phase that introduces a new integration boundary** — same shape, scoped to whatever the phase is introducing.

**Example — shape of a good integration spike:**

```
Script: scripts/spike_<integration_name>.py
───────────────────────────────────────────
1. Acquire the resource (connect to API, load dataset, initialize client)
2. Confirm the environment (log version, device, credentials, region, etc.)
3. Execute the critical path (one real operation end-to-end)
4. Assert the output is sane (type check, range check, non-empty)
5. Print a human-readable summary

If this script runs and produces sensible output, the integration is validated.
If it fails, you find out now — before writing the modules that depend on it.
```

### Architectural spike

**Question answered:** Will this design or pattern actually work? What is the probability of implementation success?

Beck's original spike flavor (Beck 1999). Throwaway code written to test a design choice **before** committing to it as the project's architecture. Used when the *implementation pattern* itself is uncertain — e.g., "can I express this state machine cleanly with async generators, or do I need a class-based approach?" or "will this serialization scheme survive round-trips under realistic load?"

**Triggers** — add an architectural spike when:

- A design choice is non-obvious and committing to it would touch many files
- Two or more candidate patterns are credible and you can't pick on paper
- The implementation pattern depends on a runtime characteristic you can't predict (performance, memory, threading semantics)

**Output:** the throwaway implementation **plus** a documented pattern decision inside the spike's story. The decision is the deliverable; the code is the evidence.

### Investigation spike

**Question answered:** Is there a viable path at all? What are the options?

A time-boxed research effort into an uncertain path. Often produces **no code** — the deliverable is a written hypothesis, the steps undertaken, and a resolution (no action / candidate found / deferred). Used most commonly in cycle modes (especially `debug`) when even the *existence* of a fix path is unclear.

**Triggers** — add an investigation spike when:

- The problem isn't yet defined well enough to write a story for the fix
- Multiple plausible causes exist and prematurely picking one would waste effort
- The work might be impossible or out-of-scope and you need to confirm before scoping a real story

**Output:** a documented outcome — usually 3–10 lines stating the hypothesis, the experiment, and what was learned. Spike box-boundary: when the time-box expires, the spike ends regardless of whether a fix path was found.

### What spikes are NOT

- A prototype to keep and clean up — delete or clearly archive after the spike passes
- A substitute for proper tests — they prove a question's answer, not that production code is correct
- An excuse to skip the production implementation — they are a gate, not a destination

### Why spikes early, spikes often

**Rationale:** The cost of discovering a broken assumption at A.c (three stories in) is near zero. The cost of discovering it at D.b (ten stories in) is a potential rewrite. Spikes are cheap insurance against the most expensive category of failure — the kind that doesn't show up until the dependent code already exists.

### Foundation-story structure

Every project starts with three structurally distinct foundation stories that each prove one thing:

| Story | Name | What it proves |
|-------|------|----------------|
| **A.a** | Scaffolding | The package builds, lints, and the manifest is wired up. Executed in `scaffold_project` mode. |
| **A.b** | Hello World | The runtime works — the smallest possible executable artifact (e.g., a CLI that prints `__version__`, an HTTP server that returns 200 on `/`, a script that imports the package and runs `main()`). |
| **A.c** | Integration spike | The external integration boundary works — the throwaway end-to-end spike described above. |

These are three concerns, not one — collapsing Hello World into the spike (or omitting scaffolding because "the package manager handles it") consistently surfaces ambiguity that the 3-story shape resolves. The canonical 3-story foundation is enforced by `plan_stories` mode.

---

## CI/CD Setup

### Always Validate Locally Before Creating CI Infrastructure

**Problem:** Creating CI workflows before ensuring the codebase passes linting/formatting leads to immediate CI failures and wasted effort.

**Best Practice:**

1. **Run linting and formatting checks locally FIRST:**
   ```bash
   # Python projects
   ruff check .
   ruff format --check .
   pytest tests/
   
   # JavaScript projects
   npm run lint
   npm run format:check
   npm test
   
   # Go projects
   go fmt ./...
   go vet ./...
   go test ./...
   ```

2. **Fix all errors** before proceeding

3. **Then** create CI workflow files (`.github/workflows/ci.yml`, etc.)

4. **Then** create supporting configs (`codecov.yml`, etc.)

**Rationale:** CI workflows should **verify** already-clean code, not be the **first discovery** of linting issues. This prevents false starts and ensures the first CI run will succeed.

---

## Code Quality

### Maintain Clean Code Throughout Development

**Problem:** Accumulating linting errors during feature development creates technical debt and blocks CI adoption.

**Best Practice:**

- Run linting checks after **every significant change** (not just at the end)
- Fix linting errors **immediately** rather than deferring them
- Use auto-fix options when safe: `ruff check . --fix`, `npm run lint -- --fix`
- Configure your editor to show linting errors in real-time

**Rationale:** Small, incremental fixes are easier than batch-fixing 100+ errors at once.

---

## Testing

### Test Changes Immediately After Implementation

**Problem:** Implementing multiple features before running tests makes it harder to isolate failures.

**Best Practice:**

- Run tests after completing **each story or sub-task**
- Verify tests pass before moving to the next feature
- If tests fail, fix immediately before continuing

**Rationale:** Faster feedback loops reduce debugging time and prevent cascading failures.

---

## Documentation

### Keep Documentation In Sync With Code

**Problem:** Outdated documentation misleads developers and wastes time.

**Best Practice:**

- Update relevant docs (README, tech specs, API docs) **in the same commit** as code changes
- Mark completed tasks in `stories.md` as `[Done]` immediately after verification
- Document breaking changes prominently

**Rationale:** Documentation drift is harder to fix retroactively than maintaining it continuously.

---

## Version Control

### Commit Logical Units of Work

**Problem:** Large, unfocused commits make code review difficult and rollbacks risky.

**Best Practice:**

- One story/feature per commit when possible
- Include both code and documentation changes in the same commit
- Write clear commit messages that reference story IDs: `"Story H.d: Service error classification and exception migration"`

**Rationale:** Atomic commits make history readable and enable selective rollbacks.

---

## Dependency Management

### Verify Dependencies Before Adding Them

**Problem:** Adding untested dependencies can introduce breaking changes or compatibility issues.

**Best Practice:**

- Test new dependencies locally before adding to `pyproject.toml`/`package.json`
- Check compatibility with existing dependencies
- Document why each dependency is needed (in comments or docs)
- Prefer well-maintained, widely-used libraries

**Rationale:** Dependency issues are easier to prevent than to debug after integration.

---

## Error Handling

### Design Error Handling Before Implementation

**Problem:** Retrofitting error handling into existing code is error-prone and incomplete.

**Best Practice:**

- Define error types and codes **before** implementing features
- Document which errors are retryable vs. permanent
- Test error paths explicitly, not just happy paths

**Rationale:** Error handling is a first-class concern, not an afterthought.

---

## Logging and User Output

### Separate User-Facing Output from Operator Logs

**Problem:** LLMs (and humans) often conflate human-readable CLI output with structured operational logs, sending the wrong message to the wrong channel. A `console.print(...)` call emitting "stage X took longer than expected" looks helpful in the terminal but is unfilterable downstream — log aggregators, alerting rules, and dashboards can't see it. Conversely, dumping JSON logs into the user's terminal makes the CLI feel hostile.

**Best Practice:**

In Python projects:

- **`rich` is for users** — CLI output, progress bars, tables, colored hints, error explanations a human reads in their terminal. Lives on stdout/stderr.
- **`logging` is for operators** — structured, filterable, level-tagged events for log aggregation, monitoring, and post-hoc debugging. Use the stdlib `logging` module with a JSON formatter (or equivalent structured target).
- **Warnings and operational concerns** ("stage X took longer than expected", "fell back to slower path", "retried 3 times") belong on the **logging** channel, not in `console.print(...)`. The wrong instinct is to reach for the user-facing channel because the message *feels* user-facing — but if downstream tooling can't filter or alert on it, it might as well not exist.
- **Errors that block the user** belong on both channels: a `rich`-styled human-readable message on stderr *and* a structured log entry the operator can correlate with the rest of the system.

The same channel discipline applies in other ecosystems (`chalk`/`pino` in Node, `pterm`/`slog` in Go, `console`/`tracing` in Rust) — two libraries because two audiences.

**Rationale:** Two channels exist because they serve two audiences with different access patterns. Humans read terminals once. Operators query logs across thousands of runs. Mixing the channels makes both audiences worse off — the human gets noisier output, and the operator can't find what they need.

---

## Open Source Sustainability

### GitHub Sponsors & Funding

**Problem:** Open-source maintainers often struggle to sustain projects long-term without financial support, leading to burnout or project abandonment.

**Best Practice:**

For public open-source projects, consider setting up funding options to support ongoing maintenance and development.

**Why Enable Funding?**
- Supports maintainer time and effort
- Signals project value to the community
- Enables faster feature development and bug fixes
- Covers infrastructure costs (hosting, domains, CI minutes)
- Builds a sustainable open-source ecosystem

**Setup Steps:**

1. **Create `.github/FUNDING.yml`** in your repository root
2. **Choose funding platforms:**
   - **GitHub Sponsors** (integrated into GitHub, no fees)
   - **Patreon** (recurring monthly support)
   - **Ko-fi** (one-time or monthly donations)
   - **Buy Me a Coffee** (simple one-time donations)
   - **Open Collective** (transparent fund management)
   - **Custom URLs** (PayPal, Stripe, etc.)

3. **Add your usernames to the config:**
   ```yaml
   # .github/FUNDING.yml
   github: [your-github-username]
   patreon: your-patreon-username
   ko_fi: your-kofi-username
   custom: ["https://www.buymeacoffee.com/yourname"]
   ```

4. **GitHub displays a "Sponsor" button** on your repository page

**Best Practices:**
- **Be transparent** about how funds are used
- **Keep it optional** and non-intrusive (never paywall features)
- **Update sponsors** on progress and roadmap
- **Offer perks** (optional): early access, priority support, sponsor recognition
- **Set realistic goals** and communicate them clearly
- **Thank sponsors** publicly (with permission) or privately

**When to Enable:**
- **Early projects:** Wait until the project has proven value and users
- **Mature projects:** Enable when you're committed to long-term maintenance
- **Popular projects:** Essential for sustainability at scale

**Rationale:** Sustainable open-source development requires resources. Funding options allow users who benefit from your work to contribute back, creating a healthier ecosystem for everyone.

---

## General Principles

### Measure Twice, Cut Once

- **Validate assumptions** before implementing
- **Run checks locally** before creating CI
- **Test incrementally** rather than in large batches
- **Review changes** before marking stories complete

### Fail Fast, Fix Fast

- Don't defer error fixes to "later"
- Address linting/test failures immediately
- Small, frequent corrections beat large batch fixes

### Document As You Go

- Update docs in the same commit as code
- Record decisions and rationale
- Keep stories.md current with progress

---

## Adding New Best Practices

When you discover a new pattern or anti-pattern:

1. Document it here in a new section
2. Keep the description **minimal** (problem, practice, rationale)
3. Focus on **actionable** guidance, not theory
4. Use **concrete examples** when helpful

This guide should grow organically as the project evolves.
