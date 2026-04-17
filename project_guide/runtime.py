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
import re
import sys
import tomllib
from pathlib import Path

import click

# Matches a bare Jinja-style placeholder: `{{var}}`, `{{ var }}`, `{{  var  }}`.
# This is exactly the shape that lenient-undefined ``__str__`` implementations
# emit when an undefined variable is rendered. Shared by ``render.py`` (go.md
# output) and ``actions.py`` (fresh artifact output) so every Jinja render
# path in the package can validate through the same contract.
UNRENDERED_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z_]\w*)\s*\}\}")

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


def _resolve_setting(
    name: str,
    cli_value: bool | str | None,
    env_var: str,
    config_key: str,
    config: object | None,
    default: bool | str,
) -> bool | str:
    """Resolve a setting via the documented four-level priority chain.

    Priority (first match wins):

    1. ``cli_value`` — the value passed via CLI flag (skipped when ``None``).
    2. ``env_var`` — environment variable name; for bool settings, matched
       case-insensitively against ``_TRUTHY_ENV_VALUES``; for str settings,
       returned as-is.
    3. ``config_key`` — attribute name on the ``config`` object (typically a
       loaded :class:`Config` instance).  Skipped when ``config`` is ``None``
       or the attribute is absent.
    4. ``default`` — the fallback value; also determines the return type
       (``bool`` when ``isinstance(default, bool)``, ``str`` otherwise).
    """
    is_bool = isinstance(default, bool)

    # 1. CLI value
    if cli_value is not None:
        return cli_value

    # 2. Env var
    raw_env = os.environ.get(env_var)
    if raw_env is not None:
        if is_bool:
            return raw_env.strip().lower() in _TRUTHY_ENV_VALUES
        return raw_env

    # 3. Config key
    if config is not None:
        config_val = getattr(config, config_key, None)
        if config_val is not None:
            return config_val  # type: ignore[no-any-return]

    # 4. Default
    return default


def _detect_project_name_from_pyproject(cwd: Path | None = None) -> str | None:
    """Return the ``[project].name`` from ``pyproject.toml`` if present.

    Returns ``None`` when the file is absent, unparseable, or lacks the
    ``project.name`` field. Non-Python projects can extend this helper later
    by adding additional manifest lookups (e.g., ``package.json``, ``Cargo.toml``).
    """
    root = cwd if cwd is not None else Path.cwd()
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return None
    try:
        with pyproject.open("rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return None
    name = data.get("project", {}).get("name")
    if isinstance(name, str) and name:
        return name
    return None


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
