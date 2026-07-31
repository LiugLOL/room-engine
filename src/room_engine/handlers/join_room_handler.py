from room_engine.commands import JoinRoomCommand
from room_engine.rooms.room_manager import RoomManager


class JoinRoomHandler:

    def __init__(self, room_manager: RoomManager):
        self._room_manager = room_manager

    def handle(self, command: JoinRoomCommand):
        return self._room_manager.join_room(
            command.room_code,
            command.user_id,
        )