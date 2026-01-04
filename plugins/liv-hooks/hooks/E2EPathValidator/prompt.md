# E2E Route Test Path Validation

<context>
<file_path_being_created>
{file_path}
</file_path_being_created>
</context>

## Instructions

You are validating an E2E test file path for convention compliance.

### Step 1: Check if This is a Route Test

Route tests MUST be in `e2e/tests/routes/`. If the file is NOT in this directory, this validator does not apply.

**If the file is NOT in `e2e/tests/routes/`:**
```
<validation_result>
<decision>allow</decision>
</validation_result>
```

### Step 2: Extract the Expected Route

From the test path, extract the expected Laravel route. The test directory structure should match the route **exactly**.

Examples:
- `e2e/tests/routes/app/users/index/smoke.spec.ts` → `GET /app/users`
- `e2e/tests/routes/app/users/create/smoke.spec.ts` → `GET /app/users/create`
- `e2e/tests/routes/app/users/edit/smoke.spec.ts` → `GET /app/users/{user}/edit`
- `e2e/tests/routes/login/smoke.spec.ts` → `GET /login`

**Conversion rules:**
1. Directory path maps directly to URL path (no case conversion needed)
2. `index/` → no suffix (just the base path)
3. `create/` → `/create` suffix
4. `edit/` → `/{param}/edit` suffix (with parameter placeholder)
5. `show/` → `/{param}` suffix (with parameter placeholder)

### Step 3: Verify the Route Exists

Run `php artisan route:list --method=GET --path=<extracted_path>` to check if the route exists.

For example:
- For `/app/users` → `php artisan route:list --method=GET --path=app/users`
- For `/login` → `php artisan route:list --method=GET --path=login`

**Note:** The route list may show routes with parameters like `{user}` - this is expected for edit/show routes.

### Step 4: Validate Directory Names Match Route

Check that directory names in the test path **exactly match** the route segments:
- If route is `/app/commission_plans`, directory must be `commission_plans/` (not `commission-plans/`)
- If route is `/app/users`, directory must be `users/`

### Step 5: Output Your Decision

<output_instructions>
- Do NOT explain your process in detail
- Do NOT include unnecessary commentary
- You MUST wrap your entire response in a <validation_result> tag
- You MUST include a <decision> tag with value "allow" or "block"
</output_instructions>

<report_format>
If the path is CORRECT (route exists and directory names match):

```
<validation_result>
<decision>allow</decision>
</validation_result>
```

If the route does NOT exist:

```
<validation_result>
<decision>block</decision>
<reason>
The route for test path `{test_path}` does not exist.

**Expected route:** `GET {expected_route}`

**Suggestion:** Run `php artisan route:list --method=GET` to find available routes.
</reason>
</validation_result>
```

If directory names don't match route segments:

```
<validation_result>
<decision>block</decision>
<reason>
The test path `{test_path}` does not match the Laravel route.

**Problem:** Directory `{directory}` should be `{correct_directory}` to match route `{route}`.

**Correct path:** `{correct_path}`
</reason>
</validation_result>
```

Replace the placeholders with actual values.
</report_format>
