import mimetypes
import re
from pathlib import Path
from urllib.parse import unquote, urlparse


def _sanitize_filename(name: str) -> str:
    sanitized = re.sub(r"[\\/:*?\"<>|]", "_", name).strip()
    return sanitized or "downloaded_file"


def _decode_filename(value: str) -> str:
    return unquote(value).strip()


def _filename_from_content_disposition(content_disposition: str | None) -> str | None:
    if not content_disposition:
        return None
    match = re.search(r"filename\*=UTF-8''([^;]+)", content_disposition, flags=re.IGNORECASE)
    if match:
        return _sanitize_filename(_decode_filename(match.group(1)))
    match = re.search(r'filename="?([^";]+)"?', content_disposition, flags=re.IGNORECASE)
    if match:
        return _sanitize_filename(_decode_filename(match.group(1)))
    return None


def resolve_filename(url: str, content_type: str | None, content_disposition: str | None, fallback: str | None = None) -> str:
    by_header = _filename_from_content_disposition(content_disposition)
    if by_header:
        return by_header

    if fallback:
        base_name = _sanitize_filename(_decode_filename(fallback))
    else:
        path_name = _decode_filename(Path(urlparse(url).path).name)
        base_name = _sanitize_filename(path_name or "downloaded_file")

    if "." in base_name:
        return base_name

    if content_type:
        extension = mimetypes.guess_extension(content_type.split(";")[0].strip().lower())
        if extension:
            return f"{base_name}{extension}"

    return base_name


def save_bytes(output_dir: Path, filename: str, payload: bytes) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / filename
    stem = target.stem
    suffix = target.suffix
    index = 1
    while target.exists():
        target = output_dir / f"{stem}_{index}{suffix}"
        index += 1
    target.write_bytes(payload)
    return target
