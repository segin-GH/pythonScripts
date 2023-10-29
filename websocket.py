import asyncio
import websockets

async def main():
    uri = "ws://192.168.0.101/ws"  # Update with your ESP32's IP address and URI
    async with websockets.connect(uri) as websocket:
        # Send a message to the server
        await websocket.send("Hello ESP32!")

        # Wait for a response from the server
        response = await websocket.recv()
        print(f"Received: {response}")
if __name__ == "__main__":

    asyncio.run(main())
