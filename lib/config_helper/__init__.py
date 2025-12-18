"""Configuration helper utilities for Claude Code.

Core modules (config, paths, yaml_utils) use only stdlib + pyyaml.
The logging module requires loguru and must be imported explicitly:

    from config_helper.logging import setup_logger, get_logger
"""

from .config import (
    get_config_path,
    get_claude_root,
    get_workspace_root,
    get_global_config,
    get_hook_config,
    resolve_log_path,
)
from .paths import get_data_path, get_logs_path, ensure_directory
from .yaml_utils import safe_load, safe_dump

# Note: logging module requires loguru, import explicitly if needed:
# from config_helper.logging import setup_logger, get_logger

__all__ = [
    # config
    "get_config_path",
    "get_claude_root",
    "get_workspace_root",
    "get_global_config",
    "get_hook_config",
    "resolve_log_path",
    # paths
    "get_data_path",
    "get_logs_path",
    "ensure_directory",
    # yaml
    "safe_load",
    "safe_dump",
]

__version__ = "1.0.0"
