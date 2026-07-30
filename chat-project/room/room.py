from datetime import datetime, timezone
from models.room_player import PlayerRole, RoomPlayer
from core.result import Success, Failure, InternalError, Result
from core.error_types import ErrorType
from room.results import HostTransfer


class Room:

    def __init__(self, code: str):
        self.code: str = code
        self.players: dict[int, RoomPlayer] = {}
        self.host_id: int | None = None
        self.created_at = datetime.now(timezone.utc)
        self.status = "Testing"
        self.next_local_id: int = 0



    def add_player(self, user_id: int) -> Result[RoomPlayer]:
        if user_id in self.players:
            return Failure(
                InternalError(
                    code=ErrorType.USER_ALREADY_IN_ROOM,
                    message="User already in room",
                    details={
                        "user_id": user_id,
                        "room_code": self.code,
                    },
                )
            )

        player = RoomPlayer(
            user_id=user_id,
            room_code=self.code,
            local_id=self.next_local_id,
            joined_at=datetime.now(timezone.utc),
            role=PlayerRole.PLAYER,
        )

        self.players[user_id] = player

        if self.host_id is None:
            self.host_id = user_id
            player.role = PlayerRole.HOST

        self.next_local_id += 1

        return Success(player)


    def remove_player(self, user_id: int) -> Result[RoomPlayer]:
        if user_id not in self.players:
            return Failure(
                InternalError(
                    code=ErrorType.USER_NOT_IN_ROOM,
                    message="User not in room",
                    details={
                        "user_id": user_id,
                        "room_code": self.code,
                    },
                )
            )

        player = self.players[user_id]
        player.left_at = datetime.now(timezone.utc)

        del self.players[user_id]

        if user_id == self.host_id:
            self.elect_new_host()

        return Success(player)


    def elect_new_host(self) -> RoomPlayer | None:
        if not self.players:
            self.host_id = None
            return None

        new_host = min(
            self.players.values(),
            key=lambda player: player.local_id,
        )

        new_host.role = PlayerRole.HOST
        self.host_id = new_host.user_id

        return new_host


    def transfer_host(self, user_id: int) -> Result[HostTransfer]:

        if self.host_id is None:
            return Failure(
                InternalError(
                    code=ErrorType.NO_HOST_IN_ROOM,
                    message="No host in room",
                    details={
                        "room_code": self.code,
                    },
                )
            )

        if user_id not in self.players:
            return Failure(
                InternalError(
                    code=ErrorType.USER_NOT_IN_ROOM,
                    message="User not in room",
                    details={
                        "user_id": user_id,
                        "room_code": self.code,
                    },
                )
            )

        if user_id == self.host_id:
            return Failure(
                InternalError(
                    code=ErrorType.USER_ALREADY_HOST,
                    message="User is already host",
                    details={
                        "user_id": user_id,
                        "room_code": self.code,
                    }
                )
            )

        old_host = self.players[self.host_id]
        new_host = self.players[user_id]

        old_host.role = PlayerRole.PLAYER
        new_host.role = PlayerRole.HOST

        self.host_id = user_id

        return Success(HostTransfer(
            old_host=old_host,
            new_host=new_host
        ))


    def get_player(self, user_id: int) -> RoomPlayer | None:
        return self.players.get(user_id)

