
# Technical Specification: Automated URL File Downloader Agent

This document outlines the architecture and workflow for an AI agent capable of extracting URLs from natural language, identifying their source platforms, and executing secure downloads.

---

## 1. Input: Message Processing & Extraction
The agent acts as the first point of contact, receiving unstructured natural language input.

* **Objective**: Isolate the target URL from conversational noise.
* **Methods**:
    * **Regex Approach**: Use a pattern-matching string to identify `http://` or `https://` prefixes.
    * **LLM Tool Calling**: Define a function schema (e.g., `get_file_from_url(url: string)`) where the LLM parses the URL and passes it as a clean parameter.

---

## 2. Action: Analyze, Route, and Execute
The core logic functions as a "Traffic Controller," determining which protocol is required for the specific domain.

### Step A: Platform Determination (The Router)
The agent inspects the URL hostname to route the request to the appropriate module:

| Hostname / Domain | Target Module |
| :--- | :--- |
| `drive.google.com` | Google Drive Module |
| `onedrive.live.com` or `1drv.ms` | OneDrive Module |
| `[tenant].sharepoint.com` | SharePoint Module |
| All other domains | Direct Web Download Module |

### Step B: Execution Modules
Each module is specialized to handle the API quirks of its respective platform:

* **Google Drive Module**: Extracts the `file_id`. Utilizes the `drive.files.get` method. Handles the conversion of Google Workspace formats (Docs/Sheets) into standard exports (PDF/Docx/Xlsx).
* **Microsoft (OneDrive/SharePoint) Module**: Utilizes the **Microsoft Graph API**. It resolves sharing links into `driveItem` objects and streams the `driveItem.content`.
* **Web Module**: Performs a standard `HTTP GET`.
    * *Pre-check*: Sends a `HEAD` request to verify `Content-Type`.
    * *Logic*: If it is a file (e.g., PDF), it downloads directly. If it is HTML, it triggers a scraping sub-routine to find the download link.

---

## 3. Output: File Handling & Saving
Post-retrieval logic ensures the data is stored with integrity.

* **MIME-Type Mapping**: Reads headers (e.g., `application/pdf`) to assign the correct file extension.
* **Naming Convention**: Prioritizes `Content-Disposition` headers or API metadata over generic URL strings.
* **User Feedback**: Returns a confirmation message (e.g., *"File 'Q3_Report.xlsx' downloaded successfully."*)

---

## ⚠️ Crucial Constraint: Authentication
Authentication is the primary barrier to execution. Unless links are set to "Public/Anyone with link," the agent requires:

1.  **Google Workspace**: Service Account or OAuth2 tokens.
2.  **Microsoft Entra ID (Azure AD)**: Proper permissions for SharePoint/OneDrive enterprise environments.
3.  **Direct Web**: Support for Bearer tokens or API keys if the site is behind a paywall/login.


