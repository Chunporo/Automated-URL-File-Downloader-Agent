# URL Downloader Agent (LangChain)

Implements URL downloader agent with platform routing and secure download flow.

## Features

- Extracts URL from natural language input
- Routes by hostname:
  - `drive.google.com` -> Google Drive module
  - `onedrive.live.com`, `1drv.ms`, `*.sharepoint.com` -> Microsoft module
  - all others -> Web module
- Web flow uses `HEAD` pre-check, then binary download or HTML link discovery
- File post-processing:
  - MIME-based extension mapping
  - filename from `Content-Disposition` or provider metadata
  - unique file save in output directory

## Project Structure

- `src/url_downloader_agent/url_extractor.py` URL extraction
- `src/url_downloader_agent/router.py` platform routing
- `src/url_downloader_agent/downloaders.py` Google/Microsoft/Web modules
- `src/url_downloader_agent/file_store.py` MIME mapping and save logic
- `src/url_downloader_agent/agent.py` orchestration + LangChain tool-calling executor
- `src/url_downloader_agent/main.py` CLI entrypoint

## Setup

1. Install dependencies with `uv`:

```bash
uv sync
```

1. Copy env file:

```bash
cp .env.example .env
```

1. Update `.env` values as needed.

For LangChain mode, set `GOOGLE_API_KEY` and optionally `GEMINI_MODEL`.

## Run

Deterministic mode:

```bash
uv run url-downloader --message "please download https://example.com/file.pdf"
```

LangChain tool-calling mode:

```bash
uv run url-downloader --mode langchain --message "download this for me https://example.com/file.pdf"
```

## Authentication Constraints

- Google private files need OAuth2/Service Account flow and proper scopes
- OneDrive/SharePoint enterprise links typically require `MICROSOFT_GRAPH_TOKEN`
- Protected websites may require `WEB_BEARER_TOKEN`

Without valid access, the agent returns a structured failure error.
