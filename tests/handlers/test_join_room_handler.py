"""Tests for the JoinRoomHandler class."""
import pytest
from room_engine.commands import CreateRoomCommand, JoinRoomCommand
from room_engine.handlers.create_room_handler import CreateRoomHandler
from room_engine.handlers.join_room_handler import JoinRoomHandler
from room_engine.rooms.room_player import PlayerRole
from room_engine.core.result import Success, Failure
from room_engine.core.error_types import ErrorType


class TestJoinRoomHandler:
    """Test JoinRoomHandler command handling."""

    def test_handle_joins_existing_room(self, join_room_handler, room_manager):
        """Test joining existing room."""
        # First create a room
        create_handler = CreateRoomHandler(room_manager)
        create_result = create_handler.handle(CreateRoomCommand(user_id=1))
        room_code = create_result.value.room.code

        # Then join it
        command = JoinRoomCommand(user_id=2, room_code=room_code)
        result = join_room_handler.handle(command)

        assert isinstance(result, Success)
        assert result.value.user_id == 2
        assert result.value.role == PlayerRole.PLAYER

    def test_handle_join_nonexistent_room_fails(self, join_room_handler):
        """Test joining nonexistent room fails."""
        command = JoinRoomCommand(user_id=1, room_code="INVALID")
        result = join_room_handler.handle(command)

        assert isinstance(result, Failure)
        assert result.error.code == ErrorType.ROOM_NOT_FOUND

    def test_handle_join_twice_fails(self, join_room_handler, room_manager):
        """Test joining same room twice with same user fails."""
        # Create room
        create_handler = CreateRoomHandler(room_manager)
        create_result = create_handler.handle(CreateRoomCommand(user_id=1))
        room_code = create_result.value.room.code

        # Join first time
        join_room_handler.handle(JoinRoomCommand(user_id=2, room_code=room_code))

        # Try to join again
        result = join_room_handler.handle(JoinRoomCommand(user_id=2, room_code=room_code))

        assert isinstance(result, Failure)
        assert result.error.code == ErrorType.USER_ALREADY_IN_ROOM

    def test_handle_multiple_players_join_same_room(self, join_room_handler, room_manager):
        """Test multiple players joining same room."""
        # Create room
        create_handler = CreateRoomHandler(room_manager)
        create_result = create_handler.handle(CreateRoomCommand(user_id=1))
        room_code = create_result.value.room.code

        # Multiple joins
        result1 = join_room_handler.handle(JoinRoomCommand(user_id=2, room_code=room_code))
        result2 = join_room_handler.handle(JoinRoomCommand(user_id=3, room_code=room_code))
        result3 = join_room_handler.handle(JoinRoomCommand(user_id=4, room_code=room_code))

        assert isinstance(result1, Success)
        assert isinstance(result2, Success)
        assert isinstance(result3, Success)

        room = room_manager.get_room(room_code)
        assert len(room.players) == 4

    def test_handle_join_preserves_command_parameters(self, join_room_handler, room_manager):
        """Test that handler uses correct user_id and room_code from command."""
        # Create room with user 100
        create_handler = CreateRoomHandler(room_manager)
        create_result = create_handler.handle(CreateRoomCommand(user_id=100))
        room_code = create_result.value.room.code

        # Join with user 200
        command = JoinRoomCommand(user_id=200, room_code=room_code)
        result = join_room_handler.handle(command)

        assert isinstance(result, Success)
        assert result.value.user_id == 200
        assert room_manager.get_user_room(user_id=200) == room_code
