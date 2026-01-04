# ControllerServiceLayerReminder

A **PostToolUse** hook that reminds Claude to use dedicated service classes for database mutations in controllers, instead of directly manipulating Eloquent models.

## Why PostToolUse (Not PreToolUse)?

This hook uses **PostToolUse** instead of PreToolUse because:

1. **Non-blocking** - Allows Claude to create initial boilerplate without interruption
2. **Gentle steering** - Provides context after the fact, doesn't reject work
3. **Better UX** - Claude can iterate; the reminder influences next steps
4. **Handles uncertainty** - Sometimes direct mutations are acceptable (simple CRUD)

## What It Does

After Claude writes to a controller file, this hook:

1. Checks if the file is a Laravel controller
2. Looks for `store()`, `update()`, or `destroy()` methods
3. Detects direct Eloquent mutations within those methods
4. If found, returns `additionalContext` reminding Claude to consider using services

## Why This Pattern Matters

Without services:
- Duplicate logic across API controllers, Inertia controllers, console commands
- Hard to test (controllers are harder to unit test than services)
- Business logic scattered across the codebase
- No single point of entry for database mutations

With services:
- Single source of truth for business logic
- Easy to reuse across controllers, commands, jobs
- Easy to unit test
- Clear separation of concerns

## Detection Patterns

### Eloquent Mutation Patterns to Detect

The hook detects these patterns within `store()`, `update()`, `destroy()` methods:

```php
// Instance methods (variable name varies!)
$user->save();
$order->update([...]);
$product->delete();
$model->forceDelete();

// Static methods (Model name varies!)
User::create([...]);
Order::updateOrCreate([...]);
Product::firstOrCreate([...]);
Customer::destroy($id);
```

### Important: Variable/Model Names Vary

The hook must NOT hardcode `$model` or specific model names. Detection should use patterns like:

```python
# Instance mutations - match any variable
r'\$\w+->save\s*\('
r'\$\w+->update\s*\('
r'\$\w+->delete\s*\('
r'\$\w+->forceDelete\s*\('

# Static mutations - match any class
r'\b[A-Z]\w+::create\s*\('
r'\b[A-Z]\w+::updateOrCreate\s*\('
r'\b[A-Z]\w+::firstOrCreate\s*\('
r'\b[A-Z]\w+::destroy\s*\('
```

### Methods to Check

Only check within these controller methods:
- `store()` - Creating new records
- `update()` - Updating existing records  
- `destroy()` - Deleting records

Do NOT check:
- `index()` - Listing (reads are fine in controllers)
- `show()` - Showing single record (reads are fine)
- `create()` - Showing create form (no mutations)
- `edit()` - Showing edit form (no mutations)

## Response Format

PostToolUse hooks return a different format than PreToolUse:

```python
# PostToolUse response with systemMessage
{
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "systemMessage": "The controller contains direct Eloquent mutations..."
    }
}
```

Key differences from PreToolUse:
- No `decision: "block"` needed (we're not blocking)
- `systemMessage` provides guidance for Claude's next actions
- Claude sees this message and can choose to refactor

Using `claude-hook-utils`:
```python
from claude_hook_utils import PostToolUseResponse

# Return a message for Claude to consider
return PostToolUseResponse.with_message("Your reminder message here")
```

## What This Hook Does NOT Do

1. **Does NOT block** - It's a reminder, not a gatekeeper
2. **Does NOT prescribe HOW** - Doesn't tell Claude how to create services
3. **Does NOT apply to reads** - Only mutation methods (store/update/destroy)
4. **Does NOT require immediate action** - Claude may continue, the reminder is contextual

## Configuration

Environment variables:
- `SERVICE_REMINDER_VERBOSE=1` - Enable verbose logging
- `SERVICE_REMINDER_LOG=/path/to/log` - Log to file

## Example Reminder Message

```
The controller method contains direct Eloquent model mutations (save/update/delete/create).

Consider extracting database operations to a dedicated service class. This provides:
- Single point of entry for database mutations
- Reusability across controllers, commands, and jobs
- Easier unit testing
- Consistent business logic

This is a reminder, not a requirement. Simple CRUD operations may not need a service.
```

## Implementation Notes

### Detecting Method Boundaries

To only check within store/update/destroy methods, the hook should:

1. Find method signatures: `public function store(`, `public function update(`, etc.
2. Track brace depth to find method boundaries
3. Only check for mutations within those boundaries

Simple approach (may have edge cases):
```python
# Find store/update/destroy method bodies
pattern = r'public\s+function\s+(store|update|destroy)\s*\([^)]*\)\s*(?::\s*\w+)?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
```

### False Positive Considerations

Some patterns that might trigger but are acceptable:
- Using `->save()` after getting from a service (but this is rare)
- Test files (should exclude `tests/` directory)
- Base controller classes (should exclude abstract classes)

## Testing Strategy

Tests should cover:
1. Detects `->save()` in store method
2. Detects `Model::create()` in store method  
3. Detects `->update()` in update method
4. Detects `->delete()` in destroy method
5. Ignores mutations in index/show methods
6. Ignores non-controller files
7. Ignores files in tests/ directory
8. Returns proper PostToolUse response format
