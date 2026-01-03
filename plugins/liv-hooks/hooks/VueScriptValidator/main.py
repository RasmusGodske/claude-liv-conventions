#!/usr/bin/env python3
"""
VueScriptValidator - Validates Vue files use <script setup lang="ts">.

Uses Claude Agent SDK to analyze Vue file structure and ensure
it follows the required pattern.
"""

import asyncio
import os
import re
import sys

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    query,
)

from claude_hook_utils import (
    HookHandler,
    HookLogger,
    PreToolUseInput,
    PreToolUseResponse,
)


class VueScriptValidator(HookHandler):
    """Validates that Vue files use <script setup lang="ts">."""

    PROMPT_TEMPLATE = """
You are a Vue.js code validator. Analyze the following Vue component and determine if it follows the required script setup pattern.

## Requirements

The Vue file MUST have a script tag that:
1. Uses the Composition API with `setup`
2. Uses TypeScript with `lang="ts"`

Valid examples:
- `<script setup lang="ts">`
- `<script lang="ts" setup>`

Invalid examples:
- `<script>` (missing setup and lang)
- `<script setup>` (missing lang="ts")
- `<script lang="ts">` (missing setup)
- No script tag at all

## Vue File Content

```vue
{content}
```

## Your Task

Analyze the script tag in this Vue file. Respond with EXACTLY one of these formats:

If valid:
<decision>allow</decision>

If invalid:
<decision>block</decision>
<reason>Explanation of what's wrong and how to fix it</reason>

Do not include any other text outside these tags.
"""

    def __init__(self) -> None:
        log_file = os.environ.get("VUE_VALIDATOR_LOG")
        logger = HookLogger(log_file=log_file) if log_file else None
        super().__init__(logger=logger)
        self._verbose = os.environ.get("VUE_VALIDATOR_VERBOSE", "").lower() in ("1", "true")

    def pre_tool_use(self, input: PreToolUseInput) -> PreToolUseResponse | None:
        """Validate Vue files before they are written."""
        # Only validate Vue files
        if not input.file_path_matches("**/*.vue"):
            return None

        content = input.content
        if not content:
            return None

        # Quick check - if it obviously has the right pattern, allow it
        if self._has_valid_script_setup(content):
            self._log("Quick check passed - valid script setup found")
            return PreToolUseResponse.allow()

        # Use Claude Agent SDK for more nuanced validation
        self._log(f"Validating Vue file: {input.file_path}")

        try:
            result = asyncio.run(self._validate_with_agent(content))
            return result
        except Exception as e:
            self._log(f"Agent validation failed: {e}")
            # Fail open - don't block on errors
            return PreToolUseResponse.allow()

    def _has_valid_script_setup(self, content: str) -> bool:
        """Quick regex check for valid script setup pattern."""
        # Match <script with both setup and lang="ts" in any order
        pattern = r'<script\s+(?=.*\bsetup\b)(?=.*\blang=["\']ts["\'])[^>]*>'
        return bool(re.search(pattern, content, re.IGNORECASE))

    async def _validate_with_agent(self, content: str) -> PreToolUseResponse:
        """Use Claude Agent SDK to validate the Vue file."""
        prompt = self.PROMPT_TEMPLATE.format(content=content)

        agent_options = ClaudeAgentOptions(
            max_turns=1,  # Simple validation, no tools needed
            allowed_tools=[],  # No tools - just analyze the content
        )

        response_texts: list[str] = []

        async for message in query(prompt=prompt, options=agent_options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_texts.append(block.text)

        response_text = "\n".join(response_texts)
        return self._parse_response(response_text)

    def _parse_response(self, response_text: str) -> PreToolUseResponse:
        """Parse the validation response from Claude."""
        # Look for <decision>...</decision>
        decision_match = re.search(
            r"<decision>\s*(allow|block)\s*</decision>",
            response_text,
            re.IGNORECASE,
        )

        if decision_match:
            decision = decision_match.group(1).lower()

            if decision == "allow":
                self._log("Decision: ALLOW")
                return PreToolUseResponse.allow()

            # Decision is "block" - extract reason
            reason_match = re.search(
                r"<reason>(.*?)</reason>",
                response_text,
                re.IGNORECASE | re.DOTALL,
            )
            reason = reason_match.group(1).strip() if reason_match else None

            self._log(f"Decision: BLOCK - {reason}")
            return PreToolUseResponse.deny(
                reason or "Vue file must use <script setup lang=\"ts\">"
            )

        # Default: allow (don't block on unexpected response)
        self._log(f"Unexpected response format, defaulting to ALLOW")
        return PreToolUseResponse.allow()

    def _log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self._verbose:
            print(f"[VueScriptValidator] {message}", file=sys.stderr)
        if self.logger:
            self.logger.info(message)


if __name__ == "__main__":
    sys.exit(VueScriptValidator().run())
