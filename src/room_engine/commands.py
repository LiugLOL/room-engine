from dataclasses import dataclass


@dataclass(frozen=True)
class CreateRoomCommand:
    user_id: int

@dataclass(frozen=True)
class JoinRoomCommand:
    user_id: int
    room_code: str

@dataclass(frozen=True)
class LeaveRoomCommand:
    user_id: int
    room_code: str

