from room_engine.commands import CreateRoomCommand
from room_engine.rooms.room_manager import RoomManager
from room_engine.handlers.handler import Handler


class CreateRoomHandler(Handler):
    """Translate room-creation commands into room manager operations."""

    def __init__(self, room_manager: RoomManager):
        """Bind the handler to the manager that owns room state.

        Args:
            room_manager: Manager responsible for creating and storing rooms.
        """
        self._room_manager = room_manager



    def handle(self, command: CreateRoomCommand):
        """Create a room for the command's user.

        Args:
            command: Request containing the prospective host's identifier.

        Returns:
            A room-creation success result or an expected failure result.
        """
        return self._room_manager.create_room(command.user_id)
