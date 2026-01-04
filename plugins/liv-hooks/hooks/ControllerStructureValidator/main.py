#!/usr/bin/env python3
"""
ControllerStructureValidator - Enforces nested controller directory structure.

This hook blocks controllers placed directly in app/Http/Controllers/ and guides
developers to organize controllers in nested domain folders.
"""

import re
import sys

from claude_hook_utils import (
    HookHandler,
    HookLogger,
    PreToolUseInput,
    PreToolUseResponse,
)

NAMESPACE = "claude-liv-conventions"


GUIDANCE_MESSAGE = """Controllers should be organized in nested domain folders, not placed directly in app/Http/Controllers/.

Instead of:
  ❌ app/Http/Controllers/UserController.php
  ❌ app/Http/Controllers/OrderController.php

Use nested domain folders:
  ✅ app/Http/Controllers/Users/UserController.php
  ✅ app/Http/Controllers/Orders/OrderController.php
  ✅ app/Http/Controllers/Auth/LoginController.php

This structure:
- Groups related controllers by domain/feature
- Improves code organization and discoverability
- Makes the codebase easier to navigate as it grows

Create the controller in an appropriate domain subdirectory."""


class ControllerStructureValidator(HookHandler):
    """Validates that controllers are placed in nested domain folders."""

    def __init__(self) -> None:
        super().__init__(
            logger=HookLogger.create_default(
                "ControllerStructureValidator",
                namespace=NAMESPACE,
            )
        )

    def pre_tool_use(self, input: PreToolUseInput) -> PreToolUseResponse | None:
        """Check for controllers placed directly in app/Http/Controllers/."""
        if input.tool_name == "Write":
            return self._check_write_path(input)
        elif input.tool_name == "Edit":
            return self._check_edit_path(input)
        return None

    def _check_write_path(self, input: PreToolUseInput) -> PreToolUseResponse | None:
        """Check if writing a controller directly to app/Http/Controllers/."""
        file_path = input.file_path or ""

        # Check if the file is a direct child of app/Http/Controllers/
        # Pattern: app/Http/Controllers/{filename}.php (no subdirectories)
        if self._is_flat_controller(file_path):
            self._log(f"Blocked: Flat controller structure: {file_path}")
            return PreToolUseResponse.deny(
                f"Do not place controllers directly in app/Http/Controllers/. {GUIDANCE_MESSAGE}"
            )

        return None

    def _check_edit_path(self, input: PreToolUseInput) -> PreToolUseResponse | None:
        """Check if editing a controller directly in app/Http/Controllers/."""
        file_path = input.file_path or ""

        # Only block if this looks like a new file being created
        # (we don't want to block edits to existing flat controllers)
        # For Edit tool, we'll be more lenient and only warn if it seems problematic
        return None

    def _is_flat_controller(self, file_path: str) -> bool:
        """
        Check if the file is a direct child of app/Http/Controllers/.

        Returns True for:
        - app/Http/Controllers/UserController.php
        - /path/to/app/Http/Controllers/TestController.php

        Returns False for:
        - app/Http/Controllers/Users/UserController.php
        - app/Http/Controllers/Auth/LoginController.php
        - app/Http/SomeOtherDir/Controller.php
        """
        # Normalize path separators
        normalized = file_path.replace("\\", "/")

        # Match: app/Http/Controllers/{filename}.php with no subdirectories
        # The pattern checks for app/Http/Controllers/ followed by a filename
        # that doesn't contain additional slashes (no subdirectories)
        pattern = r"app/Http/Controllers/[^/]+\.php$"

        if re.search(pattern, normalized):
            # Extra check: make sure it's actually a controller file
            filename = normalized.split("/")[-1]
            if "Controller.php" in filename or filename.endswith("Controller.php"):
                return True

        return False

    def _log(self, message: str) -> None:
        """Log a message if logger is available."""
        if self.logger:
            self.logger.info(message)


if __name__ == "__main__":
    sys.exit(ControllerStructureValidator().run())
