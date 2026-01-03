# Claude LIV Conventions

A Claude Code plugin that enforces opinionated conventions for **L**aravel/**I**nertia/**V**ue projects.

## Why This Exists

When using Claude Code for Laravel/Inertia/Vue development, Claude may suggest patterns that don't align with project conventions. For example:
- Creating `FormRequest` classes when the project uses `spatie/laravel-data` DataClasses
- Writing Vue components without `<script setup lang="ts">`
- Placing files in flat directory structures instead of nested domain folders

This plugin intercepts Claude's tool usage and:
1. **Blocks** anti-patterns before they happen
2. **Guides** Claude towards the correct approach with helpful messages

## What It Does

The plugin provides **pre-tool hooks** that run before Claude executes tools like `Write`, `Edit`, or `Bash`. Each hook validates the intended action and can:
- **Allow** - Let the action proceed
- **Deny** - Block the action with an explanation of the correct approach
- **Ask** - Prompt the user for confirmation

### Included Hooks

| Hook | Purpose |
|------|---------|
| `FormRequestBlocker` | Blocks Laravel FormRequest creation, guides to DataClasses |
| `VueScriptValidator` | Ensures Vue files use `<script setup lang="ts">` |

## How It Works

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Claude wants   │────▶│  Hook runs   │────▶│  Action allowed │
│  to write file  │     │  validation  │     │  or blocked     │
└─────────────────┘     └──────────────┘     └─────────────────┘
```

1. Claude Code invokes a tool (e.g., `Write` to create a file)
2. The plugin's hooks receive the tool input (file path, content, etc.)
3. Hooks validate against conventions and return allow/deny/ask
4. If denied, Claude receives guidance on the correct approach

Hooks are Python scripts using the [`claude-hook-utils`](https://github.com/RasmusGodske/claude-hook-utils) package for standardized input/output handling.

## Requirements

- **Python 3.10+** - For running hook scripts
- **uv** - Python package manager (hooks auto-install dependencies on first run)

If you're using a devcontainer, ensure these are installed in your container.

## Installation

### 1. Add the marketplace

```bash
/plugin marketplace add github.com/RasmusGodske/claude-liv-conventions
```

### 2. Install the plugin

```bash
# Install for the current project (recommended for teams)
/plugin install liv-hooks@claude-liv-conventions --scope project

# Or install globally for all projects
/plugin install liv-hooks@claude-liv-conventions --scope user
```

### 3. Restart Claude Code

Hooks are loaded when Claude Code starts. Restart to activate the plugin.

## Manual Installation

Alternatively, add to your `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "claude-liv-conventions": {
      "source": {
        "source": "github",
        "repo": "RasmusGodske/claude-liv-conventions"
      }
    }
  },
  "enabledPlugins": {
    "liv-hooks@claude-liv-conventions": true
  }
}
```

## Project Structure

```
claude-liv-conventions/
├── .claude-plugin/
│   └── marketplace.json        # Marketplace catalog
├── plugins/
│   └── liv-hooks/
│       ├── .claude-plugin/
│       │   └── plugin.json     # Plugin manifest with hooks config
│       ├── hooks/
│       │   ├── FormRequestBlocker/
│       │   │   ├── pyproject.toml
│       │   │   └── main.py
│       │   └── VueScriptValidator/
│       │       ├── pyproject.toml
│       │       └── main.py
│       └── README.md
└── README.md
```

## Adding New Hooks

See [plugins/liv-hooks/README.md](plugins/liv-hooks/README.md) for instructions on creating new hooks.

## License

MIT
