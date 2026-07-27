"""Here will be the connection manager for websocket users."""
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from network.protocol import Message, encode_msg

class ConnectionManager:
    def __init__(self):
        self.connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.connections:
            del self.connections[user_id]

    async def send_to_user(self, user_id: int, message: Message):
        """
        Send a text message to a connected user.

        Returns:
            True if the message was sent successfully.
            False if the user is disconnected or the send failed.
        """
        websocket = self.connections.get(user_id)
        if websocket is None:
            return False

        try:
            data = encode_msg(message)
            await websocket.send_text(data)
            return True
        except WebSocketDisconnect:
            self.disconnect(user_id)
            return False

    async def send_to_users(self, users_id: list[int], message: Message):
        results = []
        for user_id in users_id:
            result = await self.send_to_user(user_id, message)
            results.append(result)
        return results