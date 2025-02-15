# utils.py

import random
import time

def random_wait(min_sec=5, max_sec=15):
    """Random delay to avoid pattern detection by LinkedIn."""
    delay = random.randint(min_sec, max_sec)
    time.sleep(delay)

def sanitize_filename(name: str) -> str:
    """
    Example utility function: remove invalid filename characters, etc.
    """
    return "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()
