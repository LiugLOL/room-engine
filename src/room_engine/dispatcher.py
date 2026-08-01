from room_engine.commands import Command
from room_engine.handlers.handler import Handler


class Dispatcher:

    def __init__(self):
        self._handlers: dict[type[Command], Handler] = {}

    def register(self, command_type: type[Command], handler: Handler) -> None:
        if command_type in self._handlers:
            raise ValueError(
                f"Handler already registered for {command_type.__name__}"
            )

        self._handlers[command_type] = handler

    def dispatch(self, command: Command):
        handler = self._handlers.get(type(command))

        if handler is None:
            raise ValueError(
                f"No handler registered for {type(command).__name__}"
            )

        return handler.handle(command)