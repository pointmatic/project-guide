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


class ProjectFileNotFoundError(ProjectGuidesError):
    """Exception raised when a tracked project file is not found."""

    def __init__(self, file_name: str, available_files: list | None = None):
        self.file_name = file_name
        self.available_files = available_files or []

        message = f"File '{file_name}' not found."
        if available_files:
            message += f"\nAvailable files: {', '.join(sorted(available_files))}"

        super().__init__(message)


class MetadataError(ProjectGuidesError):
    """Exception raised for metadata parsing or validation errors."""
    pass


class RenderError(ProjectGuidesError):
    """Exception raised for template rendering failures."""
    pass


class ActionError(ProjectGuidesError):
    """Exception raised when an artifact action (create/modify/archive) fails."""
    pass
