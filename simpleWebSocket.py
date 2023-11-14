import asyncio
import websockets

async def echo(websocket, path):
    async for message in websocket:
        print("[Data Received] "+message)
        await websocket.send(f"Echo from esp32: {message}")

start_server = websockets.serve(echo, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

