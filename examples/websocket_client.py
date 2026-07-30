import asyncio
import websockets
import json
from datetime import datetime, timezone


async def main():
    uri = "ws://127.0.0.1:8000/ws/1/liug"

    async with websockets.connect(uri) as websocket:
        print("Conectado ao servidor!")

        message = {
            "sender_id": 1,
            "source": "client",
            "type": "create_room",
            "payload": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await websocket.send(json.dumps(message))

        response = await websocket.recv()

        print("Resposta do servidor:")
        print(response)


asyncio.run(main())