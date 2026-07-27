"""'
Protocol defines the contract between the client and the server, like the internal API for communication
between both(client-server) parts.
Here are the:
Event types
Message structure
Functions to create and validate messages on the chat.

Client event types:
Create Room
Join Room
Leave room
Transfer host (for only users with the HOST role on the room)
Send messages

Server event types:
Room created
Room joined
Player joined
Player left
Host transferred
Chat message
Errors in general
"""

from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json

class MessageSource(Enum):
    CLIENT = "client"
    SERVER = "server"

class MessageType(Enum):
    CREATE_ROOM = "create_room"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    TRANSFER_HOST = "transfer_host"

    CHAT_MESSAGE = "chat_message"

    ROOM_CREATED = "room_created"
    ROOM_JOINED = "room_joined"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    HOST_TRANSFERRED = "host_transferred"
    ERROR = "error"

@dataclass
class Message:
    sender_id: int
    source: MessageSource
    event_type: MessageType
    payload: dict
    timestamp: datetime

def encode_msg(message: Message) -> str:
    return json.dumps({
        "sender_id": message.sender_id,
        "source": message.source.value,
        "type": message.event_type.value,
        "payload": message.payload,
        "timestamp": message.timestamp.isoformat()
    }, ensure_ascii=False)
def decode_msg(data: str) -> Message:
    content = json.loads(data)

    return Message(
        sender_id=content["sender_id"],
        source=MessageSource(content["source"]),
        event_type=MessageType(content["type"]),
        payload=content["payload"],
        timestamp=datetime.fromisoformat(content["timestamp"])
    )