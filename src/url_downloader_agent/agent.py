from typing import Any, Callable

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import Settings
from .downloaders import GoogleDriveDownloader, MicrosoftDownloader, WebDownloader
from .models import DownloadResult, Platform
from .router import route_platform
from .url_extractor import extract_url_regex


class URLDownloaderAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.web_downloader = WebDownloader(settings)
        self.google_downloader = GoogleDriveDownloader(settings, self.web_downloader)
        self.microsoft_downloader = MicrosoftDownloader(settings, self.web_downloader)

    def extract_url(self, message: str) -> str | None:
        return extract_url_regex(message)

    def download_from_url(self, url: str) -> DownloadResult:
        platform = route_platform(url)
        if platform == Platform.GOOGLE_DRIVE:
            return self.google_downloader.download(url)
        if platform == Platform.MICROSOFT:
            return self.microsoft_downloader.download(url)
        return self.web_downloader.download(url, platform=Platform.WEB)

    def process_message(self, message: str) -> DownloadResult:
        url = self.extract_url(message)
        if not url:
            return DownloadResult(
                status="failed",
                source_platform=Platform.WEB,
                error="No URL found in the message.",
            )
        return self.download_from_url(url)

    def build_langchain_executor(self) -> Callable[[dict[str, str]], dict[str, Any]]:
        if not self.settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required for LangChain tool-calling executor.")

        instance = self

        @tool
        def extract_url_tool(message: str) -> str:
            """Extract a single URL from a natural language message."""
            url = instance.extract_url(message)
            return url or ""

        @tool
        def route_platform_tool(url: str) -> str:
            """Route URL to one of: google_drive, microsoft, web."""
            return route_platform(url).value

        @tool
        def download_url_tool(url: str) -> dict:
            """Download file from URL and return structured status."""
            result = instance.download_from_url(url)
            return result.to_dict()

        tools = [extract_url_tool, route_platform_tool, download_url_tool]
        tool_map = {tool.name: tool for tool in tools}

        llm = ChatGoogleGenerativeAI(
            model=self.settings.gemini_model,
            google_api_key=self.settings.google_api_key,
        )
        llm_with_tools = llm.bind_tools(tools)

        def invoke(input_dict: dict[str, str]) -> dict[str, Any]:
            messages = [
                HumanMessage(content=input_dict["input"])
            ]
            
            max_iterations = 10
            for _ in range(max_iterations):
                response = llm_with_tools.invoke(messages)
                messages.append(response)
                
                if not response.tool_calls:
                    return {
                        "input": input_dict["input"],
                        "output": response.content,
                        "messages": messages,
                    }
                
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    if tool_name in tool_map:
                        tool_result = tool_map[tool_name].invoke(tool_args)
                        messages.append(
                            ToolMessage(
                                content=str(tool_result),
                                tool_call_id=tool_call["id"],
                            )
                        )
            
            return {
                "input": input_dict["input"],
                "output": "Maximum iterations reached",
                "messages": messages,
            }
        
        return invoke
