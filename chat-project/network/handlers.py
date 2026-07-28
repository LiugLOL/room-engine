from network.protocol import Message
from network.error_types import ErrorCode
class Handlers:

    def __init__(self, room_manager, connection_manager):
        self.room_manager = room_manager
        self.connection_manager = connection_manager



    async def handle_create_room(self, message: Message):

        return self.room_manager.create_room(
            message.sender_id
        )



    async def handle_join_room(self, message: Message):

        return self.room_manager.join_room(
            message.payload["room_code"],
            message.sender_id
        )



    async def handle_leave_room(self, message: Message):

        return self.room_manager.leave_room(
            message.payload["room_code"],
            message.sender_id
        )

    async def handle_chat_message(self, message):
        user_id = message.sender_id

        room_players = self.room_manager.get_players_room(user_id)

        if room_players is None:
            return {
                "success": False,
                "error": ErrorCode.USER_NOT_IN_ROOM.value
            }

        return {
            "success": True
        }