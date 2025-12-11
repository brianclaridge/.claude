import sys
import json
from typing import Optional, Dict, Any, Generator


def read_hook_event() -> Optional[Dict[str, Any]]:
    try:
        line = sys.stdin.readline()
        if not line:
            return None
            
        line = line.strip()
        if not line:
            return None
            
        return json.loads(line)
        
    except json.JSONDecodeError:
        return None
    except Exception:
        return None


def process_stdin() -> Generator[Dict[str, Any], None, None]:
    while True:
        hook_data = read_hook_event()
        if hook_data is None:
            break
        yield hook_data