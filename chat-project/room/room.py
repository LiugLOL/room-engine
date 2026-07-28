from datetime import datetime, timezone
from models.room_player import PlayerRole, RoomPlayer
from network.error_types import ErrorCode


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
            return {
                "success": False,
                "error": ErrorCode.USER_ALREADY_IN_ROOM.value
            }

        player = RoomPlayer(
            user_id=user_id,
            room_id=self.code,
            local_id=self.next_local_id,
            joined_at=datetime.now(timezone.utc),
            role=PlayerRole.PLAYER
        )

        self.players[user_id] = player

        if self.host_id is None:
            self.host_id = user_id
            player.role = PlayerRole.HOST

        self.next_local_id += 1

        return {
            "success": True,
            "player": player,
            "room_code": self.code
        }


    def remove_player(self, user_id: int):
        if user_id not in self.players:
            return {
                "success": False,
                "error": ErrorCode.USER_NOT_IN_ROOM.value
            }

        player = self.players[user_id]
        player.left_at = datetime.now(timezone.utc)

        del self.players[user_id]

        if user_id == self.host_id:
            self.elect_new_host()

        return {
            "success": True,
            "player": player
        }


    def elect_new_host(self):
        if not self.players:
            self.host_id = None
            return {
                "success": True,
                "player": None
            }

        new_host = min(
            self.players.values(),
            key=lambda player: player.local_id
        )
        """"
        what does the line "key=lambda player: player.local_id" means?
        key: min "filter" that gets what compare on the min, at this case, the local ids
        lambda: function with no name
        generic way to use lambda:
        lambda parameters: result like
        lambda player: player.local_id
        the parameter is the player itself, and the result is the local_id of the player
        """
        new_host.role = PlayerRole.HOST
        self.host_id = new_host.user_id

        return {
            "success": True,
            "player": new_host
        }


    def transfer_host(self, user_id):

        if self.host_id is None:
            return {
                "success": False,
                "error": ErrorCode.NO_HOST_IN_ROOM.value
            }

        if user_id not in self.players:
            return {
                "success": False,
                "error": ErrorCode.USER_NOT_IN_ROOM.value
            }

        if user_id == self.host_id:
            return {
                "success": False,
                "error": ErrorCode.USER_ALREADY_HOST.value
            }

        old_host = self.players[self.host_id]
        new_host = self.players[user_id]

        old_host.role = PlayerRole.PLAYER
        new_host.role = PlayerRole.HOST

        self.host_id = user_id

        return {
            "success": True,
            "old_host": old_host,
            "new_host": new_host
        }