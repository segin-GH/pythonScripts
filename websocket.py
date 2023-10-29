#!/usr/bin/python3

import asyncio
import websockets
import time

async def main():
    uri = "ws://192.168.0.101/ws"  # Update with your ESP32's IP address and URI
    
    async with websockets.connect(uri) as websocket:
        message = "Hello ESP32!"
        bytes_sent = len(message)
        
        start_time = time.time()
        
        # Send a message to the server
        await websocket.send(message)

        # Wait for a response from the server
        response = await websocket.recv()
        
        end_time = time.time()
        elapsed_time_ms = (end_time - start_time) * 1000  # Convert seconds to milliseconds
        
        bytes_received = len(response)
        
        print(f"Received: {response}")
        print(f"Bytes Sent: {bytes_sent}, Bytes Received: {bytes_received}, Elapsed Time: {elapsed_time_ms:.2f} ms")

if __name__ == "__main__":
    asyncio.run(main())

