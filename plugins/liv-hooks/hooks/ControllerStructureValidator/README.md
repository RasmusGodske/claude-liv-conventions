# ControllerStructureValidator

Enforces nested directory structure for Laravel controllers.

## What It Does

When writing controller files, this hook blocks files placed directly in `app/Http/Controllers/` and requires them to be in domain subdirectories.

## Why

Flat controller structures don't scale:
- Hard to find related controllers
- No clear domain boundaries
- Controllers become a dumping ground

Nested structures provide:
- Clear domain organization
- Related controllers grouped together
- Easier navigation as the codebase grows

## Examples

**Blocked:**
```
app/Http/Controllers/UserController.php
app/Http/Controllers/OrderController.php
app/Http/Controllers/ProductController.php
```

**Allowed:**
```
app/Http/Controllers/Users/UserController.php
app/Http/Controllers/Users/ProfileController.php
app/Http/Controllers/Orders/OrderController.php
app/Http/Controllers/Orders/InvoiceController.php
app/Http/Controllers/Auth/LoginController.php
```

## Performance

This hook uses fast regex matching (~milliseconds). No external calls.

## Configuration

Environment variables:
- `CONTROLLER_VALIDATOR_VERBOSE=1` - Enable verbose logging
- `CONTROLLER_VALIDATOR_LOG=/path/to/log` - Log to file
