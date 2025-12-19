from pathlib import Path
from typing import Any, Dict, List, Optional
import sys


def load_rules(directory_path: str) -> List[Dict[str, str]]:
    """Load all rule markdown files from the specified directory."""
    rules = []

    try:
        dir_path = Path(directory_path)

        if not dir_path.exists():
            print(f"Warning: Rules directory {directory_path} does not exist", file=sys.stderr)
            return rules

        if not dir_path.is_dir():
            print(f"Error: {directory_path} is not a directory", file=sys.stderr)
            return rules

        md_files = sorted(dir_path.glob("*.md"))

        for file_path in md_files:
            rule = read_rule(file_path)
            if rule:
                rules.append(rule)

    except Exception as e:
        print(f"Error loading rules: {e}", file=sys.stderr)

    return rules


def read_rule(file_path: Path) -> Optional[Dict[str, str]]:
    """Read a single rule file and return its content."""
    try:
        content = file_path.read_text(encoding="utf-8").strip()
        # Extract rule name without extension (e.g., "000-directives" from "000-directives.md")
        rule_name = file_path.stem
        return {
            "filename": file_path.name,
            "name": rule_name,
            "content": content
        }
    except Exception as e:
        print(f"Error reading rule {file_path}: {e}", file=sys.stderr)
        return None


def filter_rules_for_reinforcement(
    rules: List[Dict[str, str]],
    hook_config: Dict[str, Any],
    event_name: str
) -> List[Dict[str, str]]:
    """
    Filter rules based on reinforcement configuration.

    For SessionStart: return all rules
    For UserPromptSubmit: return only rules with reinforcement enabled

    Args:
        rules: List of rule dictionaries
        hook_config: The rules_loader hook config (from hooks.rules_loader)
        event_name: The hook event name
    """
    if event_name == "SessionStart":
        # Always load all rules on session start
        return rules

    # For UserPromptSubmit, check per-rule reinforcement settings
    global_reinforce = hook_config.get("reinforcement_enabled", False)
    per_rule_config = hook_config.get("rules", {})

    filtered = []
    for rule in rules:
        rule_name = rule.get("name", "")
        rule_settings = per_rule_config.get(rule_name, {})

        # Use per-rule setting if specified, otherwise use global default
        should_reinforce = rule_settings.get("reinforce", global_reinforce)

        if should_reinforce:
            filtered.append(rule)

    return filtered
