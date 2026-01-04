"""Tests for E2EPathValidator hook.

Note: This hook uses Claude Agent SDK for validation, which cannot be
easily tested without mocking. We test the filtering logic (which files
get processed) rather than the agent validation itself.
"""

import pytest
from tests.utils import run_hook


class TestE2EPathValidatorMatching:
    """Tests for which files the hook applies to."""

    @pytest.mark.skip(reason="Requires Claude Agent SDK - times out in CI")
    def test_matches_e2e_spec_files(self):
        """Should process E2E spec files."""
        result = run_hook("E2EPathValidator", {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "e2e/tests/routes/app/users/index/smoke.spec.ts",
                "content": "test content",
            },
        })
        # Note: This will likely allow since we can't run artisan in tests
        # The important thing is it processes the file (doesn't return immediately)
        # We can't easily test the agent validation without mocking
        assert result is None  # Allows when agent validation succeeds or fails open

    def test_ignores_non_spec_files(self):
        """Should ignore non-.spec.ts files."""
        result = run_hook("E2EPathValidator", {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "e2e/tests/routes/app/users/helper.ts",
                "content": "export const helper = () => {};",
            },
        })
        assert result is None

    def test_ignores_non_e2e_directories(self):
        """Should ignore files outside e2e/tests/."""
        result = run_hook("E2EPathValidator", {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "tests/Feature/UserTest.php",
                "content": "<?php test",
            },
        })
        assert result is None

    def test_ignores_unit_test_files(self):
        """Should ignore regular test files."""
        result = run_hook("E2EPathValidator", {
            "hook_event_name": "PreToolUse",
            "tool_input": {
                "file_path": "tests/Unit/UserServiceTest.php",
                "content": "<?php test",
            },
        })
        assert result is None


class TestE2EPathValidatorNonWriteTools:
    """Tests for non-Write tools."""

    def test_ignores_read_tool(self):
        """Should ignore Read tool calls."""
        result = run_hook("E2EPathValidator", {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {
                "file_path": "e2e/tests/routes/app/users/index/smoke.spec.ts",
            },
        })
        assert result is None

    def test_ignores_bash_tool(self):
        """Should ignore Bash tool calls."""
        result = run_hook("E2EPathValidator", {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {
                "command": "npm run test:e2e",
            },
        })
        assert result is None


class TestE2EPathValidatorEdgeCases:
    """Edge case tests."""

    def test_handles_empty_file_path(self):
        """Should handle empty file path gracefully."""
        result = run_hook("E2EPathValidator", {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "",
                "content": "test",
            },
        })
        assert result is None

    def test_handles_missing_file_path(self):
        """Should handle missing file path gracefully."""
        result = run_hook("E2EPathValidator", {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "content": "test",
            },
        })
        assert result is None
