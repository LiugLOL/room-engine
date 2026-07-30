from room_engine.commands import CreateRoomCommand
from room_engine.rooms.room_manager import RoomManager


class CreateRoomHandler:

    def __init__(self, room_manager: RoomManager):
        self._room_manager = room_manager

    def handle(self, command: CreateRoomCommand):
        return self._room_manager.create_room(command.user_id)