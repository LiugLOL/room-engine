import random
from core.result import Failure, InternalError, Result, Success
from models.room_player import RoomPlayer
from core.error_types import ErrorType
from room.results import LeaveRoomResult, RoomCreation
from room.room import Room

class RoomManager:

    def __init__(self):
        self.rooms: dict[str, Room] = {}



    def generate_room_code(self):
        letras = "ABCDEFGHJKLMNPQRSTUVWXYZ"
        numeros = "23456789"

        while True:
            codigo = ""

            for _ in range(3):
                codigo += random.choice(letras)

            for _ in range(3):
                codigo += random.choice(numeros)

            if codigo not in self.rooms:
                return codigo

    def create_room(self, user_id: int) -> Result[RoomCreation]:
        room_code = self.generate_room_code()
        new_room = Room(room_code)

        add_result = new_room.add_player(user_id)

        if isinstance(add_result, Failure):
            return add_result

        self.rooms[room_code] = new_room

        return Success(
            RoomCreation(
                room=new_room,
                host=add_result.value,
            )
        )


    def join_room(self,room_code: str,user_id: int) -> Result[RoomPlayer]:
        room = self.rooms.get(room_code)

        if room is None:
            return Failure(
                InternalError(
                    code=ErrorType.ROOM_NOT_FOUND,
                    message="Room not found",
                    details={
                        "room_code": room_code,
                    },
                )
            )

        return room.add_player(user_id)


    def leave_room(self,room_code: str,user_id: int,) -> Result[LeaveRoomResult]:
        room = self.rooms.get(room_code)

        if room is None:
            return Failure(
                InternalError(
                    code=ErrorType.ROOM_NOT_FOUND,
                    message="Room not found",
                    details={
                        "room_code": room_code,
                    },
                )
            )

        was_host = room.host_id == user_id

        remove_result = room.remove_player(user_id)

        if isinstance(remove_result, Failure):
            return remove_result

        new_host = None

        if was_host and room.host_id is not None:
            new_host = room.get_player(room.host_id)

        room_deleted = False

        if not room.players:
            del self.rooms[room_code]
            room_deleted = True

        return Success(
            LeaveRoomResult(
                player=remove_result.value,
                room_deleted=room_deleted,
                new_host=new_host,
            )
        )


    def get_room_players_by_user(self, user_id: int) -> list[RoomPlayer] | None:

        for lobby in self.rooms.values():

            if user_id in lobby.players:
                return list(lobby.players.values())

        return None


    def get_user_room(self, user_id: int) -> str | None:

        for lobby in self.rooms.values():

            if user_id in lobby.players:
                return lobby.code

        return None


    def get_room(self, room_code: str) -> Room | None:

        return self.rooms.get(room_code)

