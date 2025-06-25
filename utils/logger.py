# utils/logger.py

import datetime
import os

LOG_DIR = "data/logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "events.log")

def log_event(tag: str, content):
    """
    Log an event with tag and content.
    Handles various content types safely by converting to string.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Convert content to string safely
    if hasattr(content, '__await__'):
        # Handle coroutines by converting to string representation
        content_str = f"<coroutine object: {type(content).__name__}>"
    elif isinstance(content, (dict, list)):
        # Handle JSON-serializable objects
        try:
            import json
            content_str = json.dumps(content)
        except (TypeError, ValueError):
            content_str = str(content)
    else:
        # Handle other types by converting to string
        content_str = str(content)
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{tag}] {content_str}\n")
