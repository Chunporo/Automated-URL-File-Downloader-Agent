import re
from typing import Optional

URL_PATTERN = re.compile(r"https?://[^\s\]\[\)\(\"\'<>]+", re.IGNORECASE)


def extract_url_regex(message: str) -> Optional[str]:
    match = URL_PATTERN.search(message)
    return match.group(0) if match else None
