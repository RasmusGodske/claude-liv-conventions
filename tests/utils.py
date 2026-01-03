"""Test utilities for running hooks."""

import json
import subprocess
from pathlib import Path
from typing import Any


# Path to the hooks directory
HOOKS_DIR = Path(__file__).parent.parent / "plugins" / "liv-hooks" / "hooks"


def run_hook(hook_name: str, input_data: dict[str, Any]) -> dict[str, Any] | None:
    """
    Run a hook with the given input and return its output.

    Args:
        hook_name: Name of the hook directory (e.g., "FormRequestBlocker")
        input_data: Dictionary to send as JSON input to the hook

    Returns:
        Parsed JSON output from the hook, or None if no output (allow)

    Raises:
        subprocess.CalledProcessError: If the hook process fails
        FileNotFoundError: If the hook directory doesn't exist
    """
    hook_dir = HOOKS_DIR / hook_name

    if not hook_dir.exists():
        raise FileNotFoundError(f"Hook directory not found: {hook_dir}")

    # Run the hook with JSON input via stdin
    result = subprocess.run(
        ["uv", "run", "python", "main.py"],
        cwd=hook_dir,
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Check for errors (non-zero exit that isn't a hook deny)
    if result.returncode != 0 and result.returncode != 2:
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            result.stdout,
            result.stderr,
        )

    # Parse output if present
    stdout = result.stdout.strip()
    if not stdout:
        return None

    return json.loads(stdout)


def make_write_input(file_path: str, content: str) -> dict[str, Any]:
    """Create a PreToolUse input for the Write tool."""
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Write",
        "tool_use_id": "test-tool-use-id",
        "tool_input": {
            "file_path": file_path,
            "content": content,
        },
    }


def make_bash_input(command: str) -> dict[str, Any]:
    """Create a PreToolUse input for the Bash tool."""
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_use_id": "test-tool-use-id",
        "tool_input": {
            "command": command,
        },
    }


def make_edit_input(file_path: str, old_string: str, new_string: str) -> dict[str, Any]:
    """Create a PreToolUse input for the Edit tool."""
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_use_id": "test-tool-use-id",
        "tool_input": {
            "file_path": file_path,
            "old_string": old_string,
            "new_string": new_string,
        },
    }


def assert_denied(result: dict[str, Any] | None, reason_contains: str | None = None) -> None:
    """Assert that the hook denied the request."""
    assert result is not None, "Expected deny but got None (allow)"
    assert "hookSpecificOutput" in result, f"Missing hookSpecificOutput: {result}"

    output = result["hookSpecificOutput"]
    assert output.get("permissionDecision") == "deny", f"Expected deny but got: {output}"

    if reason_contains:
        reason = output.get("permissionDecisionReason", "")
        assert reason_contains.lower() in reason.lower(), (
            f"Expected reason to contain '{reason_contains}' but got: {reason}"
        )


def assert_allowed(result: dict[str, Any] | None) -> None:
    """Assert that the hook allowed the request (None or explicit allow)."""
    if result is None:
        return  # None means no opinion = allow

    if "hookSpecificOutput" in result:
        decision = result["hookSpecificOutput"].get("permissionDecision")
        assert decision in ("allow", None), f"Expected allow but got: {decision}"
