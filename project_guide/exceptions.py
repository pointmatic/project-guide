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


class ProjectGuidesError(Exception):
    """Base exception for all project-guide errors."""
    pass


class ConfigError(ProjectGuidesError):
    """Exception raised for configuration-related errors."""
    pass


class SyncError(ProjectGuidesError):
    """Exception raised for sync operation failures."""
    pass


class GuideNotFoundError(ProjectGuidesError):
    """Exception raised when a guide template is not found."""

    def __init__(self, guide_name: str, available_guides: list | None = None):
        self.guide_name = guide_name
        self.available_guides = available_guides or []

        message = f"Guide '{guide_name}' not found."
        if available_guides:
            message += f"\nAvailable guides: {', '.join(sorted(available_guides))}"

        super().__init__(message)
