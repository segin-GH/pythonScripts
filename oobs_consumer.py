import json
import sys
from typing import Dict, Iterator, Optional
from datetime import datetime, timezone, timedelta
import requests

# ----------------------------------------------------
# CONSTANTS (your values)
# ----------------------------------------------------
HOST = "https://openobserve-in.dozee.ai"
ORG = "default"
SEARCH_PATH = "/api/{org}/_search"

SQL = """
SELECT * FROM "default"
WHERE body_log_data_devicename = 'S1-787'
"""

PAGE_SIZE = 500
TIMEOUT = 10000
# ----------------------------------------------------


def fetch_hits(
    user: str,
    password: str,
    start_us: int,
    end_us: int,
    offset: int = 0,
    page_size: int = PAGE_SIZE,
    session: Optional[requests.Session] = None,
) -> Dict:
    """Fetch one page from OpenObserve search API."""
    url = HOST + SEARCH_PATH.format(org=ORG)

    payload = {
        "query": {
            "sql": SQL,
            "start_time": start_us,
            "end_time": end_us,
            "from": offset,
            "size": page_size,
        },
        "search_type": "ui",
    }

    headers = {"Content-Type": "application/json"}

    close_session = False
    if session is None:
        session = requests.Session()
        close_session = True

    try:
        resp = session.post(
            url,
            json=payload,
            auth=(user, password),
            headers=headers,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    finally:
        if close_session:
            session.close()


def extract_reduced_fields(hit: Dict) -> Dict:
    """Convert a full hit into your reduced NDJSON structure."""
    return {
        "body_level": hit.get("body_log_data_level"),
        "body_timestamp": hit.get("body_timestamp"),
        "body_seq": hit.get("body_log_data_seq"),
        "body_eventname": hit.get("body_log_data_eventname"),
        "body_eventtype": hit.get("body_log_data_eventtype"),
        "body_value": hit.get("body_log_data_value"),
    }


def ndjson_stream(
    user: str,
    password: str,
    start_us: int,
    end_us: int,
    page_size: int = PAGE_SIZE,
) -> Iterator[str]:
    """Yield NDJSON lines for all hits in the given time range."""
    offset = 0
    session = requests.Session()

    try:
        while True:
            data = fetch_hits(
                user=user,
                password=password,
                start_us=start_us,
                end_us=end_us,
                offset=offset,
                page_size=page_size,
                session=session,
            )

            hits = data.get("hits", [])
            print(f"# Fetched {len(hits)} records (offset={offset})", file=sys.stderr)

            if not hits:
                break

            for h in hits:
                yield h

            count = len(hits)
            offset += count
            if count < page_size:
                break
    finally:
        session.close()


def export_filtered_ndjson(
    user: str,
    password: str,
    start_us: int,
    end_us: int,
    out_file: Optional[str] = None,
    page_size: int = PAGE_SIZE,
) -> int:
    """Write NDJSON data (stdout or file). Returns number of records written."""
    total = 0

    if out_file:
        fout = open(out_file, "w", encoding="utf-8", newline="")
    else:
        fout = sys.stdout

    try:
        for line in ndjson_stream(
            user=user,
            password=password,
            start_us=start_us,
            end_us=end_us,
            page_size=page_size,
        ):
            fout.write(line + "\n")
            total += 1
    finally:
        if out_file:
            fout.close()

    return total


def now_us():
    return int(datetime.now(timezone.utc).timestamp() * 1_000_000)


def us_days_ago(days):
    return int(
        (datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1_000_000
    )


def us_hours_ago(hours):
    return int(
        (datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp() * 1_000_000
    )


def us_minutes_ago(minutes):
    return int(
        (datetime.now(timezone.utc) - timedelta(minutes=minutes)).timestamp()
        * 1_000_000
    )


# Example usage:
if __name__ == "__main__":
    USER = "aziz@dozee.io"
    PASS = "Password@1234"

    START_US = us_days_ago(7)
    END_US = us_days_ago(5)

    count = export_filtered_ndjson(USER, PASS, START_US, END_US)
    print(f"Exported {count} records.")
