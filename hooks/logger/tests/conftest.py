"""Pytest configuration for logger hook tests."""

import sys
from pathlib import Path

# Add hooks directory to path for imports
hooks_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(hooks_dir))

# Import shared fixtures
from tests.conftest import *  # noqa: F401, F403
