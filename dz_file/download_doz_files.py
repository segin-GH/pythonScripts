#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any


DEFAULT_API_KEY = "a6emunQqzxzxyCCZihRZ"
DEFAULT_API_BASE_URL = "https://api.dozee.cloud/api/rawfiles/request"
US_API_BASE_URL = "https://api-us.dozee.cloud/api/rawfiles/request"
DEFAULT_FILE_TYPE = "pzo"
DEFAULT_POLL_INTERVAL = 10.0
DEFAULT_TIMEOUT = 600.0
PROCESSING_STATUSES = {"processing", "pending", "queued", "in_progress"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Submit a Dozee rawfiles request, poll for completion, and download the "
            "returned ZIP files."
        )
    )
    parser.add_argument(
        "--api-key",
        default=DEFAULT_API_KEY,
        help="Dozee API key. Defaults to the embedded key in this script.",
    )
    parser.add_argument(
        "--us",
        action="store_true",
        help="Use the US API host (api-us.dozee.cloud) instead of the default host.",
    )
    parser.add_argument(
        "--file-type",
        default=DEFAULT_FILE_TYPE,
        help=f"File type to request. Default: {DEFAULT_FILE_TYPE}.",
    )
    parser.add_argument(
        "--request-file",
        type=Path,
        help="JSON file containing the POST body as a list of request objects.",
    )
    parser.add_argument(
        "--item",
        action="append",
        nargs=3,
        metavar=("DEVICE_ID", "FROM", "TO"),
        help=(
            "One request item. Can be supplied multiple times. "
            "Example: --item <device-id> 2026-02-14T00:00:00Z 2026-02-15T01:00:00Z"
        ),
    )
    parser.add_argument(
        "--request-id",
        help="Existing request_id to poll and download without submitting a new POST request.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("downloads"),
        help="Directory where request results, ZIPs, and extracted files will be stored.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL,
        help=f"Seconds between polling attempts. Default: {DEFAULT_POLL_INTERVAL}.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Maximum seconds to wait for the request result. Default: {DEFAULT_TIMEOUT}.",
    )
    parser.add_argument(
        "--no-extract",
        action="store_true",
        help="Download ZIP files only and do not extract them.",
    )
    parser.add_argument(
        "--delete-zip-after-extract",
        action="store_true",
        help="Delete each ZIP after extraction completes successfully.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing ZIPs and extracted folders.",
    )
    return parser


def parse_args() -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args()

    if not args.api_key:
        parser.error("missing API key; use --api-key or set DOZEE_API_KEY")

    has_new_request = args.request_file is not None or args.item
    if not args.request_id and not has_new_request:
        parser.error(
            "provide either --request-id, --request-file, or at least one --item"
        )

    if args.request_id and has_new_request:
        parser.error(
            "use --request-id by itself, or provide a new request via --request-file/--item"
        )

    if args.poll_interval <= 0:
        parser.error("--poll-interval must be greater than 0")

    if args.timeout <= 0:
        parser.error("--timeout must be greater than 0")

    return args


def load_request_items(args: argparse.Namespace) -> list[dict[str, str]]:
    if args.request_file is not None:
        try:
            payload = json.loads(args.request_file.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise SystemExit(f"request file not found: {args.request_file}") from exc
        except json.JSONDecodeError as exc:
            raise SystemExit(
                f"invalid JSON in request file {args.request_file}: {exc}"
            ) from exc
    else:
        payload = [
            {"DeviceId": device_id, "From": from_ts, "To": to_ts}
            for device_id, from_ts, to_ts in args.item or []
        ]

    validate_request_items(payload)
    return payload


def validate_request_items(payload: Any) -> None:
    if not isinstance(payload, list) or not payload:
        raise SystemExit("request payload must be a non-empty JSON list")

    required_keys = {"DeviceId", "From", "To"}
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise SystemExit(f"request item #{index} must be a JSON object")

        missing = sorted(required_keys - item.keys())
        if missing:
            raise SystemExit(
                f"request item #{index} is missing keys: {', '.join(missing)}"
            )

        for key in required_keys:
            value = item[key]
            if not isinstance(value, str) or not value.strip():
                raise SystemExit(f"request item #{index} has an invalid {key!r} value")


def api_call(
    method: str,
    url: str,
    api_key: str,
    payload: Any | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(url=url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode(response.headers.get_content_charset("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"{method} {url} failed with HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"{method} {url} failed: {exc.reason}") from exc

    if not raw.strip():
        return {}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{method} {url} returned invalid JSON: {raw}") from exc

    if not isinstance(parsed, dict):
        raise SystemExit(f"{method} {url} returned unexpected JSON: {parsed!r}")

    return parsed


def get_api_base_url(use_us_host: bool) -> str:
    return US_API_BASE_URL if use_us_host else DEFAULT_API_BASE_URL


def submit_request(
    items: list[dict[str, str]],
    api_key: str,
    file_type: str,
    api_base_url: str,
) -> dict[str, Any]:
    query = urllib.parse.urlencode({"fileType": file_type})
    url = f"{api_base_url}?{query}"
    return api_call("POST", url, api_key, payload=items)


def poll_result(
    request_id: str,
    api_key: str,
    poll_interval: float,
    timeout: float,
    api_base_url: str,
) -> dict[str, Any]:
    url = f"{api_base_url}/result/{request_id}"
    deadline = time.monotonic() + timeout
    attempt = 1

    while True:
        result = api_call("GET", url, api_key)
        files = result.get("files")
        status = str(result.get("status", "")).strip().lower()

        if isinstance(files, list):
            if files:
                print(
                    f"Request ready on poll attempt {attempt}: {len(files)} file(s) available."
                )
                return result

            if status and status not in PROCESSING_STATUSES:
                print(
                    f"Request completed on poll attempt {attempt}: no files returned."
                )
                return result

        if status and status not in PROCESSING_STATUSES:
            print(f"Request returned status={status!r} on poll attempt {attempt}.")
            return result

        if time.monotonic() >= deadline:
            raise SystemExit(
                f"timed out after {timeout:.0f}s waiting for request_id {request_id}"
            )

        print(
            f"Poll attempt {attempt}: request is still processing; waiting {poll_interval:.1f}s..."
        )
        time.sleep(poll_interval)
        attempt += 1


def sanitize(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "unknown"


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def download_to_file(url: str, destination: Path, overwrite: bool) -> None:
    if destination.exists() and not overwrite:
        print(f"Skipping existing ZIP: {destination}")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=300) as response, destination.open(
            "wb"
        ) as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"download failed with HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"download failed: {exc.reason}") from exc


def extract_zip(zip_path: Path, extract_dir: Path, overwrite: bool) -> None:
    if extract_dir.exists() and any(extract_dir.iterdir()) and not overwrite:
        print(f"Skipping existing extract directory: {extract_dir}")
        return

    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(extract_dir)


def download_results(
    result: dict[str, Any],
    output_dir: Path,
    extract_archives: bool,
    delete_zip_after_extract: bool,
    overwrite: bool,
) -> int:
    request_id = str(result.get("request_id") or "unknown_request")
    request_dir = output_dir / request_id
    zips_dir = request_dir / "zips"
    extracted_dir = request_dir / "extracted"

    request_dir.mkdir(parents=True, exist_ok=True)
    zips_dir.mkdir(parents=True, exist_ok=True)
    if extract_archives:
        extracted_dir.mkdir(parents=True, exist_ok=True)

    save_json(request_dir / "result.json", result)

    files = result.get("files")
    if not isinstance(files, list):
        raise SystemExit("result payload does not contain a valid 'files' list")

    downloaded = 0

    for index, file_info in enumerate(files, start=1):
        if not isinstance(file_info, dict):
            raise SystemExit(f"result file entry #{index} is not a JSON object")

        url = file_info.get("url")
        if not isinstance(url, str) or not url.strip():
            raise SystemExit(f"result file entry #{index} is missing a valid URL")

        job_id = sanitize(str(file_info.get("job_id") or f"job_{index}"))
        device_id = sanitize(str(file_info.get("device_id") or "unknown_device"))
        from_ts = sanitize(str(file_info.get("from") or "from"))
        to_ts = sanitize(str(file_info.get("to") or "to"))

        zip_name = f"{device_id}_{from_ts}_{to_ts}_{job_id}.zip"
        zip_path = zips_dir / zip_name

        print(f"Downloading file #{index} to {zip_path}")
        download_to_file(url, zip_path, overwrite=overwrite)
        downloaded += 1

        if extract_archives:
            extract_path = extracted_dir / job_id
            print(f"Extracting file #{index} into {extract_path}")
            extract_zip(zip_path, extract_path, overwrite=overwrite)

            if delete_zip_after_extract:
                zip_path.unlink(missing_ok=True)

    return downloaded


def main() -> int:
    args = parse_args()

    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    api_base_url = get_api_base_url(args.us)

    request_payload: list[dict[str, str]] | None = None

    if args.request_id:
        request_id = args.request_id
        print(f"Using existing request_id: {request_id}")
    else:
        request_payload = load_request_items(args)
        print(
            f"Submitting request with {len(request_payload)} item(s), fileType={args.file_type!r}, "
            f"host={api_base_url}."
        )
        submit_response = submit_request(
            request_payload,
            args.api_key,
            args.file_type,
            api_base_url,
        )
        request_id = str(submit_response.get("request_id") or "").strip()
        if not request_id:
            raise SystemExit(
                f"submit response did not contain request_id: {submit_response}"
            )
        print(f"Submitted request_id: {request_id}")

        save_json(output_dir / request_id / "submit_response.json", submit_response)
        save_json(output_dir / request_id / "request_payload.json", request_payload)

    result = poll_result(
        request_id=request_id,
        api_key=args.api_key,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
        api_base_url=api_base_url,
    )

    download_count = download_results(
        result=result,
        output_dir=output_dir,
        extract_archives=not args.no_extract,
        delete_zip_after_extract=args.delete_zip_after_extract,
        overwrite=args.overwrite,
    )

    print(f"Finished. Downloaded {download_count} file(s) for request_id {request_id}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
