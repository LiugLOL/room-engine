from room_engine.commands import JoinRoomCommand
from room_engine.rooms.room_manager import RoomManager
from room_engine.handlers.handler import Handler


class JoinRoomHandler(Handler):
    """Translate room-join commands into room manager operations."""

    def __init__(self, room_manager: RoomManager):
        """Bind the handler to the manager that owns room state.

        Args:
            room_manager: Manager responsible for finding and updating rooms.
        """
        self._room_manager = room_manager



    def handle(self, command: JoinRoomCommand):
        """Add the command's user to the requested room.

        Args:
            command: Request containing the user and target room code.

        Returns:
            A joined-player success result or an expected failure result.
        """
        return self._room_manager.join_room(
            command.room_code,
            command.user_id,
        )
