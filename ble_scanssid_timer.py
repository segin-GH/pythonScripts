#! /usr/bin/python3

import argparse
import asyncio
import re
import sys
import time

from bleak import BleakClient, BleakScanner
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


CMD_CHARACTERISTIC_UUID = "0000FF01-0000-1000-8000-00805F9B34FB"
SCAN_COMMAND = "SCANSSIDS"
SSID_RESPONSE_RE = re.compile(r"\bssids:(\d+)\b")

console = Console()


def parse_args():
    parser = argparse.ArgumentParser(description="Measure BLE SCANSSIDS response time")
    parser.add_argument(
        "-n",
        "--name",
        type=str,
        default="DOZ-10007",
        help="BLE device name substring, e.g. DOZ-10007",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Seconds to wait for ssids:<count> and all SSID entries before failing",
    )
    parser.add_argument(
        "--scan-timeout",
        type=float,
        default=5.0,
        help="Seconds to scan for the BLE device",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.2,
        help="Seconds to wait between characteristic reads",
    )
    parser.add_argument(
        "-i",
        "--iterations",
        type=int,
        default=20,
        help="Number of complete SCANSSIDS tests to run",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to wait between test iterations",
    )
    return parser.parse_args()


async def find_device(device_name, scan_timeout):
    console.print(Panel(f"[bold cyan]Scanning for {device_name}[/bold cyan]"))
    devices = await BleakScanner.discover(timeout=scan_timeout)

    for device in devices:
        if device.name and device_name in device.name:
            console.print(
                f"[bold green]Found device:[/bold green] "
                f"{device.name} [blue][{device.address}][/blue]"
            )
            return device.address

    console.print("[bold red]Device not found[/bold red]")
    return None


async def send_command(client, command):
    await client.write_gatt_char(CMD_CHARACTERISTIC_UUID, command.encode("utf-8"))


async def receive_response(client):
    response = await client.read_gatt_char(CMD_CHARACTERISTIC_UUID)
    return response.decode("utf-8", errors="replace").strip("\x00\r\n\t ")


def split_response_entries(response):
    return [entry.strip() for entry in response.splitlines() if entry.strip()]


async def wait_for_scan_result(client, timeout, poll_interval):
    started_at = time.perf_counter()
    expected_ssid_count = None
    ssids = []

    await send_command(client, SCAN_COMMAND)
    console.print(f"[bold yellow]> {SCAN_COMMAND}[/bold yellow]")

    while True:
        elapsed = time.perf_counter() - started_at
        remaining = timeout - elapsed

        if remaining <= 0:
            return {
                "status": "timeout",
                "elapsed": elapsed,
                "response": None,
                "expected_ssid_count": expected_ssid_count,
                "ssids": ssids,
            }

        try:
            response = await asyncio.wait_for(
                receive_response(client), timeout=remaining
            )
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "elapsed": time.perf_counter() - started_at,
                "response": None,
                "expected_ssid_count": expected_ssid_count,
                "ssids": ssids,
            }

        now = time.perf_counter()
        elapsed = now - started_at
        console.print(f"[bold cyan]< {response}[/bold cyan]")

        if "INVALID" in response.upper():
            return {
                "status": "invalid",
                "elapsed": elapsed,
                "response": response,
                "expected_ssid_count": expected_ssid_count,
                "ssids": ssids,
            }

        match = SSID_RESPONSE_RE.search(response)
        if expected_ssid_count is None and match:
            expected_ssid_count = int(match.group(1))
            console.print(
                f"[bold green]Expecting {expected_ssid_count} SSID entries[/bold green]"
            )
            if expected_ssid_count == 0:
                return {
                    "status": "success",
                    "elapsed": elapsed,
                    "response": response,
                    "expected_ssid_count": expected_ssid_count,
                    "ssids": ssids,
                }

        elif expected_ssid_count is not None:
            for entry in split_response_entries(response):
                if SSID_RESPONSE_RE.search(entry):
                    continue
                ssids.append(entry)
                console.print(
                    f"[bold green]SSID {len(ssids)}/{expected_ssid_count}: "
                    f"{entry}[/bold green]"
                )
                if len(ssids) >= expected_ssid_count:
                    return {
                        "status": "success",
                        "elapsed": elapsed,
                        "response": response,
                        "expected_ssid_count": expected_ssid_count,
                        "ssids": ssids,
                    }

        await asyncio.sleep(min(poll_interval, max(0.0, timeout - elapsed)))


async def run(args):
    if args.iterations <= 0:
        console.print("[bold red]Iterations must be greater than 0[/bold red]")
        return 1

    address = await find_device(args.name, args.scan_timeout)
    if not address:
        return 1

    results = []

    async with BleakClient(address) as client:
        if not client.is_connected:
            console.print("[bold red]Failed to connect to device[/bold red]")
            return 1

        console.print("[bold green]Connected[/bold green]")
        for iteration in range(1, args.iterations + 1):
            console.print(
                Panel(
                    f"[bold cyan]Run {iteration}/{args.iterations}[/bold cyan]",
                    title="SCANSSIDS Test",
                )
            )
            result = await wait_for_scan_result(
                client, args.timeout, args.poll_interval
            )
            results.append(result)

            elapsed_ms = result["elapsed"] * 1000
            collected = len(result["ssids"])
            expected = (
                str(result["expected_ssid_count"])
                if result["expected_ssid_count"] is not None
                else "-"
            )
            if result["status"] == "success":
                console.print(
                    f"[bold green]Run {iteration} complete:[/bold green] "
                    f"{elapsed_ms:.2f} ms, collected {collected}/{expected}"
                )
            else:
                console.print(
                    f"[bold red]Run {iteration} {result['status']}:[/bold red] "
                    f"{elapsed_ms:.2f} ms, collected {collected}/{expected}"
                )

            if iteration < args.iterations:
                await asyncio.sleep(args.delay)

    table = Table(title="SCANSSIDS Test Results")
    table.add_column("Run", justify="right")
    table.add_column("Status")
    table.add_column("Elapsed (ms)", justify="right")
    table.add_column("Collected")

    for index, result in enumerate(results, start=1):
        expected = (
            str(result["expected_ssid_count"])
            if result["expected_ssid_count"] is not None
            else "-"
        )
        table.add_row(
            str(index),
            result["status"],
            f"{result['elapsed'] * 1000:.2f}",
            f"{len(result['ssids'])}/{expected}",
        )

    console.print(table)

    success_times = [
        result["elapsed"] for result in results if result["status"] == "success"
    ]
    failures = len(results) - len(success_times)
    if success_times:
        mean_s = sum(success_times) / len(success_times)
        console.print(
            Panel(
                f"Total runs: [cyan]{len(results)}[/cyan]\n"
                f"Success: [cyan]{len(success_times)}[/cyan]\n"
                f"Failures: [cyan]{failures}[/cyan]\n"
                f"Mean complete time: [cyan]{mean_s:.3f} s[/cyan] "
                f"([cyan]{mean_s * 1000:.2f} ms[/cyan])\n"
                f"Min complete time: [cyan]{min(success_times):.3f} s[/cyan]\n"
                f"Max complete time: [cyan]{max(success_times):.3f} s[/cyan]",
                title="Summary",
            )
        )
    else:
        console.print(
            Panel(
                f"Total runs: [cyan]{len(results)}[/cyan]\n"
                f"Success: [cyan]0[/cyan]\n"
                f"Failures: [cyan]{failures}[/cyan]\n"
                "[bold red]Mean complete time unavailable: no successful runs[/bold red]",
                title="Summary",
            )
        )

    return 1 if failures else 0


def main():
    args = parse_args()
    try:
        return asyncio.run(run(args))
    except KeyboardInterrupt:
        console.print("\n[bold red]Interrupted[/bold red]")
        return 130


if __name__ == "__main__":
    sys.exit(main())
