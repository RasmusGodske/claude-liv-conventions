#!/usr/bin/env python3
"""
ControllerServiceLayerReminder - PostToolUse hook to remind Claude about service layer.

This hook runs AFTER Claude writes to a controller file and checks if
direct Eloquent mutations are used in store/update/destroy methods.
If found, it provides additionalContext to remind Claude to consider
using dedicated service classes.

This is a REMINDER, not a blocker. Claude can continue working.
"""

import re
import sys

from claude_hook_utils import (
    HookHandler,
    HookLogger,
    PostToolUseInput,
    PostToolUseResponse,
)

NAMESPACE = "claude-liv-conventions"


class ControllerServiceLayerReminder(HookHandler):
    """Reminds Claude to use service classes for database mutations."""

    # Patterns for direct Eloquent mutations (variable names vary)
    INSTANCE_MUTATION_PATTERNS = [
        r'\$\w+->save\s*\(',
        r'\$\w+->update\s*\(',
        r'\$\w+->delete\s*\(',
        r'\$\w+->forceDelete\s*\(',
    ]

    # Patterns for static Eloquent mutations (Model names vary)
    STATIC_MUTATION_PATTERNS = [
        r'\b[A-Z]\w+::create\s*\(',
        r'\b[A-Z]\w+::updateOrCreate\s*\(',
        r'\b[A-Z]\w+::firstOrCreate\s*\(',
        r'\b[A-Z]\w+::destroy\s*\(',
    ]

    # Methods where we check for mutations
    MUTATION_METHODS = ['store', 'update', 'destroy']

    REMINDER_MESSAGE = """The controller method contains direct Eloquent model mutations (save/update/delete/create).

Consider extracting database operations to a dedicated service class. This provides:
- Single point of entry for database mutations
- Reusability across controllers, commands, and jobs
- Easier unit testing
- Consistent business logic

This is a reminder, not a requirement. Simple CRUD operations may not need a service."""

    def __init__(self) -> None:
        super().__init__(
            logger=HookLogger.create_default(
                "ControllerServiceLayerReminder",
                namespace=NAMESPACE,
            )
        )

    def post_tool_use(self, input: PostToolUseInput) -> PostToolUseResponse | None:
        """Check controller after write and provide reminder if needed."""
        # Only process Write tool results
        if input.tool_name != "Write":
            return None

        # Only process controller files
        if not self._is_controller_file(input.file_path):
            return None

        # Skip test files
        if self._is_test_file(input.file_path):
            return None

        content = input.content
        if not content:
            return None

        self._log(f"Checking controller: {input.file_path}")

        # Check for direct mutations in store/update/destroy methods
        if self._has_direct_mutations_in_mutation_methods(content):
            self._log("Found direct Eloquent mutations - adding reminder")
            return PostToolUseResponse.with_message(self.REMINDER_MESSAGE)

        return None

    def _is_controller_file(self, file_path: str | None) -> bool:
        """Check if file is a Laravel controller."""
        if not file_path:
            return False
        # Must be in Controllers directory and be a PHP file
        return "Controllers/" in file_path and file_path.endswith(".php")

    def _is_test_file(self, file_path: str | None) -> bool:
        """Check if file is a test file."""
        if not file_path:
            return False
        return "/tests/" in file_path.lower() or file_path.lower().startswith("tests/")

    def _has_direct_mutations_in_mutation_methods(self, content: str) -> bool:
        """Check if store/update/destroy methods contain direct Eloquent mutations."""
        # Extract method bodies for store, update, destroy
        for method_name in self.MUTATION_METHODS:
            method_body = self._extract_method_body(content, method_name)
            if method_body and self._contains_eloquent_mutation(method_body):
                self._log(f"Found mutation in {method_name}() method")
                return True
        return False

    def _extract_method_body(self, content: str, method_name: str) -> str | None:
        """
        Extract the body of a specific method from PHP content.
        
        TODO: This is a simplified implementation. May need refinement for:
        - Methods with complex signatures (type hints, attributes)
        - Nested braces in strings/comments
        - Multi-line method signatures
        """
        # Pattern to find method start
        # Matches: public function store(...) or public function store(...): ReturnType
        pattern = rf'public\s+function\s+{method_name}\s*\([^)]*\)\s*(?::\s*[\\?\w]+)?\s*\{{'
        
        match = re.search(pattern, content)
        if not match:
            return None

        # Find the matching closing brace
        start = match.end() - 1  # Position of opening brace
        brace_count = 1
        pos = start + 1

        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1

        if brace_count == 0:
            return content[start:pos]

        return None

    def _contains_eloquent_mutation(self, method_body: str) -> bool:
        """Check if method body contains direct Eloquent mutations."""
        all_patterns = self.INSTANCE_MUTATION_PATTERNS + self.STATIC_MUTATION_PATTERNS
        
        for pattern in all_patterns:
            if re.search(pattern, method_body):
                return True
        return False

    def _log(self, message: str) -> None:
        """Log a message."""
        if self.logger:
            self.logger.info(message)


if __name__ == "__main__":
    sys.exit(ControllerServiceLayerReminder().run())
