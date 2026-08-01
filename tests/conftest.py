"""Pytest configuration and shared fixtures for room_engine tests."""
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Also add room_engine to path so 'from core' works
room_engine_path = src_path / "room_engine"
sys.path.insert(0, str(room_engine_path))

import pytest

from room_engine.rooms.room_manager import RoomManager
from room_engine.handlers.create_room_handler import CreateRoomHandler
from room_engine.handlers.join_room_handler import JoinRoomHandler
from room_engine.handlers.leave_room_handler import LeaveRoomHandler


@pytest.fixture
def room_manager():
    """Fixture providing a fresh RoomManager instance."""
    return RoomManager()


@pytest.fixture
def create_room_handler(room_manager):
    """Fixture providing CreateRoomHandler with a RoomManager."""
    return CreateRoomHandler(room_manager)


@pytest.fixture
def join_room_handler(room_manager):
    """Fixture providing JoinRoomHandler with a RoomManager."""
    return JoinRoomHandler(room_manager)


@pytest.fixture
def leave_room_handler(room_manager):
    """Fixture providing LeaveRoomHandler with a RoomManager."""
    return LeaveRoomHandler(room_manager)
