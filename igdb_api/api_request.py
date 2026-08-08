"""
IDGB API Handler
- Set up request bodies in json files
- Send json files through the API manager
- Retreive data via the API
- Save data to specified file format (default csv)
"""

import csv
import json
import logging
import os
from argparse import ArgumentParser, ArgumentTypeError, Namespace
from datetime import UTC, datetime
from pathlib import Path
import platform
from typing import Any

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO
)

from api_manager import IGDBAPIManager
from dotenv import load_dotenv

_VALID_OUTPUT_TYPES = [
    "json",
    "csv",
]

def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "--endpoint", "-e",
        type=str, default="games"
    )
    def _is_valid_json_file(path: Path) -> bool:
        return (
            path.is_file()
            and path.suffix.startswith(".json") # might wanna handle jsonc and jsonl at some point
        )
    def json_or_path(value: str) -> dict[str, Any]:
        if _is_valid_json_file(pth := Path(value).resolve()):
            value = pth.read_text()
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise ArgumentTypeError(
                "Unable to decode the following argument to json: "
                + repr(value) + f"\nThis caused the following error: {e}"
            )
    parser.add_argument(
        "--request-body", "-r",
        type=json_or_path,
        help="API request body"
    )
    parser.add_argument(
        "--output-type", "-o",
        type=str, default="json",
        choices=_VALID_OUTPUT_TYPES
    )
    parser.add_argument(
        "--dotenv",
        type=Path, default=Path.cwd() / ".env"
    )
    args = parser.parse_args()
    return args

def convert_to_output(
    request_result: list[dict[str, Any]],
    output_type: str,
    output_directory: Path | None = None,
    output_file_name: str | None = None,
) -> Path:
    if output_directory is None:
        output_directory = Path.cwd() / "request_results"
    output_directory.mkdir(parents=True, exist_ok=True)
    if output_file_name is None:
        output_file_name = datetime.now(UTC).isoformat(
            timespec="seconds"
        ).split("+")[0]
    if platform.system().lower() == "windows":
        output_file_name = output_file_name.replace(":","-")
    output_path = (output_directory / output_file_name).with_suffix(
        f".{output_type}"
    )
    logger.info(
        "Output path: %s", output_path
    )
    if output_type == "json":
        output_path.write_text(json.dumps(request_result))
    elif output_type == "csv":
        with open(output_path) as f:
            writer = csv.writer(f)
            writer.writerows(request_result) # will need some extra conversion step before this
    else:
        raise ValueError(
            f"Unsupported output type: {output_type!r}"
        )
    return output_path

def _load_secrets(env_path: Path | None = None) -> bool:
    if env_path is None:
        env_path = Path.cwd() / ".env"
    if not env_path.is_file():
        raise FileNotFoundError(env_path)
    loaded = load_dotenv(env_path)
    if not loaded:
        raise RuntimeError(
            f"Unable to load env file at {env_path}"
        )
    return loaded

def main():
    args = parse_args()
    env_pth = args.dotenv
    logger.info("Loading env file at %s", env_pth)
    try:
        _load_secrets(env_pth)
    except Exception as e:
        logger.error(e)
        raise
    api_manager = IGDBAPIManager(
        client_id=os.environ["igdb_client_id"],
        client_secret=os.environ["igdb_client_secret"],
    )
    endpoint: str = args.endpoint
    body: dict[str, Any] = args.request_body
    logger.info(
        "Submitting request to %s", endpoint
    )
    try:
        req_res: list[dict[str, Any]] = api_manager.post_request(
            endpoint=endpoint,
            data=body
        )
    except Exception as e:
        logger.info(e)
        raise
    output_type = args.output_type
    logger.info(
        "Converting request result to %s", output_type
    )
    try:
        output_path = convert_to_output(req_res, output_type)
    except Exception as e:
        logger.error(e)
        raise
    logger.info(
        "Output request results to %s",
        output_path
    )

if __name__ == '__main__':
    main()
