"""Shared subprocess utilities for Claude Code skills.

Provides consistent subprocess handling with streaming output,
pattern matching, and structured results.
"""

import re
import subprocess
from dataclasses import dataclass, field
from typing import Callable

import structlog

logger = structlog.get_logger()


@dataclass
class StreamResult:
    """Result of a streaming subprocess execution.

    Attributes:
        success: Whether the command succeeded (return code 0)
        return_code: Process return code
        output: Combined stdout/stderr output
        matches: Dictionary of pattern matches found during streaming
        error: Error message if execution failed
    """

    success: bool
    return_code: int = 0
    output: str = ""
    matches: dict[str, str | None] = field(default_factory=dict)
    error: str | None = None


def run_streaming(
    cmd: list[str],
    patterns: dict[str, re.Pattern] | None = None,
    on_line: Callable[[str], None] | None = None,
    on_match: Callable[[str, str, str], None] | None = None,
    timeout: int | None = None,
) -> StreamResult:
    """Run a command with streaming output and pattern matching.

    Args:
        cmd: Command and arguments to execute
        patterns: Dictionary of {name: compiled_regex} to match against output
        on_line: Callback for each output line (receives line string)
        on_match: Callback when pattern matches (receives pattern_name, match_value, line)
        timeout: Optional timeout in seconds

    Returns:
        StreamResult with success status, output, and matched patterns

    Example:
        >>> patterns = {
        ...     "url": re.compile(r"(https://[^\\s]+)"),
        ...     "code": re.compile(r"([A-Z]{4}-[A-Z]{4})"),
        ... }
        >>> result = run_streaming(
        ...     ["aws", "sso", "login", "--profile", "dev"],
        ...     patterns=patterns,
        ...     on_line=lambda l: print(l, end=""),
        ... )
        >>> if result.success:
        ...     print(f"URL: {result.matches.get('url')}")
    """
    logger.debug("subprocess_start", cmd=" ".join(cmd))

    matches: dict[str, str | None] = {name: None for name in (patterns or {})}
    output_lines: list[str] = []

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        for line in process.stdout:
            output_lines.append(line)

            # Call line callback
            if on_line:
                on_line(line)

            # Check patterns
            if patterns:
                for name, pattern in patterns.items():
                    if matches[name] is None:  # Only match first occurrence
                        match = pattern.search(line)
                        if match:
                            value = match.group(1) if match.groups() else match.group(0)
                            matches[name] = value
                            logger.debug("pattern_matched", pattern=name, value=value)
                            if on_match:
                                on_match(name, value, line)

        process.wait(timeout=timeout)

        return StreamResult(
            success=process.returncode == 0,
            return_code=process.returncode,
            output="".join(output_lines),
            matches=matches,
        )

    except subprocess.TimeoutExpired:
        logger.error("subprocess_timeout", cmd=" ".join(cmd), timeout=timeout)
        if process:
            process.kill()
        return StreamResult(
            success=False,
            return_code=-1,
            output="".join(output_lines),
            matches=matches,
            error=f"Command timed out after {timeout}s",
        )
    except KeyboardInterrupt:
        if process:
            process.terminate()
        raise
    except Exception as e:
        logger.error("subprocess_error", cmd=" ".join(cmd), error=str(e))
        return StreamResult(
            success=False,
            return_code=-1,
            output="".join(output_lines),
            matches=matches,
            error=str(e),
        )


def run_simple(
    cmd: list[str],
    check: bool = False,
    timeout: int | None = None,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """Run a simple command with standard subprocess handling.

    Args:
        cmd: Command and arguments to execute
        check: Raise CalledProcessError on non-zero exit
        timeout: Optional timeout in seconds
        capture_output: Capture stdout/stderr

    Returns:
        subprocess.CompletedProcess result

    Raises:
        subprocess.CalledProcessError: If check=True and command fails
        subprocess.TimeoutExpired: If command exceeds timeout
    """
    logger.debug("subprocess_simple", cmd=" ".join(cmd))
    return subprocess.run(
        cmd,
        check=check,
        timeout=timeout,
        capture_output=capture_output,
        text=True,
    )


def check_command_exists(cmd: str) -> bool:
    """Check if a command is available in PATH.

    Args:
        cmd: Command name to check

    Returns:
        True if command exists, False otherwise
    """
    try:
        result = subprocess.run(
            ["which", cmd],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False
