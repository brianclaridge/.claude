import argparse
import sys
from .loader import load_directives
from .formatter import format_to_hook_json


def parse_args():
    parser = argparse.ArgumentParser(
        description="Load markdown directives and output as JSON hook format"
    )

    parser.add_argument(
        "--dir",
        help="Directory containing .md directive files"
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with indentation"
    )

    return parser.parse_args()