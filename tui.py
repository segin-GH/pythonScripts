"""
Textual NDJSON Viewer
"""

import os
import sys
import time
import json
import threading
import queue
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Header, Footer, Static, Log
from textual.containers import Horizontal
from textual.reactive import reactive

from oobs_consumer import ndjson_stream, now_us, us_days_ago

# Configuration
QUEUE_MAX_SIZE = 50000
CONSUME_BATCH = 500  # max rows to dequeue per tick
CONSUME_INTERVAL = 0.15  # seconds between UI dequeues
ARCHIVE_PATH = os.environ.get("NDJSON_ARCHIVE")  # optional archive file path
NDJSON_FILE = os.environ.get("NDJSON_FILE")  # optional file to tail


class DropOldestQueue(queue.Queue):
    """Bounded queue with drop-oldest-on-full policy.

    If the queue is full when `put` is called, the oldest item is removed to
    make room for the new one. This avoids blocking the producer indefinitely
    and keeps recent data prioritized for the UI.
    """

    def put(self, item, block=True, timeout=None):
        try:
            super().put(item, block=False)
        except queue.Full:
            try:
                # drop a single oldest item
                _ = self.get_nowait()
            except queue.Empty:
                pass
            # try to put again (should succeed)
            try:
                super().put(item, block=False)
            except queue.Full:
                # last resort: drop the incoming item
                return


class NDJSONViewer(App):
    CSS_PATH = None
    BINDINGS = [("p", "toggle_pause", "Pause/Resume live feed"), ("q", "quit", "Quit")]

    paused = reactive(False)
    queued = reactive(0)

    def __init__(
        self, q: DropOldestQueue, archive_path: Optional[str] = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.q = q
        self.archive_path = archive_path
        self.table: Optional[DataTable] = None
        self.status: Optional[Static] = None
        self._archive_file = None
        if archive_path:
            # open archive in append mode
            self._archive_file = open(archive_path, "a", encoding="utf-8")

    def compose(self) -> ComposeResult:
        yield Header()
        # Horizontal container to allow future expansion (filters / details)
        with Horizontal():
            self.table = DataTable(
                zebra_stripes=False,
                cell_padding=4,
                show_header=True,
                cursor_type="row",
            )
            self.table.add_columns("Level", "Timestamp", "Seq", "Type", "Name", "Value")
            yield self.table
        # small status widget in footer area
        self.status = Static("queued=0 paused=False total=0", expand=False)
        yield self.status
        yield Footer()

    def on_mount(self) -> None:
        # schedule the periodic consumer on the Textual event loop
        self.set_interval(CONSUME_INTERVAL, self.consume_queue)

    async def consume_queue(self) -> None:
        if self.paused:
            self.queued = self.q.qsize()
            self._update_status()
            return

        rows = []
        drained = 0

        while drained < CONSUME_BATCH:
            try:
                item = self.q.get_nowait()
            except queue.Empty:
                break

            drained += 1

            rows.append(
                (
                    item.get("body_level"),
                    item.get("body_timestamp"),
                    item.get("body_seq"),
                    item.get("body_eventtype"),
                    item.get("body_eventname"),
                    item.get("body_value"),
                )
            )

            # optional archive
            if self._archive_file:
                try:
                    self._archive_file.write(json.dumps(item) + "\n")
                except Exception:
                    pass

        # Add rows directly to table
        if rows:
            for r in rows:
                self.table.add_row(*[str(x) for x in r])

        self.queued = self.q.qsize()
        self._update_status()

    def _update_status(self) -> None:
        if self.status:
            total_rows = len(self.table.rows) if self.table else 0
            self.status.update(
                f"queued={self.queued} paused={self.paused} total={total_rows}"
            )

    def action_toggle_pause(self) -> None:
        self.paused = not self.paused
        self._update_status()

    # Clean up archive file
    def on_unmount(self) -> None:
        if self._archive_file:
            try:
                self._archive_file.flush()
                self._archive_file.close()
            except Exception:
                pass


# Producer function to pull from OOBS
def pull_from_oobs(
    q: "DropOldestQueue",
    relative_day: int = 1,
    live_interval: float = 1.0,
    live_mode: bool = True,
) -> None:
    """
    Mutually exclusive modes:
    - If live_mode is False: Pulls historical data from relative_day ago until now, then exits.
    - If live_mode is True: Ignores history, starts polling from 'now' indefinitely.
    """

    # Helper to get current time (assuming this function exists in your scope)
    current_time_us = now_us()

    # --- MODE 1: Historical Pull Only ---
    if not live_mode:
        start_us = us_days_ago(relative_day)
        end_us = current_time_us

        print(f"Starting Historical Pull: {start_us} to {end_us}")

        try:
            for line in ndjson_stream(
                user="aziz@dozee.io",
                password="Password@1234",
                start_us=start_us,
                end_us=end_us,
                page_size=5000,
            ):
                try:
                    raw = json.loads(line)
                except Exception:
                    continue  # skip malformed lines

                q.put(raw)
        except Exception as e:
            # Log error if necessary
            print(f"Historical pull failed: {e}")

        # STOP here if we are not in live mode
        return

    # --- MODE 2: Live Mode Only ---
    else:
        # Initialize pointer to NOW so we don't pull history
        last_seen_us = current_time_us
        print(f"Starting Live Mode from: {last_seen_us}")

        while True:
            try:
                poll_start = last_seen_us + 1
                poll_end = now_us()

                # Guard: only call stream if time has actually passed
                if poll_end >= poll_start:
                    for line in ndjson_stream(
                        user="aziz@dozee.io",
                        password="Password@1234",
                        start_us=poll_start,
                        end_us=poll_end,
                        page_size=5000,
                    ):
                        try:
                            raw = json.loads(line)
                        except Exception:
                            continue

                        q.put(raw)

                    # Update the pointer *after* successfully processing the batch window
                    last_seen_us = poll_end

                # Sleep between polls
                time.sleep(live_interval)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                # Log transient errors
                # print(f"Live poll error: {e}")
                time.sleep(live_interval)
                continue


def tail_file_producer(
    q: DropOldestQueue, file_path: str, poll_interval: float = 0.1
) -> None:
    """Tail an NDJSON file and enqueue normalized records.

    - Handles the common case where the file is being appended by another process.
    - On JSON parse errors, the line is skipped.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # seek to end so we only read new lines
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(poll_interval)
                    continue
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                except Exception:
                    # skip malformed line
                    continue
                q.put(raw)
    except FileNotFoundError:
        # nothing to tail; exit thread
        return


def start_producers(
    q: DropOldestQueue,
    relative_day: int = 1,
    live_interval: float = 1.0,
    live_mode: bool = True,
) -> None:
    """Start chosen producers in background threads. Uses NDJSON_FILE env to decide.

    If NDJSON_FILE is set, the file tail producer starts. Otherwise, the
    simulator starts.
    """
    if NDJSON_FILE:
        t = threading.Thread(
            target=tail_file_producer, args=(q, NDJSON_FILE), daemon=True
        )
        t.start()
    else:
        t = threading.Thread(
            target=pull_from_oobs,
            args=(
                q,
                relative_day,
                live_interval,
                live_mode,
            ),
            daemon=True,
        )
        t.start()


def main():
    relative_day = 1

    q = DropOldestQueue(maxsize=QUEUE_MAX_SIZE)
    # start producers
    start_producers(q, relative_day=relative_day, live_interval=1.0, live_mode=False)

    # start textual app (archive path optional)
    app = NDJSONViewer(q=q, archive_path=ARCHIVE_PATH)
    app.run()


if __name__ == "__main__":
    main()
