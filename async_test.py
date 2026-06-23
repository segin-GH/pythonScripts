import asyncio
import threading
import time
import kthread

stop_event = threading.Event()


async def send():
    print("S1")
    await asyncio.sleep(1)
    print("S2")


async def receive():
    print("R1")
    await asyncio.sleep(1)
    print("R2")


async def main():
    print("Starting main")

    try:
        while not stop_event.is_set():
            await send()
            await receive()

    except asyncio.CancelledError:
        print("CancelledError: Stopping main loop")
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        print("Cleaning up before exit")


def run():
    asyncio.run(main())
    print("Async loop finished")


if __name__ == "__main__":
    thread = kthread.KThread(target=run, name="async loop", daemon=True)
    thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received, stopping main loop")
        stop_event.set()
        thread.join()
        print("Exiting main")
