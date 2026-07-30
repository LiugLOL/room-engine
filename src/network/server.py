""""
Server will be responsible for organizing this whole thing, since connecting users to rooms and decoding and send
messages to the users
"""
from datetime import datetime, timezone
from starlette.websockets import WebSocketDisconnect
from rooms.room_manager import RoomManager
from network.connection_manager import ConnectionManager
from network.protocol import Message, decode_msg, MessageSource
from network.message_types import MessageType, BROADCAST_EVENTS
from handlers.handlers import Handlers
from fastapi import WebSocket

#To make easier returning server responses to the client
def server_message(event_type: MessageType, payload, sender_id: int=0 ):
    return Message(
        sender_id=sender_id,
        source=MessageSource.SERVER,
        event_type=event_type,
        payload=payload,
        timestamp=datetime.now(timezone.utc)
    )


class Server:

    def __init__(self):
        self.room_manager = RoomManager()
        self.connection_manager = ConnectionManager(room_manager=self.room_manager)
        self.handlers = Handlers(self.room_manager, self.connection_manager)



    async def handle_connection(self, user_id: int, nickname: str, websocket: WebSocket):
        await self.connection_manager.connect(user_id, nickname, websocket)
        try:
            while True:
                data = await websocket.receive_text()
                message = decode_msg(data)

                response = await self.handle_message(message)

                if response is not None:
                    message_type = response.event_type
                    if message_type in BROADCAST_EVENTS:
                        sender_id = message.sender_id
                        await self.connection_manager.send_to_room(sender_id, response)
                    else:
                        await self.connection_manager.send_to_user(user_id, response)
        except WebSocketDisconnect:
            pass
        finally:
            self.connection_manager.disconnect(user_id)


    async def handle_message(self, message: Message):

        if message.event_type == MessageType.CREATE_ROOM:
            #request is the user creating a rooms
            room_code = await self.handlers.handle_create_room(message)
            return server_message(MessageType.ROOM_CREATED, {"room_code": room_code})


        elif message.event_type == MessageType.JOIN_ROOM:
            room_code = message.payload["room_code"]
            result = await self.handlers.handle_join_room(message)

            if not result["success"]:
                return server_message(
                    MessageType.ERROR,
                    {
                        "error": result["error"]
                    }
                )

            return server_message(
                MessageType.PLAYER_JOINED,
                {
                    "room_code": room_code,
                    "player_id": message.sender_id
                }
            )


        elif message.event_type == MessageType.LEAVE_ROOM:
            result = await self.handlers.handle_leave_room(message)

            if not result["success"]:
                return server_message(
                    MessageType.ERROR,
                    {
                        "error": result["error"]
                    }
                )

            return server_message(
                MessageType.PLAYER_LEFT,
                {
                    "room_code": message.payload["room_code"],
                    "player_id": message.sender_id
                }
            )


        elif message.event_type == MessageType.SEND_CHAT_MESSAGE:
            await self.handlers.handle_chat_message(message)
            return server_message(
                MessageType.CHAT_MESSAGE,
                {
                    "text": message.payload["text"],
                    "player_id": message.sender_id
                },
                sender_id=message.sender_id
            )
        else:
            print(f"Unknown message type: {message.event_type}")
            return server_message(MessageType.ERROR, {"message": "Unknown message type"})

