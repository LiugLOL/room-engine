from room_engine.commands import Command, CreateRoomCommand, JoinRoomCommand, LeaveRoomCommand
from room_engine.dispatcher import Dispatcher
from room_engine.rooms.room_manager import RoomManager
from room_engine.handlers import CreateRoomHandler, JoinRoomHandler, LeaveRoomHandler

class RoomEngine:
    """Provide the application-facing entry point for room commands.

    The engine composes a room manager with the handlers that operate on it,
    so all commands executed by one engine instance share the same room state.
    """

    def __init__(self):
        """Create the room state and register its supported command handlers."""
        self.room_manager = RoomManager()
        self.dispatcher = Dispatcher()

        self.dispatcher.register(CreateRoomCommand, CreateRoomHandler(self.room_manager))
        self.dispatcher.register(JoinRoomCommand, JoinRoomHandler(self.room_manager))
        self.dispatcher.register(LeaveRoomCommand, LeaveRoomHandler(self.room_manager))



    def execute(self, command: Command):
        """Execute a room command against this engine's state.

        Args:
            command: Supported command to route to its handler.

        Returns:
            The success or failure result returned by the command handler.

        Raises:
            ValueError: If the command type is not supported by this engine.
        """
        return self.dispatcher.dispatch(command)
