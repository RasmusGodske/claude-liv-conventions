"""Tests for ControllerServiceLayerReminder hook.

This is a PostToolUse hook that provides reminders (additionalContext)
rather than blocking. Tests verify the detection logic.
"""

import pytest
from tests.utils import run_hook


class TestControllerServiceLayerReminderDetection:
    """Tests for detecting direct Eloquent mutations."""

    def test_detects_save_in_store_method(self):
        """Should detect $variable->save() in store method."""
        result = run_hook("ControllerServiceLayerReminder", {
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "app/Http/Controllers/Users/UserController.php",
                "content": '''<?php
class UserController extends Controller
{
    public function store(Request $request)
    {
        $user = new User();
        $user->name = $request->name;
        $user->save();
        return redirect()->route('users.index');
    }
}
''',
            },
        })
        assert result is not None
        assert "additionalContext" in result.get("hookSpecificOutput", {})

    def test_detects_model_create_in_store_method(self):
        """Should detect Model::create() in store method."""
        result = run_hook("ControllerServiceLayerReminder", {
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "app/Http/Controllers/Orders/OrderController.php",
                "content": '''<?php
class OrderController extends Controller
{
    public function store(StoreOrderData $data)
    {
        $order = Order::create($data->toArray());
        return redirect()->route('orders.show', $order);
    }
}
''',
            },
        })
        assert result is not None
        assert "additionalContext" in result.get("hookSpecificOutput", {})

    def test_detects_update_in_update_method(self):
        """Should detect $variable->update() in update method."""
        result = run_hook("ControllerServiceLayerReminder", {
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "app/Http/Controllers/Products/ProductController.php",
                "content": '''<?php
class ProductController extends Controller
{
    public function update(Request $request, Product $product)
    {
        $product->update($request->validated());
        return back();
    }
}
''',
            },
        })
        assert result is not None
        assert "additionalContext" in result.get("hookSpecificOutput", {})

    def test_detects_delete_in_destroy_method(self):
        """Should detect $variable->delete() in destroy method."""
        result = run_hook("ControllerServiceLayerReminder", {
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "app/Http/Controllers/Posts/PostController.php",
                "content": '''<?php
class PostController extends Controller
{
    public function destroy(Post $post)
    {
        $post->delete();
        return redirect()->route('posts.index');
    }
}
''',
            },
        })
        assert result is not None
        assert "additionalContext" in result.get("hookSpecificOutput", {})


class TestControllerServiceLayerReminderIgnores:
    """Tests for patterns that should NOT trigger the reminder."""

    def test_ignores_mutations_in_index_method(self):
        """Should not check index method (reads only)."""
        result = run_hook("ControllerServiceLayerReminder", {
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "app/Http/Controllers/Users/UserController.php",
                "content": '''<?php
class UserController extends Controller
{
    public function index()
    {
        // Even if there's a mutation here (weird but possible)
        $log = Log::create(['action' => 'viewed']);
        return view('users.index');
    }
}
''',
            },
        })
        assert result is None

    def test_ignores_non_controller_files(self):
        """Should not process non-controller PHP files."""
        result = run_hook("ControllerServiceLayerReminder", {
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "app/Services/UserService.php",
                "content": '''<?php
class UserService
{
    public function store(array $data)
    {
        return User::create($data);
    }
}
''',
            },
        })
        assert result is None

    def test_ignores_test_files(self):
        """Should not process test files."""
        result = run_hook("ControllerServiceLayerReminder", {
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "tests/Feature/Controllers/UserControllerTest.php",
                "content": '''<?php
class UserControllerTest extends TestCase
{
    public function test_store()
    {
        User::create(['name' => 'Test']);
    }
}
''',
            },
        })
        assert result is None

    def test_ignores_controller_using_service(self):
        """Should not trigger when controller uses a service."""
        result = run_hook("ControllerServiceLayerReminder", {
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "app/Http/Controllers/Users/UserController.php",
                "content": '''<?php
class UserController extends Controller
{
    public function __construct(
        private UserService $userService
    ) {}

    public function store(StoreUserData $data)
    {
        $user = $this->userService->create($data);
        return redirect()->route('users.show', $user);
    }
}
''',
            },
        })
        assert result is None


class TestControllerServiceLayerReminderEdgeCases:
    """Edge case tests."""

    def test_ignores_read_tool(self):
        """Should only process Write tool."""
        result = run_hook("ControllerServiceLayerReminder", {
            "hook_event_name": "PostToolUse",
            "tool_name": "Read",
            "tool_input": {
                "file_path": "app/Http/Controllers/Users/UserController.php",
            },
        })
        assert result is None

    def test_handles_empty_content(self):
        """Should handle empty content gracefully."""
        result = run_hook("ControllerServiceLayerReminder", {
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "app/Http/Controllers/Users/UserController.php",
                "content": "",
            },
        })
        assert result is None
