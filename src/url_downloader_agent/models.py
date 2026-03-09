from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Platform(str, Enum):
    GOOGLE_DRIVE = "google_drive"
    MICROSOFT = "microsoft"
    WEB = "web"


@dataclass
class DownloadResult:
    status: str
    source_platform: Platform
    filename: str | None = None
    filepath: Path | None = None
    mime_type: str | None = None
    bytes_saved: int = 0
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "source_platform": self.source_platform.value,
            "filename": self.filename,
            "filepath": str(self.filepath) if self.filepath else None,
            "mime_type": self.mime_type,
            "bytes_saved": self.bytes_saved,
            "error": self.error,
        }
