#!/usr/bin/env bash
#
# update-hooks.sh - Update claude-hook-utils in all hooks
#
# Usage: ./scripts/update-hooks.sh [--clean]
#
# Options:
#   --clean    Remove .venv directories for a completely fresh install
#
# This script updates the claude-hook-utils dependency in all hook directories
# by removing lock files and re-syncing with uv.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/plugins/liv-hooks/hooks"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
CLEAN=false
for arg in "$@"; do
    case $arg in
        --clean)
            CLEAN=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./scripts/update-hooks.sh [--clean]"
            echo ""
            echo "Options:"
            echo "  --clean    Remove .venv directories for a completely fresh install"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}Updating claude-hook-utils in all hooks...${NC}"
echo ""

# Check if hooks directory exists
if [[ ! -d "$HOOKS_DIR" ]]; then
    echo -e "${RED}Error: Hooks directory not found: $HOOKS_DIR${NC}"
    exit 1
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv is not installed. Please install it first.${NC}"
    exit 1
fi

# Track results
updated=()
failed=()

# Process each hook directory
for hook_dir in "$HOOKS_DIR"/*/; do
    hook_name=$(basename "$hook_dir")

    # Skip if no pyproject.toml
    if [[ ! -f "$hook_dir/pyproject.toml" ]]; then
        echo -e "${YELLOW}Skipping $hook_name (no pyproject.toml)${NC}"
        continue
    fi

    # Check if it uses claude-hook-utils
    if ! grep -q "claude-hook-utils" "$hook_dir/pyproject.toml"; then
        echo -e "${YELLOW}Skipping $hook_name (doesn't use claude-hook-utils)${NC}"
        continue
    fi

    echo -e "${BLUE}Updating $hook_name...${NC}"

    # Remove lock file to force re-resolution
    if [[ -f "$hook_dir/uv.lock" ]]; then
        rm "$hook_dir/uv.lock"
        echo "  Removed uv.lock"
    fi

    # Optionally remove .venv for clean install
    if [[ "$CLEAN" == true ]] && [[ -d "$hook_dir/.venv" ]]; then
        rm -rf "$hook_dir/.venv"
        echo "  Removed .venv"
    fi

    # Run uv sync
    if (cd "$hook_dir" && uv sync 2>&1); then
        echo -e "  ${GREEN}✓ Updated successfully${NC}"
        updated+=("$hook_name")
    else
        echo -e "  ${RED}✗ Failed to update${NC}"
        failed+=("$hook_name")
    fi

    echo ""
done

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}========================================${NC}"

if [[ ${#updated[@]} -gt 0 ]]; then
    echo -e "${GREEN}Updated (${#updated[@]}):${NC}"
    for hook in "${updated[@]}"; do
        echo "  ✓ $hook"
    done
fi

if [[ ${#failed[@]} -gt 0 ]]; then
    echo -e "${RED}Failed (${#failed[@]}):${NC}"
    for hook in "${failed[@]}"; do
        echo "  ✗ $hook"
    done
    exit 1
fi

echo ""
echo -e "${GREEN}All hooks updated successfully!${NC}"
