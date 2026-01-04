# FormRequestBlocker

Blocks creation of Laravel FormRequest classes and guides towards using `spatie/laravel-data` DataClasses instead.

## What It Does

When Claude tries to:
- Run artisan commands to create request classes
- Write files to `app/Http/Requests/`
- Create PHP classes extending `FormRequest`
- Import `Illuminate\...\FormRequest`

This hook blocks the operation and provides guidance on using DataClasses instead.

## Why

FormRequests are the traditional Laravel way to handle form validation, but DataClasses from `spatie/laravel-data` provide:
- Type-safe data transfer objects
- Automatic TypeScript type generation with `#[TypeScript()]`
- Better separation of validation from request handling
- Reusable data structures across the application

## Examples

**Blocked patterns:**
- Artisan commands creating request classes
- Files in `app/Http/Requests/` directory
- Classes extending `FormRequest`

**Guided Towards:**
```php
#[TypeScript()]
class StoreUserData extends Data
{
    public function __construct(
        #[Required, Email]
        public string $email,
        #[Required, Min(8)]
        public string $password,
    ) {}
}
```

## Configuration

Environment variables:
- `FORM_REQUEST_BLOCKER_VERBOSE=1` - Enable verbose logging
- `FORM_REQUEST_BLOCKER_LOG=/path/to/log` - Log to file
