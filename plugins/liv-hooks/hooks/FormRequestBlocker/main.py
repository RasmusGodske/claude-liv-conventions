#!/usr/bin/env python3
"""
FormRequestBlocker - Blocks FormRequest creation and guides towards DataClasses.

This project uses spatie/laravel-data DataClasses instead of Laravel FormRequests
for validation. This hook prevents Claude from creating FormRequests.
"""

import re
import sys

from claude_hook_utils import (
    HookHandler,
    HookLogger,
    PreToolUseInput,
    PreToolUseResponse,
)

NAMESPACE = "claude-liv-conventions"


GUIDANCE_MESSAGE = """This project uses DataClasses (spatie/laravel-data) instead of FormRequests for validation.

Instead of creating a FormRequest, create a Data class:

1. Location: app/Data/{Domain}/{Name}Data.php (nested by domain)
2. Pattern:
   ```php
   namespace App\\Data\\{Domain};

   use Spatie\\LaravelData\\Data;

   class {Name}Data extends Data
   {
       public function __construct(
           public string $field,
           public ?int $optional_field = null,
       ) {}
   }
   ```

3. Usage in controller:
   ```php
   public function store({Name}Data $data): Response
   {
       // $data is already validated
   }
   ```

See: app/Data/ for examples. Refer to spatie/laravel-data documentation for advanced patterns."""


class FormRequestBlocker(HookHandler):
    """Blocks FormRequest creation and guides towards DataClasses."""

    def __init__(self) -> None:
        super().__init__(
            logger=HookLogger.create_default(
                "FormRequestBlocker",
                namespace=NAMESPACE,
            )
        )

    def pre_tool_use(self, input: PreToolUseInput) -> PreToolUseResponse | None:
        """Check for FormRequest creation attempts."""
        if input.tool_name == "Bash":
            return self._check_bash_command(input)
        elif input.tool_name == "Write":
            return self._check_write_content(input)
        return None

    def _check_bash_command(self, input: PreToolUseInput) -> PreToolUseResponse | None:
        """Check if bash command is creating a FormRequest."""
        command = input.tool_input.get("command", "")

        # Check for artisan make:request
        if re.search(r"artisan\s+make:request", command, re.IGNORECASE):
            self._log(f"Blocked: artisan make:request command")
            return PreToolUseResponse.deny(
                f"Do not use 'artisan make:request'. {GUIDANCE_MESSAGE}"
            )

        return None

    def _check_write_content(self, input: PreToolUseInput) -> PreToolUseResponse | None:
        """Check if writing a FormRequest file."""
        file_path = input.file_path or ""
        content = input.content or ""

        # Check if writing to Http/Requests directory
        if input.file_path_matches("**/Http/Requests/**/*.php"):
            self._log(f"Blocked: Writing to Http/Requests directory: {file_path}")
            return PreToolUseResponse.deny(
                f"Do not create files in Http/Requests/. {GUIDANCE_MESSAGE}"
            )

        # Check if content extends FormRequest
        if re.search(r"extends\s+FormRequest", content):
            self._log(f"Blocked: File extends FormRequest: {file_path}")
            return PreToolUseResponse.deny(
                f"Do not extend FormRequest. {GUIDANCE_MESSAGE}"
            )

        # Check if content uses Illuminate FormRequest
        if re.search(r"use\s+Illuminate\\.*\\FormRequest", content):
            self._log(f"Blocked: File imports FormRequest: {file_path}")
            return PreToolUseResponse.deny(
                f"Do not use Illuminate FormRequest. {GUIDANCE_MESSAGE}"
            )

        return None

    def _log(self, message: str) -> None:
        """Log a message if logger is available."""
        if self.logger:
            self.logger.info(message)


if __name__ == "__main__":
    sys.exit(FormRequestBlocker().run())
