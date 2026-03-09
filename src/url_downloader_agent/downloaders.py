import base64
from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from .config import Settings
from .file_store import resolve_filename, save_bytes
from .models import DownloadResult, Platform


@dataclass
class HTTPResponseData:
    url: str
    content_type: str | None
    content_disposition: str | None
    payload: bytes


class WebDownloader:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.settings.web_bearer_token:
            headers["Authorization"] = f"Bearer {self.settings.web_bearer_token}"
        return headers

    def _head(self, url: str) -> requests.Response:
        return requests.head(
            url,
            allow_redirects=True,
            headers=self._headers(),
            timeout=self.settings.http_timeout_seconds,
        )

    def _get(self, url: str) -> requests.Response:
        return requests.get(
            url,
            allow_redirects=True,
            headers=self._headers(),
            timeout=self.settings.http_timeout_seconds,
        )

    def _find_download_link(self, base_url: str, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            lowered = href.lower()
            if any(token in lowered for token in ["download", ".pdf", ".docx", ".xlsx", ".zip", ".csv"]):
                return urljoin(base_url, href)
        return None

    def _fetch_binary(self, url: str) -> HTTPResponseData:
        response = self._get(url)
        response.raise_for_status()
        return HTTPResponseData(
            url=response.url,
            content_type=response.headers.get("Content-Type"),
            content_disposition=response.headers.get("Content-Disposition"),
            payload=response.content,
        )

    def download(self, url: str, platform: Platform = Platform.WEB) -> DownloadResult:
        try:
            head = self._head(url)
            content_type = (head.headers.get("Content-Type") or "").lower()

            if "text/html" in content_type:
                page = self._get(url)
                page.raise_for_status()
                candidate = self._find_download_link(page.url, page.text)
                if not candidate:
                    return DownloadResult(
                        status="failed",
                        source_platform=platform,
                        error="HTML page detected but no downloadable file link was found.",
                    )
                data = self._fetch_binary(candidate)
            else:
                data = self._fetch_binary(url)

            filename = resolve_filename(
                url=data.url,
                content_type=data.content_type,
                content_disposition=data.content_disposition,
            )
            target = save_bytes(self.settings.output_dir, filename, data.payload)
            return DownloadResult(
                status="success",
                source_platform=platform,
                filename=target.name,
                filepath=target,
                mime_type=data.content_type,
                bytes_saved=len(data.payload),
            )
        except requests.HTTPError as exc:
            return DownloadResult(status="failed", source_platform=platform, error=f"HTTP error: {exc}")
        except requests.RequestException as exc:
            return DownloadResult(status="failed", source_platform=platform, error=f"Network error: {exc}")


class GoogleDriveDownloader:
    def __init__(self, settings: Settings, web_downloader: WebDownloader) -> None:
        self.settings = settings
        self.web_downloader = web_downloader

    def _extract_file_id(self, url: str) -> str | None:
        parsed = urlparse(url)
        path_parts = [part for part in parsed.path.split("/") if part]
        if "d" in path_parts:
            idx = path_parts.index("d")
            if idx + 1 < len(path_parts):
                return path_parts[idx + 1]
        query_id = parse_qs(parsed.query).get("id")
        if query_id:
            return query_id[0]
        return None

    def _is_google_workspace_doc(self, url: str) -> tuple[bool, str | None]:
        parsed = urlparse(url)
        path = parsed.path
        export_map = {
            "/document/": "pdf",
            "/spreadsheets/": "xlsx",
            "/presentation/": "pptx",
        }
        for token, export_format in export_map.items():
            if token in path:
                return True, export_format
        return False, None

    def download(self, url: str) -> DownloadResult:
        file_id = self._extract_file_id(url)
        if not file_id:
            return DownloadResult(
                status="failed",
                source_platform=Platform.GOOGLE_DRIVE,
                error="Unable to extract Google Drive file id from URL.",
            )

        is_workspace, export_format = self._is_google_workspace_doc(url)
        if is_workspace and export_format:
            export_url = f"https://docs.google.com/document/d/{file_id}/export?format={export_format}"
            if "/spreadsheets/" in url:
                export_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format={export_format}"
            if "/presentation/" in url:
                export_url = f"https://docs.google.com/presentation/d/{file_id}/export/{export_format}"
            return self.web_downloader.download(export_url, platform=Platform.GOOGLE_DRIVE)

        direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        return self.web_downloader.download(direct_url, platform=Platform.GOOGLE_DRIVE)


class MicrosoftDownloader:
    def __init__(self, settings: Settings, web_downloader: WebDownloader) -> None:
        self.settings = settings
        self.web_downloader = web_downloader

    def _append_download_query(self, url: str) -> str:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        query["download"] = ["1"]
        encoded = urlencode(query, doseq=True)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, encoded, parsed.fragment))

    def _graph_share_id(self, url: str) -> str:
        encoded = base64.urlsafe_b64encode(url.encode("utf-8")).decode("utf-8").rstrip("=")
        return f"u!{encoded}"

    def _download_via_graph(self, shared_url: str) -> DownloadResult:
        if not self.settings.microsoft_graph_token:
            return DownloadResult(
                status="failed",
                source_platform=Platform.MICROSOFT,
                error="Microsoft Graph token missing. Set MICROSOFT_GRAPH_TOKEN or use a public link.",
            )

        headers = {"Authorization": f"Bearer {self.settings.microsoft_graph_token}"}
        share_id = self._graph_share_id(shared_url)
        meta_url = f"https://graph.microsoft.com/v1.0/shares/{share_id}/driveItem"
        try:
            meta = requests.get(meta_url, headers=headers, timeout=self.settings.http_timeout_seconds)
            meta.raise_for_status()
            metadata = meta.json()
            content_url = f"https://graph.microsoft.com/v1.0/shares/{share_id}/driveItem/content"
            response = requests.get(content_url, headers=headers, timeout=self.settings.http_timeout_seconds)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type")
            content_disposition = response.headers.get("Content-Disposition")
            fallback_name = metadata.get("name")
            filename = resolve_filename(shared_url, content_type, content_disposition, fallback=fallback_name)
            target = save_bytes(self.settings.output_dir, filename, response.content)
            return DownloadResult(
                status="success",
                source_platform=Platform.MICROSOFT,
                filename=target.name,
                filepath=target,
                mime_type=content_type,
                bytes_saved=len(response.content),
            )
        except requests.HTTPError as exc:
            return DownloadResult(status="failed", source_platform=Platform.MICROSOFT, error=f"Graph API error: {exc}")
        except requests.RequestException as exc:
            return DownloadResult(status="failed", source_platform=Platform.MICROSOFT, error=f"Network error: {exc}")

    def download(self, url: str) -> DownloadResult:
        if self.settings.microsoft_graph_token:
            return self._download_via_graph(url)
        candidate = self._append_download_query(url)
        return self.web_downloader.download(candidate, platform=Platform.MICROSOFT)
