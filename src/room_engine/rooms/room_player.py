from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class PlayerRole(Enum):
    """Describe a player's responsibilities within a room."""

    PLAYER = "player"
    HOST = "host"
    SPECTATOR = "spectator"

@dataclass
class RoomPlayer:
    """Represent one user's membership record in a room.

    Args:
        user_id: Identifier of the represented user.
        room_code: Code of the room containing the player.
        role: Current responsibilities assigned to the player.
        joined_at: Time at which the player joined the room.
        local_id: Join-order identifier used for deterministic host election.
        left_at: Time at which the player left, when applicable.
    """

    user_id: int
    room_code: str
    role: PlayerRole
    joined_at: datetime
    local_id: int
    left_at: datetime | None = None
