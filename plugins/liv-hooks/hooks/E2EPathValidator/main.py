#!/usr/bin/env python3
"""
E2EPathValidator - Validates E2E test paths match Laravel routes.

Uses Claude Agent SDK to run `php artisan route:list` and validate
that E2E test directory structure matches the actual Laravel routes.

This hook uses Claude Agent SDK because it needs to:
1. Execute artisan commands to list routes
2. Analyze the output to match against test paths
This cannot be done with simple pattern matching.
"""

import asyncio
import os
import re
import sys
from pathlib import Path

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

NAMESPACE = "claude-liv-conventions"


# Path to the prompt template (relative to this file)
HOOK_DIR = Path(__file__).parent.resolve()
PROMPT_PATH = HOOK_DIR / "prompt.md"


class E2EPathValidator(HookHandler):
    """Validates E2E test paths match Laravel routes."""

    # Tools the agent needs for validation
    ALLOWED_TOOLS = [
        "Read",
        "Glob",
        "Grep",
        "Bash",  # For running php artisan route:list
    ]

    def __init__(self) -> None:
        super().__init__(
            logger=HookLogger.create_default(
                "E2EPathValidator",
                namespace=NAMESPACE,
            )
        )
        self._template: str | None = None

    @property
    def template(self) -> str:
        """Load and cache the prompt template."""
        if self._template is None:
            if not PROMPT_PATH.exists():
                raise FileNotFoundError(f"Prompt template not found: {PROMPT_PATH}")
            self._template = PROMPT_PATH.read_text()
        return self._template

    def pre_tool_use(self, input: PreToolUseInput) -> PreToolUseResponse | None:
        """Validate E2E test paths before files are written."""
        # Only validate Write tool calls
        if input.tool_name != "Write":
            return None

        # Only validate E2E test files
        if not self._is_e2e_test_file(input.file_path):
            return None

        self._log(f"Validating E2E path: {input.file_path}")

        try:
            result = asyncio.run(self._validate_with_agent(input.file_path))
            return result
        except Exception as e:
            self._log(f"Agent validation failed: {e}")
            # Fail open - don't block on errors
            return None

    def _is_e2e_test_file(self, file_path: str | None) -> bool:
        """Check if the file path is an E2E test file."""
        if not file_path:
            return False
        return "e2e/tests/" in file_path and file_path.endswith(".spec.ts")

    async def _validate_with_agent(self, file_path: str) -> PreToolUseResponse | None:
        """Use Claude Agent SDK to validate the path."""
        prompt = self.template.replace("{file_path}", file_path)

        # Get project root from environment or plugin root
        project_root = os.environ.get("CLAUDE_PROJECT_DIR", str(HOOK_DIR.parent.parent.parent.parent))

        agent_options = ClaudeAgentOptions(
            max_turns=10,
            cwd=project_root,
            allowed_tools=self.ALLOWED_TOOLS,
        )

        self._log(f"Running agent with cwd={project_root}")

        response_texts: list[str] = []

        async for message in query(prompt=prompt, options=agent_options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_texts.append(block.text)

        response_text = "\n".join(response_texts)

        if not response_text.strip():
            self._log("Empty response from agent")
            return None  # Allow on empty response

        return self._parse_response(response_text)

    def _parse_response(self, response_text: str) -> PreToolUseResponse | None:
        """Parse the validation response from Claude."""
        # Look for <decision>...</decision> tag
        decision_match = re.search(
            r"<decision>\s*(allow|block)\s*</decision>",
            response_text,
            re.IGNORECASE,
        )

        if decision_match:
            decision = decision_match.group(1).lower()

            if decision == "allow":
                self._log("Decision: ALLOW")
                return None

            # Decision is "block" - extract reason
            reason_match = re.search(
                r"<reason>(.*?)</reason>",
                response_text,
                re.IGNORECASE | re.DOTALL,
            )
            reason = reason_match.group(1).strip() if reason_match else None

            self._log(f"Decision: BLOCK - {reason}")
            return PreToolUseResponse.deny(
                reason or "E2E test path does not follow conventions."
            )

        # Fallback: check for ALLOW/BLOCK keywords
        response_upper = response_text.upper()
        if "BLOCK" in response_upper:
            self._log("Decision: BLOCK (keyword fallback)")
            return PreToolUseResponse.deny(response_text[:500])

        if "ALLOW" in response_upper:
            self._log("Decision: ALLOW (keyword fallback)")
            return None

        # Default: allow (don't block on unexpected response format)
        self._log(f"Unexpected response format, defaulting to ALLOW")
        return None

    def _log(self, message: str) -> None:
        """Log a message."""
        if self.logger:
            self.logger.info(message)


if __name__ == "__main__":
    sys.exit(E2EPathValidator().run())
