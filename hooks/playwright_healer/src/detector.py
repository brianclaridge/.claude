from typing import Dict, Any
from .paths import get_config


def is_playwright_tool(tool_name: str) -> bool:
    """Check if the tool is a Playwright MCP tool."""
    return tool_name.startswith("mcp__playwright__")


def extract_response_text(tool_response: Any) -> str:
    """Extract text content from tool response (handles multiple formats)."""
    if isinstance(tool_response, str):
        return tool_response

    if isinstance(tool_response, dict):
        if "text" in tool_response:
            return str(tool_response["text"])
        if "error" in tool_response:
            return str(tool_response["error"])
        if "stdout" in tool_response or "stderr" in tool_response:
            return f"{tool_response.get('stdout', '')} {tool_response.get('stderr', '')}"
        return str(tool_response)

    if isinstance(tool_response, list):
        texts = []
        for item in tool_response:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    texts.append(item.get("text", ""))
                elif "error" in item:
                    texts.append(str(item["error"]))
        return " ".join(texts)

    return str(tool_response)


def categorize_error(pattern: str) -> str:
    """Categorize error for appropriate recovery strategy."""
    pattern_lower = pattern.lower()

    if "already in use" in pattern_lower:
        return "browser_lock"
    elif "closed" in pattern_lower:
        return "browser_closed"
    elif "connection" in pattern_lower:
        return "connection_lost"
    else:
        return "unknown"


def detect_browser_error(tool_response: Any) -> Dict[str, Any]:
    """
    Detect browser-related errors in tool response.

    Returns:
        Dict with keys:
            - detected: bool
            - pattern: str (matched error pattern)
            - message: str (full error message)
            - error_type: str (categorized error type)
    """
    config = get_config()
    error_patterns = config.get("error_patterns", [])

    response_text = extract_response_text(tool_response)

    for pattern in error_patterns:
        if pattern.lower() in response_text.lower():
            error_type = categorize_error(pattern)

            return {
                "detected": True,
                "pattern": pattern,
                "message": response_text[:500],
                "error_type": error_type
            }

    return {
        "detected": False,
        "pattern": None,
        "message": None,
        "error_type": None
    }
