---
name: hook-creator
description: Guide for creating Claude Code hooks in the liv-conventions plugin. This skill should be used when users want to create a new hook to validate, block, or guide Claude's tool usage (Write, Bash, Edit, etc.). Covers the HookHandler pattern, PreToolUseInput/Response APIs, glob matching, plugin.json configuration, and testing.
---

# Claude Code Hook Creator

This skill provides guidance for creating Claude Code hooks for the liv-conventions plugin.

## Overview

This plugin uses Python-based hooks with the `claude-hook-utils` package to validate and guide Claude's tool usage. Hooks intercept tool calls (Write, Bash, Edit, etc.) and can allow, deny, or ask for confirmation.

## Package: claude-hook-utils

GitHub: https://github.com/RasmusGodske/claude-hook-utils

### Installation

```toml
# pyproject.toml
[project]
name = "my-hook-name"
version = "1.0.0"
description = "Description of what the hook does"
requires-python = ">=3.10"
dependencies = [
    "claude-hook-utils @ git+https://github.com/RasmusGodske/claude-hook-utils.git",
]
```

### Core Classes

```python
from claude_hook_utils import (
    HookHandler,      # Base class - extend this
    HookLogger,       # Optional logging
    PreToolUseInput,  # Input for PreToolUse hooks
    PreToolUseResponse,  # Response builder
    PostToolUseInput,    # Input for PostToolUse hooks (if needed)
    PostToolUseResponse, # Response for PostToolUse hooks (if needed)
)
```

## Hook Structure

### Directory Layout

```
plugins/liv-hooks/hooks/{HookName}/
├── pyproject.toml
├── main.py
├── README.md
└── .venv/  (created by uv, gitignored)
```

### Basic Template

```python
#!/usr/bin/env python3
"""
{HookName} - Brief description of what this hook does.

Longer description explaining the purpose and behavior.
"""

import os
import sys

from claude_hook_utils import (
    HookHandler,
    HookLogger,
    PreToolUseInput,
    PreToolUseResponse,
)


class {HookName}(HookHandler):
    """{Brief description}."""

    def __init__(self) -> None:
        # Optional: Enable logging via environment variable
        log_file = os.environ.get("{HOOK_NAME}_LOG")
        logger = HookLogger(log_file=log_file) if log_file else None
        super().__init__(logger=logger)

    def pre_tool_use(self, input: PreToolUseInput) -> PreToolUseResponse | None:
        """Validate tool usage before execution."""
        # Return None to allow (no opinion)
        # Return PreToolUseResponse.allow() to explicitly allow
        # Return PreToolUseResponse.deny("reason") to block
        # Return PreToolUseResponse.ask("question") to ask user

        # Example: Only process certain files
        if not input.file_path_matches("**/*.php"):
            return None

        # Your validation logic here
        if self._is_invalid(input):
            return PreToolUseResponse.deny("Explanation of why and how to fix")

        return None  # Allow by default

    def _is_invalid(self, input: PreToolUseInput) -> bool:
        """Helper method for validation logic."""
        # Implement your check
        return False


if __name__ == "__main__":
    sys.exit({HookName}().run())
```

## PreToolUseInput API

### Properties

```python
input.tool_name      # str: "Write", "Bash", "Edit", etc.
input.tool_input     # dict: Raw tool input
input.tool_use_id    # str: Unique ID for this tool use
input.hook_event_name  # str: "PreToolUse"

# Convenience properties (from tool_input)
input.file_path      # str | None: tool_input.get("file_path")
input.content        # str | None: tool_input.get("content")
input.command        # str | None: tool_input.get("command") - for Bash
```

### Glob Matching

```python
# Check if file_path matches glob patterns
input.file_path_matches("**/*.php")
input.file_path_matches("**/*.vue", "**/*.ts")  # Multiple patterns (OR)
input.file_path_matches("app/Http/Requests/**/*.php")

# Check any path against globs
input.path_matches("/some/path", "**/*.php")
input.path_matches(input.tool_input.get("old_path"), "**/*.php")
```

## PreToolUseResponse API

```python
# Allow the tool use
PreToolUseResponse.allow()
PreToolUseResponse.allow(reason="Validation passed")

# Deny/block the tool use
PreToolUseResponse.deny("Explanation of why this is blocked and how to fix it")

# Ask the user for confirmation
PreToolUseResponse.ask("Are you sure you want to do X?")

# Modify the tool input (advanced)
response = PreToolUseResponse.allow()
response = response.with_updated_input(content="modified content")
```

## Plugin.json Configuration

Add hooks to `plugins/liv-hooks/.claude-plugin/plugin.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "cd ${CLAUDE_PLUGIN_ROOT}/hooks/{HookName} && uv run python main.py",
            "timeout": 10
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "cd ${CLAUDE_PLUGIN_ROOT}/hooks/{HookName} && uv run python main.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**IMPORTANT:** Always use `${CLAUDE_PLUGIN_ROOT}` for paths - plugins are cached/copied when installed.

### Matcher Options

- `"Write"` - File creation/overwrite
- `"Edit"` - File edits
- `"Bash"` - Shell commands
- `"Read"` - File reads
- `"Glob"` - File searches
- `"Grep"` - Content searches

## Existing Hooks (Examples)

### 1. FormRequestBlocker
**Purpose:** Blocks FormRequest creation, guides to DataClasses
**Detects:**
- `php artisan make:request` commands
- Files in `app/Http/Requests/`
- Code extending `FormRequest`

**Location:** `plugins/liv-hooks/hooks/FormRequestBlocker/`

### 2. VueScriptValidator
**Purpose:** Ensures Vue files use `<script setup lang="ts">`
**Detects:** Vue files without proper script setup
**Speed:** Fast (pure regex)

**Location:** `plugins/liv-hooks/hooks/VueScriptValidator/`

### 3. ControllerStructureValidator
**Purpose:** Enforces nested directory structure for controllers
**Detects:** Controllers placed directly in `app/Http/Controllers/`
**Speed:** Fast (pure regex)

**Location:** `plugins/liv-hooks/hooks/ControllerStructureValidator/`

### 4. E2EPathValidator
**Purpose:** Validates E2E test paths match Laravel routes
**Detects:** E2E test files that don't match actual routes
**Uses:** Claude Agent SDK (runs `php artisan route:list`)
**Speed:** Slow (120s timeout) - appropriate for complex validation

**Location:** `plugins/liv-hooks/hooks/E2EPathValidator/`

## Creating a New Hook - Checklist

1. [ ] Create directory: `plugins/liv-hooks/hooks/{HookName}/`
2. [ ] Create `pyproject.toml` with `claude-hook-utils` dependency
3. [ ] Create `main.py` with HookHandler subclass
4. [ ] Create `README.md` with description, examples, and configuration
5. [ ] Run `uv sync` to install dependencies
6. [ ] Test manually with echo JSON pipe
7. [ ] Write tests in `tests/test_{hook_name}.py`
8. [ ] Run `uv run pytest tests/test_{hook_name}.py -v`
9. [ ] Add hook to `plugins/liv-hooks/.claude-plugin/plugin.json`
10. [ ] Update `plugins/liv-hooks/README.md` with a summary of the new hook

## Testing Hooks

### Manual Testing

```bash
cd plugins/liv-hooks/hooks/{HookName}

# Test Write tool
echo '{"hook_event_name":"PreToolUse","tool_name":"Write","tool_input":{"file_path":"test.php","content":"<?php class Test {}"}}' | uv run python main.py

# Test Bash tool
echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"php artisan make:request Test"}}' | uv run python main.py

# Expected outputs:
# - No output = allow (returned None)
# - JSON with permissionDecision = explicit response
```

### Automated Tests

Create tests in `tests/test_{hook_name}.py`:

```python
import pytest
from tests.utils import run_hook

class TestMyHook:
    """Tests for MyHook."""

    def test_blocks_invalid_pattern(self):
        """Should block when invalid pattern detected."""
        result = run_hook("MyHook", {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "bad/path.php",
                "content": "invalid content"
            }
        })
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "guidance" in result["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_allows_valid_pattern(self):
        """Should allow when valid pattern detected."""
        result = run_hook("MyHook", {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "good/path.php",
                "content": "valid content"
            }
        })
        assert result is None  # None = no opinion = allow

    def test_ignores_unrelated_files(self):
        """Should not process files outside its scope."""
        result = run_hook("MyHook", {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "unrelated.txt",
                "content": "anything"
            }
        })
        assert result is None
```

Run tests:

```bash
# From repository root
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_my_hook.py -v

# Specific test
uv run pytest tests/test_my_hook.py::TestMyHook::test_blocks_invalid_pattern -v
```

## Tips

1. **Return None for "no opinion"** - Only return a response when you have something to say
2. **Fail open** - If validation errors occur, allow rather than block (don't break Claude)
3. **Clear deny messages** - Explain WHY it's blocked and HOW to fix it
4. **Use glob matching** - `input.file_path_matches()` handles complex patterns
5. **Keep timeouts short** - Hooks run on every tool call, 10s is usually enough
6. **Test before committing** - Use both manual and automated tests
7. **Check existing hooks** - Use them as templates for new hooks
