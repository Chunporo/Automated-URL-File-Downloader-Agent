from urllib.parse import urlparse

from .models import Platform


def route_platform(url: str) -> Platform:
    hostname = (urlparse(url).hostname or "").lower()
    if hostname in {"drive.google.com", "docs.google.com"}:
        return Platform.GOOGLE_DRIVE
    if hostname in {"onedrive.live.com", "1drv.ms"} or hostname.endswith(".sharepoint.com"):
        return Platform.MICROSOFT
    return Platform.WEB
