import asyncio
from bleak import BleakClient, BleakScanner
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text

console = Console()

# Replace with your device's name or address
DEVICE_NAME = "BSS-12345678"
CMD_CHARACTERISTIC_UUID = "0000FF01-0000-1000-8000-00805F9B34FB"  # Command UUID


async def find_device():
    console.print(Panel(f"[bold cyan]Scanning for {DEVICE_NAME} [/bold cyan]"))
    devices = await BleakScanner.discover()
    for device in devices:
        if DEVICE_NAME in device.name:
            console.print(
                f"[bold green]Found device:[/bold green] {device.name} [blue][{device.address}][/blue]"
            )
            return device.address
    console.print("[bold red]Device not found[/bold red]")
    return None


async def send_command(client, command):
    try:
        await client.write_gatt_char(CMD_CHARACTERISTIC_UUID, command.encode("utf-8"))
        console.print(f"[bold yellow]> {command}[/bold yellow] ")
    except Exception as e:
        console.print(f"[bold red]Error sending command:[/bold red] {e}")


async def receive_response(client):
    try:
        response = await client.read_gatt_char(CMD_CHARACTERISTIC_UUID)
        console.print(f"[bold cyan]< {response.decode()} [/bold cyan] ")
        return response
    except Exception as e:
        console.print(f"[bold red]Error reading response:[/bold red] {e}")


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
                "[bold green]Connected to device![/bold green]\nType commands to send.\n[italic]Type 'exit' to quit.[/italic]",
                title="[bold cyan]BLE Interface[/bold cyan]",
            )
        )
        try:
            while True:
                try:
                    command = Prompt.ask("[bold magenta]$[/bold magenta]")
                    if command.lower() == "exit":
                        break

                    await send_command(client, command)
                    await asyncio.sleep(0.5)
                    await receive_response(client)
                except Exception as e:
                    console.print(f"[bold red]Error in loop:[/bold red] {e}")
        except KeyboardInterrupt:
            console.print(
                "\n[bold red]Keyboard interrupt detected. Exiting...[/bold red]"
            )


asyncio.run(interactive_ble())
