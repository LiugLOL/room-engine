from room_engine.commands import Command


class Handler:

    def handle(self, command: Command):
        raise NotImplementedError