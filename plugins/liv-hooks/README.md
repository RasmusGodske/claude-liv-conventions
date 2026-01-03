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

## Adding a New Hook

1. Create a new directory under `hooks/`:
   ```
   hooks/
   └── MyNewHook/
       ├── pyproject.toml
       └── main.py
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

4. Add hook to `plugin.json`:
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

5. Test locally before committing:
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
