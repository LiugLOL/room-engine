from room_engine.commands import Command
from room_engine.handlers.handler import Handler


class Dispatcher:
    """Route command objects to the handlers responsible for them.

    A dispatcher maintains the application-level mapping between a command
    type and its behavior, keeping the engine facade independent of handler
    lookup details.
    """

    def __init__(self):
        """Initialize an empty command-handler registry."""
        self._handlers: dict[type[Command], Handler] = {}



    def register(self, command_type: type[Command], handler: Handler) -> None:
        """Associate one concrete command type with its handler.

        Args:
            command_type: Command class that the handler accepts.
            handler: Handler that implements the command's behavior.

        Raises:
            ValueError: If a handler is already registered for the command.
        """
        if command_type in self._handlers:
            raise ValueError(
                f"Handler already registered for {command_type.__name__}"
            )

        self._handlers[command_type] = handler


    def dispatch(self, command: Command):
        """Execute a command through its registered handler.

        Args:
            command: Concrete command describing the requested operation.

        Returns:
            The result produced by the command's handler.

        Raises:
            ValueError: If no handler has been registered for the command type.
        """
        handler = self._handlers.get(type(command))

        if handler is None:
            raise ValueError(
                f"No handler registered for {type(command).__name__}"
            )

        return handler.handle(command)
