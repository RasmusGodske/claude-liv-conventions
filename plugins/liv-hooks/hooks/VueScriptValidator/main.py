#!/usr/bin/env python3
"""
VueScriptValidator - Validates Vue files use <script setup lang="ts">.

Uses fast regex matching to validate Vue file structure.
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


class VueScriptValidator(HookHandler):
    """Validates that Vue files use <script setup lang="ts">."""

    DENY_MESSAGE = """Vue files must use `<script setup lang="ts">`.

❌ Invalid:
  - `<script>` (missing setup and lang)
  - `<script setup>` (missing lang="ts")
  - `<script lang="ts">` (missing setup)

✅ Valid:
  - `<script setup lang="ts">`
  - `<script lang="ts" setup>`

Please update your script tag to include both `setup` and `lang="ts"`.
"""

    def __init__(self) -> None:
        super().__init__(
            logger=HookLogger.create_default(
                "VueScriptValidator",
                namespace=NAMESPACE,
            )
        )

    def pre_tool_use(self, input: PreToolUseInput) -> PreToolUseResponse | None:
        """Validate Vue files before they are written."""
        # Only validate Vue files
        if not input.file_path_matches("**/*.vue"):
            return None

        content = input.content
        if not content:
            return None

        self._log(f"Validating Vue file: {input.file_path}")

        # Check for valid script setup pattern
        if self._has_valid_script_setup(content):
            self._log("Valid script setup found")
            return None  # Allow

        # Check if there's any script tag at all
        if not self._has_any_script_tag(content):
            self._log("No script tag found - blocking")
            return PreToolUseResponse.deny(self.DENY_MESSAGE)

        # Has script tag but not valid setup
        self._log("Invalid script tag format - blocking")
        return PreToolUseResponse.deny(self.DENY_MESSAGE)

    def _has_valid_script_setup(self, content: str) -> bool:
        """Check for valid <script setup lang="ts"> pattern."""
        # Match <script with both setup and lang="ts" in any order
        pattern = r'<script\s+(?=.*\bsetup\b)(?=.*\blang=["\']ts["\'])[^>]*>'
        return bool(re.search(pattern, content, re.IGNORECASE))

    def _has_any_script_tag(self, content: str) -> bool:
        """Check if any script tag exists."""
        return bool(re.search(r'<script\b', content, re.IGNORECASE))

    def _log(self, message: str) -> None:
        """Log a message."""
        if self.logger:
            self.logger.info(message)


if __name__ == "__main__":
    sys.exit(VueScriptValidator().run())
