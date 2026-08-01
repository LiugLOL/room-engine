from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING
from room_engine.rooms.room_player import RoomPlayer
if TYPE_CHECKING:
    from room_engine.rooms.room import Room



@dataclass(frozen=True)
class HostTransfer:
    """Describe a change in room ownership.

    Args:
        old_host: Player who relinquished host responsibilities.
        new_host: Player selected as the new host.
    """

    old_host: RoomPlayer
    new_host: RoomPlayer

@dataclass(frozen=True)
class RoomCreation:
    """Return the room and host created by a room-creation operation.

    Args:
        room: Newly created room.
        host: Creator represented as the room's initial host.
    """

    room: Room
    host: RoomPlayer

@dataclass(frozen=True)
class LeaveRoomResult:
    """Describe the effects of removing a player from a room.

    Args:
        player: Player record for the user who left.
        room_deleted: Whether the departure left the room empty and removed it.
        new_host: Replacement host when the departing user was the host.
    """

    player: RoomPlayer
    room_deleted: bool
    new_host: RoomPlayer | None
