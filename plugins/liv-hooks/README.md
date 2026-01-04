# LIV Hooks Plugin

Pre-tool hooks that enforce Laravel/Inertia/Vue conventions.

## Included Hooks

### FormRequestBlocker

**Triggers:** `Write`, `Bash`

Blocks creation of Laravel FormRequest classes and guides towards using `spatie/laravel-data` DataClasses instead.

**Detects:**
- `php artisan make:request` commands
- Files written to `app/Http/Requests/`
- PHP classes extending `FormRequest`
- Imports of `Illuminate\...\FormRequest`

**Guidance provided:**
- Correct location: `app/Data/{Domain}/{Name}Data.php`
- DataClass pattern with constructor property promotion
- Controller usage example

### VueScriptValidator

**Triggers:** `Write`

Ensures Vue single-file components use the Composition API with TypeScript.

**Requires:**
- `<script setup lang="ts">` or `<script lang="ts" setup>`

**Detects:**
- Missing `setup` attribute
- Missing `lang="ts"` attribute
- Options API usage

### ControllerStructureValidator

**Triggers:** `Write`

Enforces nested directory structure for Laravel controllers.

**Blocks:**
- Controllers placed directly in `app/Http/Controllers/`

**Requires:**
- Controllers in domain subdirectories like `app/Http/Controllers/Users/`

### E2EPathValidator

**Triggers:** `Write` | **Uses:** Claude Agent SDK

Validates E2E test paths match actual Laravel routes.

**Checks:**
- Runs `php artisan route:list` to verify route exists
- Compares test directory structure to route path

**Note:** This hook uses Claude Agent SDK for complex validation and has a 120-second timeout.

### ControllerServiceLayerReminder

**Triggers:** `Write` (PostToolUse) | **Type:** Reminder (non-blocking)

Reminds Claude to use dedicated service classes for database mutations in controllers.

**Detects in store/update/destroy methods:**
- `$variable->save()`, `$variable->update()`, `$variable->delete()`
- `Model::create()`, `Model::updateOrCreate()`, etc.

**Note:** This is a PostToolUse hook - it provides guidance AFTER the write, not blocking.

## Adding a New Hook

1. Create a new directory under `hooks/`:
   ```
   hooks/
   └── MyNewHook/
       ├── pyproject.toml
       ├── main.py
       └── README.md
   ```

2. Create `pyproject.toml`:
   ```toml
   [project]
   name = "my-new-hook"
   version = "1.0.0"
   description = "What this hook does"
   requires-python = ">=3.10"
   dependencies = [
       "claude-hook-utils @ git+https://github.com/RasmusGodske/claude-hook-utils.git",
   ]
   ```

3. Create `main.py`:
   ```python
   #!/usr/bin/env python3
   import sys
   from claude_hook_utils import HookHandler, PreToolUseInput, PreToolUseResponse

   class MyNewHook(HookHandler):
       def pre_tool_use(self, input: PreToolUseInput) -> PreToolUseResponse | None:
           # Your validation logic
           if self._is_invalid(input):
               return PreToolUseResponse.deny("Explanation and guidance")
           return None

       def _is_invalid(self, input: PreToolUseInput) -> bool:
           # Check conditions
           return False

   if __name__ == "__main__":
       sys.exit(MyNewHook().run())
   ```

4. Create `README.md`:
   ```markdown
   # MyNewHook

   Brief description of what this hook does.

   ## What It Does

   Explain the validation logic.

   ## Why

   Explain why this convention matters.

   ## Examples

   Show examples of blocked vs allowed patterns.
   ```

5. Add hook to `plugin.json`:
   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Write",
           "hooks": [
             {
               "type": "command",
               "command": "cd ${CLAUDE_PLUGIN_ROOT}/hooks/MyNewHook && uv run python main.py",
               "timeout": 10
             }
           ]
         }
       ]
     }
   }
   ```

6. Update this README with a summary of your hook (in the "Included Hooks" section)

7. Test locally before committing:
   ```bash
   cd hooks/MyNewHook
   echo '{"hook_event_name":"PreToolUse","tool_name":"Write","tool_input":{"file_path":"test.php","content":"..."}}' | uv run python main.py
   ```

## Dependencies

Hooks use the [`claude-hook-utils`](https://github.com/RasmusGodske/claude-hook-utils) package which provides:

- `HookHandler` - Base class with dispatch logic
- `PreToolUseInput` - Input parsing with glob matching helpers
- `PreToolUseResponse` - Response builder (allow/deny/ask)
- `HookLogger` - Optional structured logging

Dependencies are automatically installed via `uv` on first run.
