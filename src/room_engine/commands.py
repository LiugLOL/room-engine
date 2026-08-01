from dataclasses import dataclass


class Command:
    """Base type for requests executed by the room engine.

    Commands describe an intended room operation without embedding domain
    behavior. The dispatcher uses their concrete type to select a handler.
    """
    pass

@dataclass(frozen=True)
class CreateRoomCommand(Command):
    """Request creation of a new room owned by a user.

    Args:
        user_id: Identifier of the user who will create and host the room.
    """

    user_id: int

@dataclass(frozen=True)
class JoinRoomCommand(Command):
    """Request that a user joins an existing room.

    Args:
        user_id: Identifier of the user joining the room.
        room_code: Code identifying the room to join.
    """

    user_id: int
    room_code: str

@dataclass(frozen=True)
class LeaveRoomCommand(Command):
    """Request that a user leaves a room.

    Args:
        user_id: Identifier of the user leaving the room.
        room_code: Code identifying the room to leave.
    """

    user_id: int
    room_code: str
