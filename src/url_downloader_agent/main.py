import argparse
import json

from dotenv import load_dotenv

from .agent import URLDownloaderAgent
from .config import Settings


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Automated URL file downloader agent")
    parser.add_argument("--message", required=True, help="Natural language message containing a URL")
    parser.add_argument(
        "--mode",
        choices=["deterministic", "langchain"],
        default="deterministic",
        help="Execution mode",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    agent = URLDownloaderAgent(settings)

    if args.mode == "deterministic":
        result = agent.process_message(args.message)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    executor = agent.build_langchain_executor()
    output = executor({"input": args.message})
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
