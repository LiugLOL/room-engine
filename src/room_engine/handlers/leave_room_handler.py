from room_engine.commands import LeaveRoomCommand
from room_engine.rooms.room_manager import RoomManager
from room_engine.handlers.handler import Handler


class LeaveRoomHandler(Handler):
    """Translate room-leave commands into room manager operations."""

    def __init__(self, room_manager: RoomManager):
        """Bind the handler to the manager that owns room state.

        Args:
            room_manager: Manager responsible for finding and updating rooms.
        """
        self._room_manager = room_manager



    def handle(self, command: LeaveRoomCommand):
        """Remove the command's user from the requested room.

        Args:
            command: Request containing the user and target room code.

        Returns:
            A leave-result success or an expected failure result.
        """
        return self._room_manager.leave_room(command.room_code, command.user_id)
