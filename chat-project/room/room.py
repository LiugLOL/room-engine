from datetime import datetime, timezone
import room_player
from room_player import PlayerRole
class Room:
    def __init__(self, code):
        self.code = code
        self.players = {}
        self.host_id = None
        self.created_at = datetime.now(timezone.utc)
        self.status = "Testing"
        self.next_local_id = 0

    def add_player(self, user_id: int):
        if user_id in self.players:
            return "Player already in room"
        player = room_player.RoomPlayer(
            user_id= user_id,
            room_id = self.code,
            local_id = self.next_local_id,
            joined_at = datetime.now(timezone.utc),
            role = PlayerRole.PLAYER
        )
        self.players[user_id] = player

        if self.host_id is None:
            self.host_id = user_id
            player.role = PlayerRole.HOST
        self.next_local_id += 1
        return None
    def remove_player(self, user_id : int):
        if user_id not in self.players:
            return "Player not found/not in room"
        player = self.players[user_id]
        player.left_at = datetime.now(timezone.utc)
        del self.players[user_id]
        if user_id == self.host_id:
            self.elect_new_host()
        return None
    def elect_new_host(self):
        if not self.players:
            self.host_id = None
            return
        new_host = None

        for player in self.players.values():
            if new_host is None:
                new_host = player
            elif player.local_id < new_host.local_id:
                new_host = player

        if new_host:
            new_host.role = PlayerRole.HOST
            self.host_id = new_host.user_id
    def transfer_host(self, user_id):
        if user_id not in self.players:
            return "Player not found"
        if user_id == self.host_id:
            return "Already host"
        old_host = self.players[self.host_id]
        new_host = self.players[user_id]
        new_host.role = PlayerRole.HOST
        old_host.role = PlayerRole.PLAYER
        self.host_id = user_id
        return "Successfully transferred host"