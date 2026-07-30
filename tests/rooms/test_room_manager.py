"""Tests for the RoomManager class."""
import pytest
from room_engine.rooms.room_manager import RoomManager
from room_engine.rooms.room_player import PlayerRole
from room_engine.core.result import Success, Failure
from room_engine.core.error_types import ErrorType


class TestCreateRoom:
    """Test room creation through RoomManager."""

    def test_create_room_succeeds(self, room_manager):
        """Test creating a room succeeds."""
        result = room_manager.create_room(user_id=1)

        assert isinstance(result, Success)
        assert result.value.room is not None
        assert result.value.host.user_id == 1
        assert result.value.host.role == PlayerRole.HOST

    def test_create_room_generates_unique_code(self, room_manager):
        """Test that created rooms have unique codes."""
        result1 = room_manager.create_room(user_id=1)
        result2 = room_manager.create_room(user_id=2)

        assert result1.value.room.code != result2.value.room.code

    def test_created_room_added_to_manager(self, room_manager):
        """Test that created room is stored in manager."""
        result = room_manager.create_room(user_id=1)
        room_code = result.value.room.code

        room = room_manager.get_room(room_code)

        assert room is not None
        assert room.code == room_code
        assert 1 in room.players

    def test_creator_becomes_host(self, room_manager):
        """Test that room creator becomes host."""
        result = room_manager.create_room(user_id=42)

        assert result.value.host.user_id == 42
        assert result.value.host.role == PlayerRole.HOST
        assert result.value.room.host_id == 42


class TestJoinRoom:
    """Test joining rooms through RoomManager."""

    def test_join_existing_room_succeeds(self, room_manager):
        """Test joining existing room succeeds."""
        create_result = room_manager.create_room(user_id=1)
        room_code = create_result.value.room.code

        join_result = room_manager.join_room(room_code, user_id=2)

        assert isinstance(join_result, Success)
        assert join_result.value.user_id == 2
        assert join_result.value.role == PlayerRole.PLAYER

    def test_join_nonexistent_room_fails(self, room_manager):
        """Test joining nonexistent room fails."""
        result = room_manager.join_room("INVALID", user_id=1)

        assert isinstance(result, Failure)
        assert result.error.code == ErrorType.ROOM_NOT_FOUND
        assert result.error.details["room_code"] == "INVALID"

    def test_join_room_twice_fails(self, room_manager):
        """Test joining same room twice with same user fails."""
        create_result = room_manager.create_room(user_id=1)
        room_code = create_result.value.room.code

        room_manager.join_room(room_code, user_id=2)
        result = room_manager.join_room(room_code, user_id=2)

        assert isinstance(result, Failure)
        assert result.error.code == ErrorType.USER_ALREADY_IN_ROOM

    def test_multiple_players_join_same_room(self, room_manager):
        """Test multiple players can join same room."""
        create_result = room_manager.create_room(user_id=1)
        room_code = create_result.value.room.code

        room_manager.join_room(room_code, user_id=2)
        room_manager.join_room(room_code, user_id=3)
        room_manager.join_room(room_code, user_id=4)

        room = room_manager.get_room(room_code)

        assert len(room.players) == 4
        assert all(uid in room.players for uid in [1, 2, 3, 4])


class TestLeaveRoom:
    """Test leaving rooms through RoomManager."""

    def test_leave_room_succeeds(self, room_manager):
        """Test leaving room succeeds."""
        create_result = room_manager.create_room(user_id=1)
        room_code = create_result.value.room.code
        room_manager.join_room(room_code, user_id=2)

        result = room_manager.leave_room(room_code, user_id=2)

        assert isinstance(result, Success)
        assert result.value.player.user_id == 2
        assert result.value.room_deleted is False
        assert result.value.new_host is None

    def test_leave_nonexistent_room_fails(self, room_manager):
        """Test leaving nonexistent room fails."""
        result = room_manager.leave_room("INVALID", user_id=1)

        assert isinstance(result, Failure)
        assert result.error.code == ErrorType.ROOM_NOT_FOUND

    def test_leave_when_not_in_room_fails(self, room_manager):
        """Test leaving room when not a member fails."""
        create_result = room_manager.create_room(user_id=1)
        room_code = create_result.value.room.code

        result = room_manager.leave_room(room_code, user_id=999)

        assert isinstance(result, Failure)
        assert result.error.code == ErrorType.USER_NOT_IN_ROOM

    def test_regular_player_leaves_room_deleted_false(self, room_manager):
        """Test that leaving as regular player doesn't delete room."""
        create_result = room_manager.create_room(user_id=1)
        room_code = create_result.value.room.code
        room_manager.join_room(room_code, user_id=2)
        room_manager.join_room(room_code, user_id=3)

        result = room_manager.leave_room(room_code, user_id=2)

        assert isinstance(result, Success)
        assert result.value.room_deleted is False
        assert result.value.new_host is None
        assert room_manager.get_room(room_code) is not None

    def test_host_leaves_transfers_host(self, room_manager):
        """Test that host leaving transfers host to next player."""
        create_result = room_manager.create_room(user_id=1)
        room_code = create_result.value.room.code
        room_manager.join_room(room_code, user_id=2)
        room_manager.join_room(room_code, user_id=3)

        result = room_manager.leave_room(room_code, user_id=1)

        assert isinstance(result, Success)
        assert result.value.new_host is not None
        assert result.value.new_host.user_id == 2
        assert result.value.new_host.role == PlayerRole.HOST
        assert result.value.room_deleted is False

    def test_last_player_leaves_deletes_room(self, room_manager):
        """Test that last player leaving deletes room."""
        create_result = room_manager.create_room(user_id=1)
        room_code = create_result.value.room.code

        result = room_manager.leave_room(room_code, user_id=1)

        assert isinstance(result, Success)
        assert result.value.room_deleted is True
        assert room_manager.get_room(room_code) is None

    def test_all_players_leave_deletes_room(self, room_manager):
        """Test that room is deleted when all players leave."""
        create_result = room_manager.create_room(user_id=1)
        room_code = create_result.value.room.code
        room_manager.join_room(room_code, user_id=2)
        room_manager.join_room(room_code, user_id=3)

        room_manager.leave_room(room_code, user_id=1)
        room_manager.leave_room(room_code, user_id=2)
        result = room_manager.leave_room(room_code, user_id=3)

        assert isinstance(result, Success)
        assert result.value.room_deleted is True
        assert room_manager.get_room(room_code) is None


class TestGetRoomPlayersByUser:
    """Test retrieving room players by user."""

    def test_get_players_when_user_in_room(self, room_manager):
        """Test getting players when user is in room."""
        create_result = room_manager.create_room(user_id=1)
        room_code = create_result.value.room.code
        room_manager.join_room(room_code, user_id=2)
        room_manager.join_room(room_code, user_id=3)

        players = room_manager.get_room_players_by_user(user_id=2)

        assert players is not None
        assert len(players) == 3
        assert all(p.user_id in [1, 2, 3] for p in players)

    def test_get_players_when_user_not_in_any_room(self, room_manager):
        """Test getting players when user not in any room."""
        result = room_manager.get_room_players_by_user(user_id=999)

        assert result is None

    def test_get_players_returns_correct_room_only(self, room_manager):
        """Test that only players from user's room are returned."""
        create_result1 = room_manager.create_room(user_id=1)
        room_code1 = create_result1.value.room.code
        room_manager.join_room(room_code1, user_id=2)

        create_result2 = room_manager.create_room(user_id=10)
        room_code2 = create_result2.value.room.code
        room_manager.join_room(room_code2, user_id=11)

        players = room_manager.get_room_players_by_user(user_id=2)

        assert len(players) == 2
        assert all(p.user_id in [1, 2] for p in players)


class TestGetUserRoom:
    """Test retrieving user's room code."""

    def test_get_user_room_when_in_room(self, room_manager):
        """Test getting room code when user is in room."""
        create_result = room_manager.create_room(user_id=1)
        room_code = create_result.value.room.code
        room_manager.join_room(room_code, user_id=2)

        result = room_manager.get_user_room(user_id=2)

        assert result == room_code

    def test_get_user_room_when_not_in_room(self, room_manager):
        """Test getting room code when user not in room."""
        result = room_manager.get_user_room(user_id=999)

        assert result is None

    def test_get_user_room_returns_only_one_room(self, room_manager):
        """Test that user can only be in one room."""
        create_result = room_manager.create_room(user_id=1)
        room_code = create_result.value.room.code

        result = room_manager.get_user_room(user_id=1)

        assert result == room_code


class TestGetRoom:
    """Test retrieving room by code."""

    def test_get_existing_room(self, room_manager):
        """Test getting existing room."""
        create_result = room_manager.create_room(user_id=1)
        room_code = create_result.value.room.code

        room = room_manager.get_room(room_code)

        assert room is not None
        assert room.code == room_code

    def test_get_nonexistent_room(self, room_manager):
        """Test getting nonexistent room."""
        room = room_manager.get_room("INVALID")

        assert room is None
