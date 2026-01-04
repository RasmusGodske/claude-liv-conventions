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
├── scripts/
│   └── update-hooks.sh        # Update claude-hook-utils in all hooks
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

# Update claude-hook-utils in all hooks
./scripts/update-hooks.sh

# Clean update (removes .venv for fresh install)
./scripts/update-hooks.sh --clean
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

### Key Principles

**1. Actionable Guidance**
When denying, always provide **actionable guidance** - explain WHY it's blocked and HOW to do it correctly.

**2. Performance First - Hooks Must Be Fast**

⚠️ **Hooks run on EVERY tool call.** A slow hook makes Claude feel sluggish for the user.

| Approach | Speed | Use When |
|----------|-------|----------|
| Pure Python (regex, string ops) | ✅ Fast (~ms) | Always prefer this |
| File system operations | ⚠️ Moderate | Only if necessary |
| External HTTP requests | ❌ Slow | Avoid if possible |
| Claude Agent SDK calls | ❌ Very slow | Only for complex analysis that can't be done with code |

**Guidelines:**
- **Prefer pure code:** If you can validate with regex, string matching, or AST parsing - do that
- **Avoid external calls:** Don't call Claude/LLMs unless absolutely necessary (e.g., reviewing code quality)
- **Fail fast:** Return early when conditions don't match
- **Set reasonable timeouts:** Use 10-30s timeouts, not minutes

```python
# ✅ GOOD - Fast regex check
def pre_tool_use(self, input: PreToolUseInput) -> PreToolUseResponse | None:
    if not input.file_path_matches("**/*.php"):
        return None  # Fast exit

    if re.search(r"class \w+ extends FormRequest", input.content):
        return PreToolUseResponse.deny("Use DataClasses instead")
    return None

# ❌ BAD - Slow LLM call for simple validation
def pre_tool_use(self, input: PreToolUseInput) -> PreToolUseResponse | None:
    # Don't do this for simple pattern matching!
    result = await query("Is this a FormRequest class?", content=input.content)
    ...
```

**When LLM calls ARE appropriate:**
- Code review hooks that need to understand intent/quality
- Complex analysis that can't be expressed as patterns
- Hooks that run infrequently (e.g., only on specific file types)

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
| `ControllerStructureValidator` | Flat controller file structure | Nested domain folders |
| `E2EPathValidator` | E2E test paths that don't match routes | Correct path structure (uses Claude Agent SDK) |

## CI/CD

- **Tests:** Run on every PR via GitHub Actions
- **Manual testing:** Use echo pipe method shown above

## Plugin Troubleshooting

### "No plugins installed" but marketplace shows plugins

**Symptom:**
- `/plugin` Installed tab shows "No plugins installed"
- `/hooks` shows "No matchers configured yet"
- But `~/.claude/plugins/installed_plugins.json` shows the plugin IS registered

**Root Cause:**
Claude Code UI reads from `installed_plugins_v2.json` but sometimes only `installed_plugins.json` exists. This is a known bug (GitHub issues #9426, #13509).

**Quick Fix:**
```bash
cp ~/.claude/plugins/installed_plugins.json ~/.claude/plugins/installed_plugins_v2.json
```
Then restart Claude Code.

**Clean Reinstall Fix:**
```bash
# Remove plugin cache and registry
rm -rf ~/.claude/plugins/cache/claude-liv-conventions
rm ~/.claude/plugins/installed_plugins.json
rm ~/.claude/plugins/installed_plugins_v2.json

# Restart Claude Code, then:
/plugin install liv-hooks@claude-liv-conventions --scope project
```

### Debugging Plugin Issues

1. Check registry: `cat ~/.claude/plugins/installed_plugins.json`
2. Check cache exists: `ls ~/.claude/plugins/cache/`
3. Check plugin.json: `cat ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/.claude-plugin/plugin.json`
4. Run with debug: `claude --debug`

### Key Plugin Files

| File | Purpose |
|------|---------|
| `~/.claude/plugins/installed_plugins.json` | Plugin registry (old format) |
| `~/.claude/plugins/installed_plugins_v2.json` | Plugin registry (UI reads this) |
| `~/.claude/plugins/known_marketplaces.json` | Configured marketplaces |
| `~/.claude/plugins/cache/` | Downloaded plugin files |
| `<project>/.claude/settings.json` | Project-level `enabledPlugins` |

## Questions?

If unclear about patterns or conventions:
1. Check existing hooks for examples
2. Use the hook-creator skill
3. Look at tests for expected behavior
