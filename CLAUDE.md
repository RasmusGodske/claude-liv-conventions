# CLAUDE.md - Guide for AI Agents

## Project Overview

**claude-liv-conventions** is a Claude Code plugin that enforces opinionated conventions for Laravel/Inertia/Vue projects through pre-tool hooks.

**Purpose:** Intercept Claude's tool usage and guide it towards project best practices by blocking anti-patterns before they happen.

## Repository Structure

```
claude-liv-conventions/
├── .claude-plugin/
│   └── marketplace.json       # Marketplace catalog (lists available plugins)
├── plugins/
│   └── liv-hooks/
│       ├── .claude-plugin/
│       │   └── plugin.json    # Plugin manifest (hooks configuration)
│       ├── hooks/             # Individual hook implementations
│       │   ├── FormRequestBlocker/
│       │   └── VueScriptValidator/
│       └── README.md
├── tests/                     # pytest tests for hooks
├── .claude/
│   └── skills/
│       └── hook-creator/      # Skill for creating new hooks
├── CLAUDE.md                  # This file
└── README.md                  # User-facing documentation
```

## Creating New Hooks

**Always use the hook-creator skill when creating new hooks:**

```
/hook-creator
```

Or activate it by asking: "Create a new hook for X"

The skill provides:
- Complete hook template
- `claude-hook-utils` API reference
- Testing patterns
- Configuration steps

### Quick Reference

1. **Create hook directory:** `plugins/liv-hooks/hooks/{HookName}/`
2. **Add files:**
   - `pyproject.toml` - Dependencies (must include `claude-hook-utils`)
   - `main.py` - Hook implementation
3. **Update plugin.json:** Add hook to appropriate matcher
4. **Write tests:** Add tests to `tests/test_{hook_name}.py`
5. **Test locally:** Run `pytest tests/test_{hook_name}.py`

## Development Commands

```bash
# Install test dependencies
cd /path/to/claude-liv-conventions
uv sync

# Run all tests
uv run pytest tests/ -v

# Run specific hook tests
uv run pytest tests/test_form_request_blocker.py -v

# Test a hook manually
cd plugins/liv-hooks/hooks/FormRequestBlocker
echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"php artisan make:request Test"}}' | uv run python main.py
```

## Hook Architecture

### Input Flow
```
Claude invokes tool → Hook receives JSON via stdin → Validates → Returns decision
```

### Response Types
- **Allow:** `PreToolUseResponse.allow()` or return `None`
- **Deny:** `PreToolUseResponse.deny("reason with guidance")`
- **Ask:** `PreToolUseResponse.ask("question for user")`

### Key Principle
When denying, always provide **actionable guidance** - explain WHY it's blocked and HOW to do it correctly.

## Testing Hooks

Every hook must have tests. Test structure:

```python
# tests/test_{hook_name}.py
import pytest
from tests.utils import run_hook

class TestMyHook:
    def test_blocks_invalid_pattern(self):
        result = run_hook("MyHook", {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "bad/path.php", "content": "..."}
        })
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_allows_valid_pattern(self):
        result = run_hook("MyHook", {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "good/path.php", "content": "..."}
        })
        assert result is None  # None = no opinion = allow
```

## Adding a Hook to plugin.json

After creating a hook, register it in `plugins/liv-hooks/.claude-plugin/plugin.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",  // or "Bash", "Edit", etc.
        "hooks": [
          {
            "type": "command",
            "command": "cd ${CLAUDE_PLUGIN_ROOT}/hooks/MyHook && uv run python main.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**Important:** Always use `${CLAUDE_PLUGIN_ROOT}` for paths - plugins are cached/copied when installed.

## Existing Hooks

| Hook | Blocks | Guides Towards |
|------|--------|----------------|
| `FormRequestBlocker` | Laravel FormRequest classes | spatie/laravel-data DataClasses |
| `VueScriptValidator` | Vue files without proper setup | `<script setup lang="ts">` |

## CI/CD

- **Tests:** Run on every PR via GitHub Actions
- **Manual testing:** Use echo pipe method shown above

## Questions?

If unclear about patterns or conventions:
1. Check existing hooks for examples
2. Use the hook-creator skill
3. Look at tests for expected behavior
