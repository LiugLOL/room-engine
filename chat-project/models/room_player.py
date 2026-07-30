"""
These classes exist for the relation between players and the room they're in

self.id is the user itself id, for location of the user
self.room_id is the room id, for location of the user and which room
self.local_id is the local id on the room, I'll use it for locate the next host of the room for now, that's the only use
self.joined_at is the time at which the player joined the room
self.role is the player role
Possible roles:
    1 - player
    2 - host
    3 - spectator
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class PlayerRole(Enum):
        PLAYER = "player"
        HOST ="host"
        SPECTATOR = "spectator"
@dataclass
class RoomPlayer:
        user_id: int
        room_code: str
        role: PlayerRole
        joined_at: datetime
        local_id: int
        left_at: datetime | None = None
