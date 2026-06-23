#! /usr/bin/python3

import asyncio
import os
import argparse
import time
from bleak import BleakClient, BleakScanner
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table


parser = argparse.ArgumentParser(description="BLE Interactive CLI")
parser.add_argument(
    "-n",
    "--name",
    type=str,
    default="BSS-12345678",
    help="BLE device name e.g. BSS-12345678",
)
args = parser.parse_args()

DEVICE_NAME = args.name
CMD_CHARACTERISTIC_UUID = "0000FF01-0000-1000-8000-00805F9B34FB"

console = Console()


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


async def find_device():
    console.print(Panel(f"[bold cyan]Scanning for {DEVICE_NAME} [/bold cyan]"))
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name and DEVICE_NAME in device.name:
            console.print(
                f"[bold green]Found device:[/bold green] {device.name} [blue][{device.address}][/blue]"
            )
            return device.address
    console.print("[bold red]Device not found[/bold red]")
    return None


async def send_command(client, command):
    try:
        await client.write_gatt_char(CMD_CHARACTERISTIC_UUID, command.encode("utf-8"))
        return True
    except Exception as e:
        console.print(f"[bold red]Error sending command:[/bold red] {e}")
        return False


async def receive_response(client, silent=False):
    try:
        response = await client.read_gatt_char(CMD_CHARACTERISTIC_UUID)
        decoded = response.decode(errors="replace")
        if not silent:
            console.print(f"[bold cyan]> {decoded}[/bold cyan]")
        return decoded
    except Exception as e:
        if not silent:
            console.print(f"[bold red]Error reading response:[/bold red] {e}")
        return None


async def run_test(client, previous_command):
    test_command = Prompt.ask(
        "[bold yellow]Test command[/bold yellow]",
        default=previous_command if previous_command else "ping",
    )

    try:
        count = int(
            Prompt.ask("[bold yellow]Number of iterations[/bold yellow]", default="10")
        )
    except ValueError:
        console.print("[bold red]Invalid iteration count[/bold red]")
        return previous_command

    try:
        delay_ms = int(
            Prompt.ask(
                "[bold yellow]Delay between iterations (ms)[/bold yellow]",
                default="200",
            )
        )
    except ValueError:
        console.print("[bold red]Invalid delay[/bold red]")
        return previous_command

    console.print(
        Panel(
            f"[bold green]Running test[/bold green]\n"
            f"Command: [cyan]{test_command}[/cyan]\n"
            f"Iterations: [cyan]{count}[/cyan]\n"
            f"Delay: [cyan]{delay_ms} ms[/cyan]",
            title="[bold magenta]Test Mode[/bold magenta]",
        )
    )

    success = 0
    failures = 0
    latencies = []
    responses = {}

    table = Table(title="Test Results")
    table.add_column("Run", justify="right")
    table.add_column("Status")
    table.add_column("Latency (ms)", justify="right")
    table.add_column("Response")

    for i in range(1, count + 1):
        start = time.perf_counter()

        ok = await send_command(client, test_command)
        if not ok:
            failures += 1
            table.add_row(str(i), "[red]WRITE_FAIL[/red]", "-", "-")
            await asyncio.sleep(delay_ms / 1000)
            continue

        response = await receive_response(client, silent=True)
        end = time.perf_counter()
        latency_ms = (end - start) * 1000

        if response is None:
            failures += 1
            table.add_row(str(i), "[red]READ_FAIL[/red]", f"{latency_ms:.2f}", "-")
        else:
            success += 1
            latencies.append(latency_ms)
            responses[response] = responses.get(response, 0) + 1
            table.add_row(str(i), "[green]OK[/green]", f"{latency_ms:.2f}", response)

        await asyncio.sleep(delay_ms / 1000)

    console.print(table)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0

    summary = Table(title="Summary")
    summary.add_column("Metric")
    summary.add_column("Value")
    summary.add_row("Command", test_command)
    summary.add_row("Total Runs", str(count))
    summary.add_row("Success", str(success))
    summary.add_row("Failures", str(failures))
    summary.add_row("Avg Latency (ms)", f"{avg_latency:.2f}")
    summary.add_row("Min Latency (ms)", f"{min_latency:.2f}")
    summary.add_row("Max Latency (ms)", f"{max_latency:.2f}")

    console.print(summary)

    if responses:
        resp_table = Table(title="Response Distribution")
        resp_table.add_column("Response")
        resp_table.add_column("Count", justify="right")
        for resp, cnt in sorted(responses.items(), key=lambda x: x[1], reverse=True):
            resp_table.add_row(resp, str(cnt))
        console.print(resp_table)

    return test_command


async def interactive_ble():
    address = await find_device()
    if not address:
        return

    async with BleakClient(address) as client:
        if not client.is_connected:
            console.print("[bold red]Failed to connect to device[/bold red]")
            return

        console.print(
            Panel(
                "[bold green]Connected to device![/bold green]\n"
                "Type commands to send.\n"
                "[italic]Type 'exit' to quit.[/italic]\n"
                "[italic]Type 'clear' to clear screen.[/italic]\n"
                "[italic]Type 'p' to repeat previous command.[/italic]\n"
                "[italic]Type 'r' to read response.[/italic]\n"
                "[italic]Type 't' to run test mode.[/italic]\n",
                title="[bold cyan]BLE Interface[/bold cyan]",
            )
        )

        try:
            previous_command = ""
            while True:
                try:
                    command = Prompt.ask("[bold magenta]$[/bold magenta]")

                    if command.lower() == "exit":
                        break
                    if command == "":
                        continue
                    if command == "clear":
                        clear_screen()
                        continue
                    if command == "p":
                        if not previous_command:
                            console.print(
                                "[bold yellow]No previous command available[/bold yellow]"
                            )
                            continue
                        command = previous_command
                    if command == "r":
                        await receive_response(client)
                        continue
                    if command == "t":
                        previous_command = await run_test(client, previous_command)
                        continue

                    previous_command = command
                    ok = await send_command(client, command)
                    if ok:
                        await receive_response(client)

                except Exception as e:
                    console.print(f"[bold red]Error in loop:[/bold red] {e}")

        except KeyboardInterrupt:
            console.print(
                "\n[bold red]Keyboard interrupt detected. Exiting...[/bold red]"
            )


asyncio.run(interactive_ble())
