from room_engine.commands import Command


class Handler:
    """Define the interface implemented by command-specific handlers."""

    def handle(self, command: Command):
        """Handle one command.

        Args:
            command: Command assigned to this handler.

        Returns:
            The domain result produced while handling the command.

        Raises:
            NotImplementedError: Always, when a subclass has not implemented
                the operation.
        """
        raise NotImplementedError
