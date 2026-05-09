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

# Security Policy

## Supported Versions

Only the latest minor release line receives security fixes. Earlier minor
releases are not patched; upgrade to the latest minor to stay supported.

| Version | Supported          |
| ------- | ------------------ |
| 2.6.x   | :white_check_mark: |
| < 2.6   | :x:                |

## Reporting a Vulnerability

Please report security issues privately via **GitHub Security Advisories**:

> https://github.com/pointmatic/project-guide/security/advisories/new

This routes the report straight to the maintainers and creates a private
advisory thread you can use to share details, reproduction steps, and any
proposed fix. **Do not file public GitHub issues for security reports.**

### What to expect

- **Acknowledgement**: within ~7 days. Given the project's solo-maintainer
  status, there is no hard SLA on fix time — but every report gets a real
  human reply, not a form auto-response.
- **Disclosure**: coordinated through the same GitHub advisory thread. Once
  a fix has shipped, the advisory is published and the reporter is credited
  (unless they prefer to remain anonymous).

## Threat model

`project-guide` is a small Python CLI that reads bundled Jinja2 templates
from its own package and writes rendered output into the user's project
directory. Concretely:

- The package contains **no secrets, credentials, or API keys**.
- All operations are **local-filesystem only**. There are **no network
  calls** at runtime — no telemetry, no remote template fetches, no
  auto-update checks.
- The only state read or written outside the project's own working tree is
  `~/.config`-style config (none today) and standard `pip` / package
  installation paths managed by the user's Python environment.

The relevant attack surface is therefore narrow: malicious templates inside
a tampered installation could render unexpected content into the user's
repo, and a malicious `.project-guide.yml` could redirect writes to an
unexpected `target_dir`. Both are mitigated by running `project-guide` only
from a trusted install (`pip install project-guide`) and reviewing
`.project-guide.yml` before running commands.
