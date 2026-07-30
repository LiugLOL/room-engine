from enum import Enum
class MessageType(Enum):
    CREATE_ROOM = "create_room"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    TRANSFER_HOST = "transfer_host"

    SEND_CHAT_MESSAGE = "send_chat_message"
    CHAT_MESSAGE = "chat_message"

    ROOM_CREATED = "room_created"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    HOST_TRANSFERRED = "host_transferred"
    ERROR = "error"

BROADCAST_EVENTS = {
    MessageType.PLAYER_JOINED,
    MessageType.PLAYER_LEFT,
    MessageType.HOST_TRANSFERRED,
    MessageType.SEND_CHAT_MESSAGE
}
PRIVATE_EVENTS = {
    MessageType.ROOM_CREATED,
    MessageType.ERROR
}