"""Error handling module for gac."""

import logging
import sys
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


class GacError(Exception):
    """Base exception class for all gac errors."""

    exit_code = 1  # Default exit code

    def __init__(
        self,
        message: str,
        details: str | None = None,
        suggestion: str | None = None,
        exit_code: int | None = None,
    ):
        """
        Initialize a new GacError.

        Args:
            message: The error message
            details: Optional details about the error
            suggestion: Optional suggestion for the user
            exit_code: Optional exit code to override the class default
        """
        super().__init__(message)
        self.message = message
        self.details = details
        self.suggestion = suggestion
        if exit_code is not None:
            self.exit_code = exit_code


class ConfigError(GacError):
    """Error related to configuration issues."""

    exit_code = 2


class GitError(GacError):
    """Error related to Git operations."""

    exit_code = 3


class AIError(GacError):
    """Error related to AI provider or models."""

    exit_code = 4

    def __init__(
        self,
        message: str,
        error_type: str = "unknown",
        exit_code: int | None = None,
        suggestion: str | None = None,
    ):
        """Initialize an AIError with a specific error type.

        Args:
            message: The error message
            error_type: The type of AI error (from AI_ERROR_CODES keys)
            exit_code: Optional exit code to override the default
            suggestion: Optional suggestion for the user
        """
        super().__init__(message, exit_code=exit_code, suggestion=suggestion)
        self.error_type = error_type
        self.error_code = AI_ERROR_CODES.get(error_type, AI_ERROR_CODES["unknown"])

    @classmethod
    def authentication_error(cls, message: str, *, suggestion: str | None = None) -> "AIError":
        """Create an authentication error."""
        return cls(
            message,
            error_type="authentication",
            suggestion=suggestion or "Run 'uvx gac init' to configure your API key.",
        )

    @classmethod
    def connection_error(cls, message: str, *, suggestion: str | None = None) -> "AIError":
        """Create a connection error."""
        return cls(
            message, error_type="connection", suggestion=suggestion or "Check your internet connection and try again."
        )

    @classmethod
    def rate_limit_error(cls, message: str, *, suggestion: str | None = None) -> "AIError":
        """Create a rate limit error."""
        return cls(
            message,
            error_type="rate_limit",
            suggestion=suggestion or "Wait a moment and try again, or switch to a different model.",
        )

    @classmethod
    def timeout_error(cls, message: str, *, suggestion: str | None = None) -> "AIError":
        """Create a timeout error."""
        return cls(
            message, error_type="timeout", suggestion=suggestion or "Try again, or use a different model with --model."
        )

    @classmethod
    def model_error(cls, message: str, *, suggestion: str | None = None) -> "AIError":
        """Create a model error."""
        return cls(
            message, error_type="model", suggestion=suggestion or "Run 'uvx gac model' to configure a valid model."
        )

    @classmethod
    def unknown_error(cls, message: str, *, suggestion: str | None = None) -> "AIError":
        """Create an unknown error."""
        return cls(message, error_type="unknown", suggestion=suggestion)


class FormattingError(GacError):
    """Error related to code formatting."""

    exit_code = 5


class SecurityError(GacError):
    """Error related to security issues (e.g., detected secrets)."""

    exit_code = 6


class HookError(GacError):
    """Error when pre-commit or lefthook hooks fail."""

    exit_code = 1


# Simplified error hierarchy - we use a single AIError class with error codes
# instead of multiple subclasses for better maintainability

# Error codes for AI errors
AI_ERROR_CODES = {
    "authentication": 401,  # Authentication failures
    "connection": 503,  # Connection issues
    "rate_limit": 429,  # Rate limits
    "timeout": 408,  # Timeouts
    "model": 400,  # Model-related errors
    "unknown": 500,  # Unknown errors
}


def _error_display_name(error: Exception) -> str:
    """Return a short, human-readable label for the error category."""
    if isinstance(error, AIError):
        type_labels = {
            "authentication": "Authentication Error",
            "connection": "Connection Error",
            "rate_limit": "Rate Limit",
            "timeout": "Timeout",
            "model": "Model Error",
        }
        return type_labels.get(getattr(error, "error_type", ""), "AI Error")
    if isinstance(error, ConfigError):
        return "Configuration Error"
    if isinstance(error, GitError):
        return "Git Error"
    if isinstance(error, SecurityError):
        return "Security Error"
    if isinstance(error, FormattingError):
        return "Formatting Error"
    if isinstance(error, HookError):
        return "Hook Error"
    return "Error"


def handle_error(error: Exception, exit_program: bool = False, quiet: bool = False) -> None:
    """Handle an error with proper logging and user feedback.

    Displays a Rich-formatted error panel to the user and logs the error
    for debugging. If the error has a ``suggestion`` attribute, it is shown
    as a helpful hint below the main message.

    Args:
        error: The error to handle
        exit_program: If True, exit the program after handling the error
        quiet: If True, suppress console output (still logs)
    """
    logger.error(f"Error: {str(error)}")

    if isinstance(error, GitError):
        logger.error("Git operation failed. Please check your repository status.")
    elif isinstance(error, AIError):
        logger.error("AI operation failed. Please check your configuration and API keys.")
    elif isinstance(error, SecurityError):
        logger.error("Security scan detected potential secrets in staged changes.")
    else:
        logger.error("An unexpected error occurred.")

    # Show user-friendly Rich output (unless quiet mode)
    if not quiet:
        try:
            from gac.utils import console

            display_name = _error_display_name(error)
            message = str(error)
            suggestion = getattr(error, "suggestion", None)

            # Build the panel content
            lines = [message]
            if suggestion:
                lines.append("")
                lines.append(f"💡 {suggestion}")

            console.print(f"\n[bold red]{display_name}[/bold red]")
            console.print("[red]" + "─" * 40 + "[/red]")
            console.print("[red]" + "\n".join(lines) + "[/red]")
        except Exception:
            # Rich display is best-effort; never let it mask the original error
            pass

    if exit_program:
        logger.error("Exiting program due to error.")
        sys.exit(error.exit_code if hasattr(error, "exit_code") else 1)


def format_error_for_user(error: Exception) -> str:
    """
    Format an error message for display to the user.

    If the error has a ``suggestion`` attribute (set via GacError/AIError
    constructors or factory methods), it takes precedence over the
    generic per-type remediation text.

    Args:
        error: The exception to format

    Returns:
        A user-friendly error message with remediation steps if applicable
    """
    base_message = str(error)
    suggestion = getattr(error, "suggestion", None)

    # If the error already carries a suggestion, use it directly
    if suggestion:
        return f"{base_message}\n\n💡 {suggestion}"

    # Fallback remediation for AI errors without a suggestion attribute
    if isinstance(error, AIError):
        if hasattr(error, "error_type"):
            if error.error_type == "authentication":
                return f"{base_message}\n\nPlease check your API key and ensure it is valid."
            elif error.error_type == "connection":
                return f"{base_message}\n\nPlease check your internet connection and try again."
            elif error.error_type == "rate_limit":
                return f"{base_message}\n\nYou've hit the rate limit for this AI provider. Please wait and try again later."
            elif error.error_type == "timeout":
                return f"{base_message}\n\nThe request timed out. Please try again or use a different model."
            elif error.error_type == "model":
                return f"{base_message}\n\nPlease check that the specified model exists and is available to you."
        return f"{base_message}\n\nPlease check your API key, model name, and internet connection."

    # Mapping of error types to remediation steps
    remediation_steps = {
        ConfigError: "Please check your configuration settings.",
        GitError: "Please ensure Git is installed and you're in a valid Git repository.",
        FormattingError: "Please check that required formatters are installed.",
        SecurityError: "Please remove or secure any detected secrets before committing.",
    }

    # Generic remediation for unexpected errors
    if not any(isinstance(error, t) for t in remediation_steps.keys()):
        return f"{base_message}\n\nIf this issue persists, please report it as a bug."

    # Get remediation steps for the specific error type
    for error_class, steps in remediation_steps.items():
        if isinstance(error, error_class):
            return f"{base_message}\n\n{steps}"

    # Fallback (though we should never reach this)
    return base_message


def with_error_handling(
    error_type: type[GacError], error_message: str, quiet: bool = False, exit_on_error: bool = True
) -> Callable[[Callable[..., T]], Callable[..., T | None]]:
    """
    A decorator that wraps a function with standardized error handling.

    Args:
        error_type: The specific error type to raise if an exception occurs
        error_message: The error message to use
        quiet: If True, suppress non-error output
        exit_on_error: If True, exit the program on error

    Returns:
        A decorator function that handles errors for the wrapped function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T | None]:
        def wrapper(*args: Any, **kwargs: Any) -> T | None:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Create a specific error with our message and the original error
                specific_error = error_type(f"{error_message}: {e}")
                # Handle the error using our standardized handler
                handle_error(specific_error, quiet=quiet, exit_program=exit_on_error)
                return None

        return wrapper

    return decorator
