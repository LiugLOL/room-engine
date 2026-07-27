""""
Server will be responsible for organizing this whole thing, since connecting users to rooms and decoding and send
messages to the users
"""
from datetime import datetime, timezone

from starlette.websockets import WebSocketDisconnect

from network import handlers
from room.room_manager import RoomManager
from network.connection_manager import ConnectionManager
from network.protocol import Message, decode_msg, MessageType, MessageSource
from network.handlers import Handlers
from fastapi import WebSocket

class Server:
    def __init__(self):
        self.room_manager = RoomManager()
        self.connection_manager = ConnectionManager()
        self.handlers = Handlers(self.room_manager, self.connection_manager)

    async def handle_connection(self, user_id: int, websocket: WebSocket):
        await self.connection_manager.connect(user_id, websocket)
        try:
            while True:
                data = await websocket.receive_text()
                message = decode_msg(data)
                await self.handle_message(message)
        except WebSocketDisconnect:
            pass
        finally:
            self.connection_manager.disconnect(user_id)

    async def handle_message(self, message: Message):

        if message.event_type == MessageType.CREATE_ROOM:
            room_code = await self.handlers.handle_create_room(message)
            response = Message(
                sender_id=message.sender_id,
                source=MessageSource.SERVER,
                event_type=MessageType.ROOM_CREATED,
                payload={"room_code": room_code},
                timestamp = datetime.now(timezone.utc)
                )
            await self.connection_manager.send_to_user(message.sender_id, response)

        elif message.event_type == MessageType.JOIN_ROOM:
            await self.handlers.handle_join_room(message)
            room_code = message.payload["room_code"]
            request = Message(
                sender_id=message.sender_id,
                source=MessageSource.CLIENT,
                event_type=MessageType.JOIN_ROOM,
                payload={"room_code": room_code},
                timestamp=datetime.now(timezone.utc)
            )
            await self.handlers.handle_join_room(request)

            return response

        elif message.event_type == MessageType.LEAVE_ROOM:
            await self.handlers.handle_leave_room(message)

        elif message.event_type == MessageType.CHAT_MESSAGE:
            await self.handlers.handle_chat_message(message)
        else:
            print(f"Unknown message type: {message.event_type}")

