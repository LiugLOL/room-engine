"""Tests for the CreateRoomHandler class."""
import pytest
from room_engine.commands import CreateRoomCommand
from room_engine.handlers.create_room_handler import CreateRoomHandler
from room_engine.rooms.room_player import PlayerRole
from room_engine.core.result import Success


class TestCreateRoomHandler:
    """Test CreateRoomHandler command handling."""

    def test_handle_creates_room_with_command(self, create_room_handler, room_manager):
        """Test that handler creates room with user from command."""
        command = CreateRoomCommand(user_id=42)
        result = create_room_handler.handle(command)

        assert isinstance(result, Success)
        assert result.value.host.user_id == 42
        assert result.value.host.role == PlayerRole.HOST

    def test_handle_returns_room_creation_result(self, create_room_handler):
        """Test that handler returns proper RoomCreation object."""
        command = CreateRoomCommand(user_id=1)
        result = create_room_handler.handle(command)

        assert isinstance(result, Success)
        assert hasattr(result.value, 'room')
        assert hasattr(result.value, 'host')
        assert result.value.room is not None
        assert result.value.host is not None

    def test_multiple_room_creations(self, create_room_handler):
        """Test creating multiple rooms."""
        command1 = CreateRoomCommand(user_id=1)
        command2 = CreateRoomCommand(user_id=2)

        result1 = create_room_handler.handle(command1)
        result2 = create_room_handler.handle(command2)

        assert result1.value.room.code != result2.value.room.code
        assert result1.value.host.user_id == 1
        assert result2.value.host.user_id == 2
