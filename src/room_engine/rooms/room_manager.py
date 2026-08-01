import random
from room_engine.core.result import Failure, InternalError, Result, Success
from room_engine.rooms.room_player import RoomPlayer
from room_engine.core.error_types import ErrorType
from room_engine.rooms.results import LeaveRoomResult, RoomCreation
from room_engine.rooms.room import Room


class RoomManager:
    """Coordinate the lifecycle and lookup of all active rooms.

    The manager is the application state boundary for rooms. It creates unique
    room codes, delegates membership rules to individual rooms, and removes
    rooms that no longer have players.
    """

    def __init__(self):
        """Initialize an empty collection of active rooms."""
        self.rooms: dict[str, Room] = {}



    def generate_room_code(self) -> str:
        """Generate an unused, human-readable room code.

        Returns:
            A six-character code not assigned to an active room.
        """
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
        """Create a room and make its creator the initial host.

        Args:
            user_id: Identifier of the user creating the room.

        Returns:
            A success containing the created room and host, or an expected
            failure if the initial membership cannot be created.
        """
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


    def join_room(self, room_code: str, user_id: int) -> Result[RoomPlayer]:
        """Add a user to an existing room.

        Args:
            room_code: Code identifying the room to join.
            user_id: Identifier of the user joining the room.

        Returns:
            A success containing the new player record, or a failure when the
            room is missing or the user is already a member.
        """
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


    def leave_room(self, room_code: str, user_id: int) -> Result[LeaveRoomResult]:
        """Remove a user from a room and clean up an empty room.

        Args:
            room_code: Code identifying the room to leave.
            user_id: Identifier of the user leaving the room.

        Returns:
            A success describing the departure, including host reassignment or
            room deletion, or an expected failure when the room or user is
            absent.
        """
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
        """Return the members of the room that contains a user.

        Args:
            user_id: Identifier of a room member.

        Returns:
            Player records for the user's room, or ``None`` when the user is
            not in any active room.
        """

        for lobby in self.rooms.values():

            if user_id in lobby.players:
                return list(lobby.players.values())

        return None


    def get_user_room(self, user_id: int) -> str | None:
        """Find the room code for a user.

        Args:
            user_id: Identifier of the user to locate.

        Returns:
            The active room code containing the user, or ``None`` when absent.
        """

        for lobby in self.rooms.values():

            if user_id in lobby.players:
                return lobby.code

        return None


    def get_room(self, room_code: str) -> Room | None:
        """Retrieve an active room by its code.

        Args:
            room_code: Code identifying the room.

        Returns:
            The matching room, or ``None`` when no active room has the code.
        """

        return self.rooms.get(room_code)

