"""Configuration helper utilities for Claude Code."""

from .config import (
    get_config_path,
    get_claude_root,
    get_workspace_root,
    get_global_config,
    get_hook_config,
    resolve_log_path,
)
from .logging import setup_logger, get_logger
from .paths import get_data_path, get_logs_path, ensure_directory
from .yaml_utils import safe_load, safe_dump

__all__ = [
    # config
    "get_config_path",
    "get_claude_root",
    "get_workspace_root",
    "get_global_config",
    "get_hook_config",
    "resolve_log_path",
    # logging
    "setup_logger",
    "get_logger",
    # paths
    "get_data_path",
    "get_logs_path",
    "ensure_directory",
    # yaml
    "safe_load",
    "safe_dump",
]

__version__ = "1.0.0"
