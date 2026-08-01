"""Tests for the RoomEngine facade."""
import pytest

from room_engine.commands import (
    Command,
    CreateRoomCommand,
    JoinRoomCommand,
    LeaveRoomCommand,
)
from room_engine.core.error_types import ErrorType
from room_engine.core.result import Failure, Success
from room_engine.engine import RoomEngine
from room_engine.handlers import (
    CreateRoomHandler,
    JoinRoomHandler,
    LeaveRoomHandler,
)
from room_engine.rooms.room_manager import RoomManager
from room_engine.rooms.room_player import PlayerRole


@pytest.fixture
def room_engine():
    """Fixture providing a fresh RoomEngine instance."""
    return RoomEngine()


class TestRoomEngine:
    """Test RoomEngine command dispatching and state management."""

    def test_initializes_successfully(self, room_engine):
        """Test that engine initializes its room manager and dispatcher."""
        assert isinstance(room_engine.room_manager, RoomManager)
        assert room_engine.dispatcher is not None

    def test_initialization_configures_dispatcher(self, room_engine):
        """Test that engine registers handlers for supported commands."""
        handlers = room_engine.dispatcher._handlers

        assert isinstance(handlers[CreateRoomCommand], CreateRoomHandler)
        assert isinstance(handlers[JoinRoomCommand], JoinRoomHandler)
        assert isinstance(handlers[LeaveRoomCommand], LeaveRoomHandler)
        assert all(
            handler._room_manager is room_engine.room_manager
            for handler in handlers.values()
        )

    def test_execute_creates_room(self, room_engine):
        """Test that engine creates a room through CreateRoomCommand."""
        result = room_engine.execute(CreateRoomCommand(user_id=1))

        assert isinstance(result, Success)
        assert result.value.host.user_id == 1
        assert result.value.host.role == PlayerRole.HOST
        assert room_engine.room_manager.get_room(result.value.room.code) is result.value.room

    def test_execute_joins_existing_room(self, room_engine):
        """Test that engine joins an existing room through JoinRoomCommand."""
        create_result = room_engine.execute(CreateRoomCommand(user_id=1))
        room_code = create_result.value.room.code

        result = room_engine.execute(JoinRoomCommand(user_id=2, room_code=room_code))

        assert isinstance(result, Success)
        assert result.value.user_id == 2
        assert result.value.role == PlayerRole.PLAYER

    def test_execute_leaves_room(self, room_engine):
        """Test that engine leaves a room through LeaveRoomCommand."""
        create_result = room_engine.execute(CreateRoomCommand(user_id=1))
        room_code = create_result.value.room.code
        room_engine.execute(JoinRoomCommand(user_id=2, room_code=room_code))

        result = room_engine.execute(LeaveRoomCommand(user_id=2, room_code=room_code))

        assert isinstance(result, Success)
        assert result.value.player.user_id == 2
        assert room_engine.room_manager.get_user_room(user_id=2) is None

    def test_multiple_commands_share_room_manager_state(self, room_engine):
        """Test that all commands operate on the engine's one room manager."""
        create_result = room_engine.execute(CreateRoomCommand(user_id=1))
        room_code = create_result.value.room.code
        room_engine.execute(JoinRoomCommand(user_id=2, room_code=room_code))

        room = room_engine.room_manager.get_room(room_code)

        assert list(room.players) == [1, 2]
        assert room_engine.room_manager.get_user_room(user_id=2) == room_code

    def test_execute_unknown_command_raises_value_error(self, room_engine):
        """Test that engine raises for commands without registered handlers."""
        class UnknownCommand(Command):
            pass

        with pytest.raises(ValueError, match="No handler registered for UnknownCommand"):
            room_engine.execute(UnknownCommand())

    def test_independent_engines_do_not_share_state(self):
        """Test that each engine receives an independent room manager."""
        first_engine = RoomEngine()
        second_engine = RoomEngine()
        create_result = first_engine.execute(CreateRoomCommand(user_id=1))
        room_code = create_result.value.room.code

        result = second_engine.execute(JoinRoomCommand(user_id=2, room_code=room_code))

        assert first_engine.room_manager is not second_engine.room_manager
        assert isinstance(result, Failure)
        assert result.error.code == ErrorType.ROOM_NOT_FOUND

    def test_execute_create_join_leave_flow(self, room_engine):
        """Test the complete create, join, and leave command flow."""
        create_result = room_engine.execute(CreateRoomCommand(user_id=1))
        room_code = create_result.value.room.code
        join_result = room_engine.execute(JoinRoomCommand(user_id=2, room_code=room_code))
        leave_result = room_engine.execute(LeaveRoomCommand(user_id=2, room_code=room_code))

        room = room_engine.room_manager.get_room(room_code)

        assert isinstance(create_result, Success)
        assert isinstance(join_result, Success)
        assert isinstance(leave_result, Success)
        assert list(room.players) == [1]
