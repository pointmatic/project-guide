# Copyright (c) 2026 Pointmatic
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Runtime helpers for unattended / CI-friendly command execution.

The single entry point is :func:`should_skip_input`, which every future prompt
site in this package should call to decide whether it is safe to read from
stdin. It composes four independent signals (explicit flag, env var, CI env
var, TTY status) in a fixed priority order so that the behavior is predictable
across local shells, piped stdin, CI runners, and subprocess contexts.
"""

from __future__ import annotations

import os
import sys

import click

# Case-insensitive set of truthy env-var values. Everything else (including
# empty string and unset) falls through to the next signal.
_TRUTHY_ENV_VALUES = frozenset({"1", "true", "yes", "on"})


def _env_is_truthy(var_name: str) -> bool:
    """Return True if the named env var is set to a truthy value."""
    value = os.environ.get(var_name, "")
    return value.strip().lower() in _TRUTHY_ENV_VALUES


def _stdin_is_non_tty() -> bool:
    """Return True if stdin is not an interactive TTY.

    Handles the subprocess edge cases where ``sys.stdin`` may be ``None`` or a
    closed file object. In both cases we treat the caller as non-interactive,
    which is the safe default for unattended use.
    """
    try:
        return not sys.stdin.isatty()
    except (AttributeError, ValueError):
        # AttributeError: sys.stdin is None (some subprocess contexts).
        # ValueError: isatty() on a closed file raises ValueError.
        return True


def should_skip_input(flag: bool = False) -> bool:
    """Decide whether prompts should be skipped in favor of defaults.

    Priority (first match wins):

    1. Explicit ``flag`` argument (usually the ``--no-input`` CLI option).
    2. ``PROJECT_GUIDE_NO_INPUT`` env var set to a truthy value.
    3. ``CI`` env var set to a truthy value.
    4. Non-TTY stdin (piped input, subprocess, closed stdin, etc.).
    5. Otherwise: interactive — return ``False``.

    Truthy env values are matched case-insensitively against
    ``{"1", "true", "yes", "on"}``.
    """
    if flag:
        return True
    if _env_is_truthy("PROJECT_GUIDE_NO_INPUT"):
        return True
    if _env_is_truthy("CI"):
        return True
    return _stdin_is_non_tty()


def _require_setting(name: str, cli_flag: str, env_var: str) -> None:
    """Abort with exit 1 when a required setting has no value under --no-input.

    Call this from any future prompt site after determining that
    :func:`should_skip_input` returned ``True`` *and* no default is available
    for the setting. The exact message format is part of the contract and is
    exercised by the FR-L4 regression-guard test in ``tests/test_cli.py``.

    The message is intentionally actionable: it names the setting, the CLI
    flag the user can pass, and the env var they can export.
    """
    message = (
        f"{name} is required when --no-input is active. "
        f"Provide via --{cli_flag} or {env_var}."
    )
    raise click.ClickException(message)
