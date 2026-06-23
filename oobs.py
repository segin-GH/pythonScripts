#!/usr/bin/env python3
import os
import sys
import argparse
import requests
import csv
from datetime import datetime, timezone, timedelta
import json

HOST = "https://openobserve-in.dozee.ai"
ORG = "default"
SEARCH_PATH = "/api/{org}/_search"

SQL = """
SELECT * FROM "default"
WHERE body_log_data_devicename = 'S1-748'
"""


def iso_to_us(s):
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000)


def now_us():
    return int(datetime.now(timezone.utc).timestamp() * 1_000_000)


def us_days_ago(days):
    return int(
        (datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1_000_000
    )


def export_csv_print(user, password, start_us, end_us, page_size=5000):
    url = HOST + SEARCH_PATH.format(org=ORG)
    headers = {"Content-Type": "application/json"}

    offset = 0
    total = 0
    fields_written = False
    field_order = []

    writer = csv.writer(sys.stdout)

    while True:
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

        r = requests.post(
            url, json=payload, auth=(user, password), headers=headers, timeout=1000
        )

        r.raise_for_status()
        hits = r.json().get("hits", [])

        print(f"# Fetched {len(hits)} records (offset={offset})", file=sys.stderr)
        if not hits:
            break

        # Print header once
        if not fields_written:
            sample = hits[0]
            field_order = list(sample.keys())
            fields_written = True

        # Print rows
        for h in hits:
            row = []
            for key in field_order:
                val = h.get(key, "")
                if isinstance(val, (dict, list)):
                    val = json.dumps(val, ensure_ascii=False)
                row.append(val)

        n = len(hits)
        total += n
        offset += n

        if n < page_size:
            break

    return total


def export_json_print(user, password, start_us, end_us, page_size=5000):
    url = HOST + SEARCH_PATH.format(org=ORG)
    headers = {"Content-Type": "application/json"}

    offset = 0
    total = 0

    while True:
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

        r = requests.post(
            url, json=payload, auth=(user, password), headers=headers, timeout=1000
        )
        r.raise_for_status()

        hits = r.json().get("hits", [])

        print(f"# Fetched {len(hits)} records (offset={offset})", file=sys.stderr)

        if not hits:
            break

        # 🔥 Print each full record as JSON
        for h in hits:
            print(json.dumps(h, ensure_ascii=False))

        n = len(hits)
        total += n
        offset += n

        if n < page_size:
            break

    return total


def export_filtered_ndjson(user, password, start_us, end_us, page_size=5000):
    """
    Fetch pages from the search API and print one NDJSON line per record,
    containing only the requested fields:
      - body_level        (from body_log_level)
      - body_timestamp    (from body_timestamp)
      - body_seq          (from body_log_data_seq)
      - body_eventname    (from body_log_data_eventname)
      - body_eventtype    (from body_log_data_eventtype)
      - body_value        (from body_log_data_value)

    Returns total number of records printed.
    """
    url = HOST + SEARCH_PATH.format(org=ORG)
    headers = {"Content-Type": "application/json"}

    offset = 0
    total = 0

    while True:
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

        r = requests.post(
            url, json=payload, auth=(user, password), headers=headers, timeout=1000
        )
        r.raise_for_status()

        hits = r.json().get("hits", [])
        print(f"# Fetched {len(hits)} records (offset={offset})", file=sys.stderr)

        if not hits:
            break

        for h in hits:
            out = {
                "body_level": h.get("body_log_data_level"),
                "body_timestamp": h.get("body_timestamp"),
                "body_seq": h.get("body_log_data_seq"),
                "body_eventname": h.get("body_log_data_eventname"),
                "body_eventtype": h.get("body_log_data_eventtype"),
                "body_value": h.get("body_log_data_value"),
            }
            # Print as NDJSON (one JSON object per line)
            print(json.dumps(out, ensure_ascii=False))

        n = len(hits)
        total += n
        offset += n

        if n < page_size:
            break

    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", "-u", default=os.getenv("OO_USER"))
    parser.add_argument("--pass", "-p", dest="password", default=os.getenv("OO_PASS"))
    parser.add_argument("--start", help="Start ISO datetime")
    parser.add_argument("--end", help="End ISO datetime")
    parser.add_argument(
        "--last-days", type=int, help="Export last N days (overrides start/end)"
    )
    parser.add_argument("--out", "-o", default="ping_fail_logs.csv")
    args = parser.parse_args()

    if not args.user or not args.password:
        print("ERROR: Provide --user and --pass or set OO_USER / OO_PASS")
        sys.exit(1)

    # Handle last-days mode
    if args.last_days is not None:
        end_us = now_us()
        start_us = us_days_ago(args.last_days)
    else:
        # Manual start/end mode
        end_us = iso_to_us(args.end) if args.end else now_us()
        start_us = (
            iso_to_us(args.start)
            if args.start
            else (end_us - int(timedelta(days=1).total_seconds() * 1_000_000))
        )

    print("Running SQL query:")
    print(SQL)
    print()

    print("Time range (microseconds):")
    print(f"  start_us = {start_us}")
    print(f"  end_us   = {end_us}")
    print()

    print(f"Output file: {args.out}")

    # total = export_csv_print(args.user, args.password, start_us, end_us, page_size=5000)

    # total = export_json_print(
    #     args.user, args.password, start_us, end_us, page_size=5000
    # )

    total = export_filtered_ndjson(
        args.user, args.password, start_us, end_us, page_size=5000
    )
    print(f"Done. {total} rows written.")


if __name__ == "__main__":
    main()
