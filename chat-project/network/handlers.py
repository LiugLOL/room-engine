from room.room_manager import RoomManager
from network.protocol import Message
from network.connection_manager import ConnectionManager
class Handlers:
    def __init__(self, room_manager: RoomManager, connection_manager: ConnectionManager):
        self.room_manager = room_manager
        self.connection_manager = connection_manager
    async def handle_create_room(self, message: Message):
        user_id = message.sender_id
        room_code = self.room_manager.create_room(user_id)
        return room_code


    async def handle_join_room(self, message: Message):
        user_id = message.sender_id
        room_code = message.payload["room_code"]
        answer = self.room_manager.join_room(room_code, user_id)
        return answer


    async def handle_leave_room(self, message: Message):
        user_id = message.sender_id
        room_code = message.payload["room_code"]
        answer = self.room_manager.leave_room(room_code, user_id)
        return answer

    async def handle_chat_message(self, message: Message):
        user_id = message.sender_id
        room_players = self.room_manager.get_players_room(user_id)

        if room_players is None:
            return "User is not in a room"

        users_id = [player.user_id for player in room_players]

        await self.connection_manager.send_to_users(
            users_id,
            message
        )