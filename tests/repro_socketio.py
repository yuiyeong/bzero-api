import asyncio
import threading
import time

import httpx
import socketio
import uvicorn
from fastapi import FastAPI


# Define the two apps
sio_correct = socketio.AsyncServer(async_mode="asgi")
app_correct = socketio.ASGIApp(sio_correct, socketio_path="socket.io")

sio_wrong = socketio.AsyncServer(async_mode="asgi")
app_wrong = socketio.ASGIApp(sio_wrong, socketio_path="/")  # The buggy config

# Mount them in a main app
main_app = FastAPI()
main_app.mount("/correct", app_correct)
main_app.mount("/wrong", app_wrong)


def run_server():
    uvicorn.run(main_app, port=8001, log_level="critical")


async def check_connection(path):
    print(f"Checking {path}...")
    headers = {
        "Connection": "Upgrade",
        "Upgrade": "websocket",
        "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
        "Sec-WebSocket-Version": "13",
    }
    # Note: Socket.IO client usually does polling first, then upgrade.
    # But direct websocket connection request looks like this.
    # The path usually has query params too.

    url = f"http://localhost:8001{path}/?EIO=4&transport=websocket"

    async with httpx.AsyncClient() as client:
        try:
            # We must use a raw request that looks like a websocket upgrade
            # But httpx doesn't do WS upgrades easily without a plugin.
            # We'll just check if we get 404 or 101 (or 400 if it expects upgrade).
            # Actually, standard HTTP GET to the endpoint:
            response = await client.get(url, headers=headers)
            print(f"Path: {path} -> Status: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(2)  # Wait for server

    asyncio.run(check_connection("/correct/socket.io"))
    asyncio.run(check_connection("/wrong/socket.io"))
