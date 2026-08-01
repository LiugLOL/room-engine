from room_engine.commands import LeaveRoomCommand
from room_engine.rooms.room_manager import RoomManager
from room_engine.handlers.handler import Handler


class LeaveRoomHandler(Handler):

    def __init__(self, room_manager: RoomManager):
        self._room_manager = room_manager

    def handle(self, command: LeaveRoomCommand):
        return self._room_manager.leave_room(command.room_code, command.user_id)