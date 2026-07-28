"""Here will be the connection manager for websocket users."""
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
from models.connection import Connection
from models.user import User
from room.room_manager import RoomManager

from network.protocol import Message, encode_msg

class ConnectionManager:
    def __init__(self, room_manager: RoomManager):
        self.connections: dict[int, Connection] = {}
        self.room_manager = room_manager

    async def connect(self, user_id: int, nickname:str, websocket: WebSocket):
        await websocket.accept()
        user = User(user_id, nickname)
        connection = Connection(
            user=user,
            websocket=websocket
        )

        self.connections[user.id] = connection

    def disconnect(self, user_id: int):
        if user_id in self.connections:
            del self.connections[user_id]

    async def send_to_user(self, user_id: int, message: Message):
        """
        Send a text message to a connected user.

        Returns:
            True if the message was sent successfully.
            False if the user is disconnected or send failed.
        """
        connection = self.connections.get(user_id)
        if connection is None:
            return False

        try:
            data = encode_msg(message)
            await connection.websocket.send_text(data)
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
    def get_user(self, user_id: int) -> User | None:
        if user_id not in self.connections:
            return None
        return self.connections[user_id].user

    async def send_to_room(self, user_id: int, message: Message):
        users = self.room_manager.get_players_room(user_id)
        if users is None:
            return False
        users_id = [
            player.user_id
            for player in users
        ]
        return await self.send_to_users(users_id, message)
