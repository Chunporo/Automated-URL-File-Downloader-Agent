import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    output_dir: Path
    http_timeout_seconds: int
    google_api_key: str | None
    gemini_model: str
    google_access_token: str | None
    microsoft_graph_token: str | None
    web_bearer_token: str | None


    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            output_dir=Path(os.getenv("OUTPUT_DIR", "./downloads")).resolve(),
            http_timeout_seconds=int(os.getenv("HTTP_TIMEOUT_SECONDS", "30")),
            google_api_key=os.getenv("GOOGLE_API_KEY") or None,
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            google_access_token=os.getenv("GOOGLE_ACCESS_TOKEN") or None,
            microsoft_graph_token=os.getenv("MICROSOFT_GRAPH_TOKEN") or None,
            web_bearer_token=os.getenv("WEB_BEARER_TOKEN") or None,
        )
