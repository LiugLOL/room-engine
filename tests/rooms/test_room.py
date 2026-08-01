"""Tests for the Room class."""
import pytest
from room_engine.rooms.room import Room
from room_engine.rooms.room_player import PlayerRole
from room_engine.core.result import Success, Failure
from room_engine.core.error_types import ErrorType


class TestRoomCreation:
    """Test room creation and initialization."""

    def test_room_initializes_with_code(self):
        """Test that a room initializes with correct code."""
        room = Room("ABC123")
        assert room.code == "ABC123"
        assert room.players == {}
        assert room.host_id is None
        assert room.next_local_id == 0


class TestAddPlayer:
    """Test adding players to a room."""

    def test_add_first_player_becomes_host(self):
        """Test that first player added becomes host."""
        room = Room("ABC123")
        result = room.add_player(user_id=1)

        assert isinstance(result, Success)
        assert result.value.user_id == 1
        assert result.value.role == PlayerRole.HOST
        assert room.host_id == 1
        assert 1 in room.players

    def test_add_second_player_is_regular_player(self):
        """Test that second player added is regular player, not host."""
        room = Room("ABC123")
        room.add_player(user_id=1)
        result = room.add_player(user_id=2)

        assert isinstance(result, Success)
        assert result.value.user_id == 2
        assert result.value.role == PlayerRole.PLAYER
        assert room.host_id == 1  # Host unchanged

    def test_add_multiple_players(self):
        """Test adding multiple players."""
        room = Room("ABC123")
        room.add_player(user_id=1)
        room.add_player(user_id=2)
        room.add_player(user_id=3)

        assert len(room.players) == 3
        assert room.host_id == 1

    def test_add_duplicate_player_fails(self):
        """Test that adding same player twice fails."""
        room = Room("ABC123")
        room.add_player(user_id=1)
        result = room.add_player(user_id=1)

        assert isinstance(result, Failure)
        assert result.error.code == ErrorType.USER_ALREADY_IN_ROOM
        assert result.error.details["user_id"] == 1

    def test_add_player_assigns_local_id_sequentially(self):
        """Test that local IDs are assigned sequentially."""
        room = Room("ABC123")
        result1 = room.add_player(user_id=1)
        result2 = room.add_player(user_id=2)
        result3 = room.add_player(user_id=3)

        assert result1.value.local_id == 0
        assert result2.value.local_id == 1
        assert result3.value.local_id == 2


class TestRemovePlayer:
    """Test removing players from a room."""

    def test_remove_regular_player_succeeds(self):
        """Test removing a regular player succeeds."""
        room = Room("ABC123")
        room.add_player(user_id=1)
        room.add_player(user_id=2)

        result = room.remove_player(user_id=2)

        assert isinstance(result, Success)
        assert result.value.user_id == 2
        assert 2 not in room.players
        assert room.host_id == 1  # Host unchanged

    def test_remove_nonexistent_player_fails(self):
        """Test removing nonexistent player fails."""
        room = Room("ABC123")
        room.add_player(user_id=1)
        result = room.remove_player(user_id=999)

        assert isinstance(result, Failure)
        assert result.error.code == ErrorType.USER_NOT_IN_ROOM
        assert result.error.details["user_id"] == 999

    def test_remove_host_elects_new_host(self):
        """Test that removing host elects new host."""
        room = Room("ABC123")
        room.add_player(user_id=1)
        room.add_player(user_id=2)
        room.add_player(user_id=3)

        result = room.remove_player(user_id=1)

        assert isinstance(result, Success)
        assert 1 not in room.players
        assert room.host_id == 2  # Next player by local_id
        assert room.players[2].role == PlayerRole.HOST

    def test_remove_host_when_only_player_clears_host(self):
        """Test that removing only player clears host."""
        room = Room("ABC123")
        room.add_player(user_id=1)

        result = room.remove_player(user_id=1)

        assert isinstance(result, Success)
        assert room.host_id is None
        assert len(room.players) == 0

    def test_remove_last_player_empties_room(self):
        """Test that removing last player empties room."""
        room = Room("ABC123")
        room.add_player(user_id=1)
        room.add_player(user_id=2)

        room.remove_player(user_id=1)
        room.remove_player(user_id=2)

        assert len(room.players) == 0
        assert room.host_id is None


class TestElectNewHost:
    """Test host election mechanism."""

    def test_elect_new_host_chooses_lowest_local_id(self):
        """Test that new host is elected with lowest local_id."""
        room = Room("ABC123")
        room.add_player(user_id=10)
        room.add_player(user_id=20)
        room.add_player(user_id=30)

        room.elect_new_host()

        assert room.host_id == 10  # First player to join (lowest local_id)
        assert room.players[10].role == PlayerRole.HOST

    def test_elect_new_host_with_empty_room(self):
        """Test electing host with empty room."""
        room = Room("ABC123")
        result = room.elect_new_host()

        assert result is None
        assert room.host_id is None


class TestTransferHost:
    """Test manual host transfer."""

    def test_transfer_host_succeeds(self):
        """Test successful host transfer."""
        room = Room("ABC123")
        room.add_player(user_id=1)
        room.add_player(user_id=2)

        result = room.transfer_host(user_id=2)

        assert isinstance(result, Success)
        assert result.value.old_host.user_id == 1
        assert result.value.new_host.user_id == 2
        assert room.host_id == 2
        assert room.players[1].role == PlayerRole.PLAYER
        assert room.players[2].role == PlayerRole.HOST

    def test_transfer_host_to_nonexistent_player(self):
        """Test transferring host to player not in room."""
        room = Room("ABC123")
        room.add_player(user_id=1)

        result = room.transfer_host(user_id=999)

        assert isinstance(result, Failure)
        assert result.error.code == ErrorType.USER_NOT_IN_ROOM

    def test_transfer_host_to_current_host(self):
        """Test transferring host to current host fails."""
        room = Room("ABC123")
        room.add_player(user_id=1)
        room.add_player(user_id=2)

        result = room.transfer_host(user_id=1)

        assert isinstance(result, Failure)
        assert result.error.code == ErrorType.USER_ALREADY_HOST

    def test_transfer_host_with_no_host(self):
        """Test transferring host when no host exists."""
        room = Room("ABC123")
        room.host_id = None

        result = room.transfer_host(user_id=1)

        assert isinstance(result, Failure)
        assert result.error.code == ErrorType.NO_HOST_IN_ROOM


class TestGetPlayer:
    """Test getting player by ID."""

    def test_get_existing_player(self):
        """Test retrieving existing player."""
        room = Room("ABC123")
        room.add_player(user_id=1)

        player = room.get_player(user_id=1)

        assert player is not None
        assert player.user_id == 1

    def test_get_nonexistent_player(self):
        """Test retrieving nonexistent player."""
        room = Room("ABC123")
        player = room.get_player(user_id=999)

        assert player is None
