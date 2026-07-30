"""Tests for the LeaveRoomHandler class."""
import pytest
from room_engine.commands import CreateRoomCommand, JoinRoomCommand, LeaveRoomCommand
from room_engine.handlers.create_room_handler import CreateRoomHandler
from room_engine.handlers.join_room_handler import JoinRoomHandler
from room_engine.handlers.leave_room_handler import LeaveRoomHandler
from room_engine.rooms.room_player import PlayerRole
from room_engine.core.result import Success, Failure
from room_engine.core.error_types import ErrorType


class TestLeaveRoomHandler:
    """Test LeaveRoomHandler command handling."""

    def test_handle_regular_player_leaves(self, leave_room_handler, room_manager):
        """Test regular player leaving room."""
        # Setup: Create room and join
        create_handler = CreateRoomHandler(room_manager)
        join_handler = JoinRoomHandler(room_manager)

        create_result = create_handler.handle(CreateRoomCommand(user_id=1))
        room_code = create_result.value.room.code

        join_handler.handle(JoinRoomCommand(user_id=2, room_code=room_code))

        # Leave
        command = LeaveRoomCommand(user_id=2, room_code=room_code)
        result = leave_room_handler.handle(command)

        assert isinstance(result, Success)
        assert result.value.player.user_id == 2
        assert result.value.room_deleted is False
        assert result.value.new_host is None

    def test_handle_leave_nonexistent_room_fails(self, leave_room_handler):
        """Test leaving nonexistent room fails."""
        command = LeaveRoomCommand(user_id=1, room_code="INVALID")
        result = leave_room_handler.handle(command)

        assert isinstance(result, Failure)
        assert result.error.code == ErrorType.ROOM_NOT_FOUND

    def test_handle_user_not_in_room_fails(self, leave_room_handler, room_manager):
        """Test leaving room when not a member fails."""
        # Create room
        create_handler = CreateRoomHandler(room_manager)
        create_result = create_handler.handle(CreateRoomCommand(user_id=1))
        room_code = create_result.value.room.code

        # Try to leave as someone not in room
        command = LeaveRoomCommand(user_id=999, room_code=room_code)
        result = leave_room_handler.handle(command)

        assert isinstance(result, Failure)
        assert result.error.code == ErrorType.USER_NOT_IN_ROOM

    def test_handle_host_leaves_transfers_host(self, leave_room_handler, room_manager):
        """Test that host leaving transfers host to next player."""
        # Setup: Create room with 3 players
        create_handler = CreateRoomHandler(room_manager)
        join_handler = JoinRoomHandler(room_manager)

        create_result = create_handler.handle(CreateRoomCommand(user_id=1))
        room_code = create_result.value.room.code

        join_handler.handle(JoinRoomCommand(user_id=2, room_code=room_code))
        join_handler.handle(JoinRoomCommand(user_id=3, room_code=room_code))

        # Host leaves
        command = LeaveRoomCommand(user_id=1, room_code=room_code)
        result = leave_room_handler.handle(command)

        assert isinstance(result, Success)
        assert result.value.new_host is not None
        assert result.value.new_host.user_id == 2
        assert result.value.new_host.role == PlayerRole.HOST
        assert result.value.room_deleted is False

    def test_handle_last_player_leaves_deletes_room(self, leave_room_handler, room_manager):
        """Test that last player leaving deletes room."""
        # Create room with single player
        create_handler = CreateRoomHandler(room_manager)
        create_result = create_handler.handle(CreateRoomCommand(user_id=1))
        room_code = create_result.value.room.code

        # Host leaves (and is last)
        command = LeaveRoomCommand(user_id=1, room_code=room_code)
        result = leave_room_handler.handle(command)

        assert isinstance(result, Success)
        assert result.value.room_deleted is True
        assert result.value.new_host is None
        assert room_manager.get_room(room_code) is None

    def test_handle_sequential_leaves_delete_on_last(self, leave_room_handler, room_manager):
        """Test that room is deleted when last of multiple players leaves."""
        # Setup: Create room with 3 players
        create_handler = CreateRoomHandler(room_manager)
        join_handler = JoinRoomHandler(room_manager)

        create_result = create_handler.handle(CreateRoomCommand(user_id=1))
        room_code = create_result.value.room.code

        join_handler.handle(JoinRoomCommand(user_id=2, room_code=room_code))
        join_handler.handle(JoinRoomCommand(user_id=3, room_code=room_code))

        # Players leave sequentially
        leave_room_handler.handle(LeaveRoomCommand(user_id=1, room_code=room_code))
        leave_room_handler.handle(LeaveRoomCommand(user_id=2, room_code=room_code))
        result = leave_room_handler.handle(LeaveRoomCommand(user_id=3, room_code=room_code))

        assert isinstance(result, Success)
        assert result.value.room_deleted is True
        assert room_manager.get_room(room_code) is None

    def test_handle_preserves_command_parameters(self, leave_room_handler, room_manager):
        """Test that handler uses correct user_id and room_code from command."""
        # Setup
        create_handler = CreateRoomHandler(room_manager)
        join_handler = JoinRoomHandler(room_manager)

        create_result = create_handler.handle(CreateRoomCommand(user_id=100))
        room_code = create_result.value.room.code

        join_handler.handle(JoinRoomCommand(user_id=200, room_code=room_code))
        join_handler.handle(JoinRoomCommand(user_id=300, room_code=room_code))

        # Leave with specific parameters
        command = LeaveRoomCommand(user_id=200, room_code=room_code)
        result = leave_room_handler.handle(command)

        assert isinstance(result, Success)
        assert result.value.player.user_id == 200
        assert room_manager.get_user_room(user_id=200) is None
        assert room_manager.get_user_room(user_id=300) == room_code
