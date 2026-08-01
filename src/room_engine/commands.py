from dataclasses import dataclass


class Command:
    """Base type for commands handled by the engine."""
    pass


@dataclass(frozen=True)
class CreateRoomCommand(Command):
    user_id: int


@dataclass(frozen=True)
class JoinRoomCommand(Command):
    user_id: int
    room_code: str


@dataclass(frozen=True)
class LeaveRoomCommand(Command):
    user_id: int
    room_code: str