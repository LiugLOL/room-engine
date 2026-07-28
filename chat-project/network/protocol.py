"""'
Protocol defines the contract between the client and the server, like the internal API for communication
between both(client-server) parts.
Here are the:
Event types
Message structure
Functions to create and validate messages on the chat.

All events with * on the end are broadcasted to all users in the room, others not marked are private.
Client event types:
Create Room
Join Room
Leave room
Transfer host (for only users with the HOST role on the room)
Send chat message

Server event types:
Room created
Player joined *
Player left *
Host transferred *
Chat message *
Errors in general
"""

from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from network.message_types import MessageType
import json

class MessageSource(Enum):
    CLIENT = "client"
    SERVER = "server"

@dataclass
class Message:
    sender_id: int
    source: MessageSource
    event_type: MessageType
    payload: dict
    timestamp: datetime
#def funcao (parametro: tipodoparametro) -> tipodoresultado:
#    return (
#        expressao
#
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