"""Tests for FormRequestBlocker hook."""

import pytest

from tests.utils import (
    assert_allowed,
    assert_denied,
    make_bash_input,
    make_write_input,
    run_hook,
)


HOOK_NAME = "FormRequestBlocker"


class TestFormRequestBlockerBash:
    """Tests for Bash command blocking."""

    def test_blocks_artisan_make_request(self):
        """Should block 'php artisan make:request' command."""
        result = run_hook(HOOK_NAME, make_bash_input("php artisan make:request StoreUserRequest"))
        assert_denied(result, reason_contains="DataClass")

    def test_blocks_artisan_make_request_with_path(self):
        """Should block make:request even with full path."""
        result = run_hook(HOOK_NAME, make_bash_input("/usr/bin/php artisan make:request TestRequest"))
        assert_denied(result, reason_contains="DataClass")

    def test_allows_other_artisan_commands(self):
        """Should allow other artisan commands."""
        result = run_hook(HOOK_NAME, make_bash_input("php artisan make:model User"))
        assert_allowed(result)

    def test_allows_general_bash_commands(self):
        """Should allow general bash commands."""
        result = run_hook(HOOK_NAME, make_bash_input("ls -la"))
        assert_allowed(result)

    def test_allows_composer_commands(self):
        """Should allow composer commands."""
        result = run_hook(HOOK_NAME, make_bash_input("composer install"))
        assert_allowed(result)


class TestFormRequestBlockerWritePath:
    """Tests for Write path blocking."""

    def test_blocks_http_requests_directory(self):
        """Should block files in app/Http/Requests/."""
        result = run_hook(
            HOOK_NAME,
            make_write_input(
                "app/Http/Requests/StoreUserRequest.php",
                "<?php\nnamespace App\\Http\\Requests;\nclass StoreUserRequest {}"
            )
        )
        assert_denied(result, reason_contains="Http/Requests")

    def test_blocks_nested_http_requests_directory(self):
        """Should block files in nested Http/Requests directories."""
        result = run_hook(
            HOOK_NAME,
            make_write_input(
                "app/Http/Requests/User/StoreUserRequest.php",
                "<?php\nclass StoreUserRequest {}"
            )
        )
        assert_denied(result, reason_contains="Http/Requests")

    def test_allows_data_directory(self):
        """Should allow files in app/Data/."""
        result = run_hook(
            HOOK_NAME,
            make_write_input(
                "app/Data/User/CreateUserData.php",
                "<?php\nnamespace App\\Data\\User;\nuse Spatie\\LaravelData\\Data;\nclass CreateUserData extends Data {}"
            )
        )
        assert_allowed(result)

    def test_allows_other_directories(self):
        """Should allow files in other directories."""
        result = run_hook(
            HOOK_NAME,
            make_write_input(
                "app/Services/UserService.php",
                "<?php\nclass UserService {}"
            )
        )
        assert_allowed(result)


class TestFormRequestBlockerWriteContent:
    """Tests for Write content blocking."""

    def test_blocks_extends_form_request(self):
        """Should block files that extend FormRequest."""
        result = run_hook(
            HOOK_NAME,
            make_write_input(
                "app/MyRequest.php",
                "<?php\nclass MyRequest extends FormRequest {}"
            )
        )
        assert_denied(result, reason_contains="FormRequest")

    def test_blocks_illuminate_form_request_import(self):
        """Should block files that import Illuminate FormRequest."""
        result = run_hook(
            HOOK_NAME,
            make_write_input(
                "app/MyRequest.php",
                "<?php\nuse Illuminate\\Foundation\\Http\\FormRequest;\nclass MyRequest {}"
            )
        )
        assert_denied(result, reason_contains="FormRequest")

    def test_allows_normal_php_class(self):
        """Should allow normal PHP classes."""
        result = run_hook(
            HOOK_NAME,
            make_write_input(
                "app/Services/MyService.php",
                "<?php\nnamespace App\\Services;\nclass MyService { public function handle() {} }"
            )
        )
        assert_allowed(result)

    def test_allows_data_class(self):
        """Should allow Data classes."""
        result = run_hook(
            HOOK_NAME,
            make_write_input(
                "app/Data/CreateUserData.php",
                "<?php\nuse Spatie\\LaravelData\\Data;\nclass CreateUserData extends Data {}"
            )
        )
        assert_allowed(result)


class TestFormRequestBlockerGuidance:
    """Tests for guidance message content."""

    def test_guidance_mentions_data_class(self):
        """Should provide guidance about using Data classes."""
        result = run_hook(HOOK_NAME, make_bash_input("php artisan make:request Test"))
        assert result is not None
        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "Data" in reason
        assert "spatie" in reason.lower() or "laravel-data" in reason.lower()

    def test_guidance_includes_example(self):
        """Should include code example in guidance."""
        result = run_hook(HOOK_NAME, make_bash_input("php artisan make:request Test"))
        assert result is not None
        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "extends Data" in reason
        assert "__construct" in reason


class TestFormRequestBlockerEdgeCases:
    """Tests for edge cases."""

    def test_ignores_non_php_files(self):
        """Should ignore non-PHP files."""
        result = run_hook(
            HOOK_NAME,
            make_write_input(
                "resources/views/request.blade.php",
                "FormRequest is mentioned here but it's a blade file"
            )
        )
        # Blade files don't extend FormRequest so this should pass
        assert_allowed(result)

    def test_ignores_read_tool(self):
        """Should not process Read tool."""
        result = run_hook(HOOK_NAME, {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_use_id": "test",
            "tool_input": {"file_path": "app/Http/Requests/Test.php"}
        })
        assert_allowed(result)

    def test_handles_empty_content(self):
        """Should handle empty content gracefully."""
        result = run_hook(
            HOOK_NAME,
            make_write_input("app/Test.php", "")
        )
        assert_allowed(result)
