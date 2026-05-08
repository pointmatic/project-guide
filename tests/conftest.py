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

import pytest


@pytest.fixture(autouse=True)
def _disable_auto_heal_hook(monkeypatch):
    """Suppress the group-level auto-heal hook by default in tests.

    The hook (Story P.b) fires before every CLI invocation and would prompt
    on any drifted state — most existing tests deliberately introduce drift
    to exercise downstream commands and would hang on the prompt under a
    non-TTY CliRunner stdin. Tests that exercise the hook itself opt out
    via ``monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)``.
    """
    monkeypatch.setenv("PROJECT_GUIDE_HEALING", "1")
