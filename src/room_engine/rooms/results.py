from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING
from room_engine.rooms.room_player import RoomPlayer
if TYPE_CHECKING:
    from room_engine.rooms.room import Room



@dataclass(frozen=True)
class HostTransfer:
    old_host: RoomPlayer
    new_host: RoomPlayer

@dataclass(frozen=True)
class RoomCreation:
    room: Room
    host: RoomPlayer

@dataclass(frozen=True)
class LeaveRoomResult:
    player: RoomPlayer
    room_deleted: bool
    new_host: RoomPlayer | None