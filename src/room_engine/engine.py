from room_engine.commands import Command, CreateRoomCommand, JoinRoomCommand, LeaveRoomCommand
from room_engine.dispatcher import Dispatcher
from room_engine.rooms.room_manager import RoomManager
from room_engine.handlers import CreateRoomHandler, JoinRoomHandler, LeaveRoomHandler

class RoomEngine:
    def __init__(self):
        self.room_manager = RoomManager()
        self.dispatcher = Dispatcher()

        self.dispatcher.register(CreateRoomCommand, CreateRoomHandler(self.room_manager))
        self.dispatcher.register(JoinRoomCommand, JoinRoomHandler(self.room_manager))
        self.dispatcher.register(LeaveRoomCommand, LeaveRoomHandler(self.room_manager))

    def execute(self, command: Command):
        return self.dispatcher.dispatch(command)
