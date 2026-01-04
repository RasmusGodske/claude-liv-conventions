# E2EPathValidator

Validates that E2E test file paths match actual Laravel routes.

## What It Does

When writing E2E test files (`e2e/tests/**/*.spec.ts`), this hook uses Claude Agent SDK to:

1. Extract the expected Laravel route from the test path
2. Run `php artisan route:list` to verify the route exists
3. Block the file if the path doesn't match a real route

## Why

E2E tests should be organized to mirror the application's route structure. This prevents:
- Tests for non-existent routes
- Misnamed test directories that don't match route segments
- Confusion about which route a test covers

## Examples

| Test Path | Expected Route | Valid? |
|-----------|---------------|--------|
| `e2e/tests/routes/app/users/index/smoke.spec.ts` | `GET /app/users` | ✅ If route exists |
| `e2e/tests/routes/app/users/create/smoke.spec.ts` | `GET /app/users/create` | ✅ If route exists |
| `e2e/tests/routes/app/fake-page/smoke.spec.ts` | `GET /app/fake-page` | ❌ Route doesn't exist |

## Performance Note

This hook uses Claude Agent SDK to run artisan commands and analyze output. It has a 120-second timeout and only runs on E2E test files, so the performance impact is limited to when you're writing E2E tests.

## Configuration

Environment variables:
- `E2E_VALIDATOR_VERBOSE=1` - Enable verbose logging
- `E2E_VALIDATOR_LOG=/path/to/log` - Log to file
