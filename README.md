# Room Engine

A reusable, transport-independent room management engine for multiplayer applications.

## Overview

**Room Engine** is a Python library that provides core room management functionality without dependencies on networking protocols, user interfaces, or specific frameworks. It handles room creation, player membership, host election, and command processing—making it easy to integrate into any application architecture.

The engine is designed to be:
- **Independent**: Completely decoupled from networking and UI layers
- **Reusable**: A clean, modular core you can embed in any application
- **Testable**: Comprehensive test coverage (66 unit tests) with dependency injection throughout

## Features

- ✅ Room creation with automatic host assignment
- ✅ Player join/leave operations
- ✅ Automatic host election when the host leaves
- ✅ Command Dispatcher for routing operations
- ✅ Handler architecture for extensibility
- ✅ Engine facade for application integration
- ✅ Typed Success/Failure results for error handling
- ✅ Comprehensive unit test coverage

## Project Structure

```
src/
├── room_engine/           # Core engine implementation
│   ├── commands.py        # Command definitions (CreateRoom, JoinRoom, LeaveRoom)
│   ├── engine.py          # RoomEngine facade
│   ├── dispatcher.py      # Command dispatcher
│   ├── core/              # Core types and utilities
│   │   ├── result.py      # Success/Failure types
│   │   └── error_types.py # Error categories
│   ├── handlers/          # Command handlers
│   ├── rooms/             # Room management
│   └── users/             # User/player management
tests/                      # Unit tests (66 passing)
graphify-out/              # Architecture analysis
basic_usage/               # Example usage
```

## Installation

### Clone the repository

```bash
git clone https://github.com/LiugLOL/room-engine.git
cd room-engine
```

### Create a virtual environment

```bash
python -m venv .venv
```

### Activate the virtual environment

**On macOS/Linux:**
```bash
source .venv/bin/activate
```

**On Windows:**
```bash
.\.venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

## Running Tests

Execute the test suite with pytest:

```bash
python -m pytest -q
```

The project currently contains **66 passing unit tests** covering all core functionality.

## Basic Usage

Here's a minimal example using the public API:

```python
from room_engine.commands import (
    CreateRoomCommand,
    JoinRoomCommand,
    LeaveRoomCommand,
)
from room_engine.engine import RoomEngine
from room_engine.core.result import Success

# Create engine instance
engine = RoomEngine()

# Create a new room (user 1 becomes the host)
create_result = engine.execute(CreateRoomCommand(user_id=1))

assert isinstance(create_result, Success)
room_code = create_result.value.room.code

# Join the room (user 2)
join_result = engine.execute(
    JoinRoomCommand(
        user_id=2,
        room_code=room_code,
    )
)

# Leave the room
leave_result = engine.execute(
    LeaveRoomCommand(
        user_id=2,
        room_code=room_code,
    )
)
```

## Architecture

The engine follows a layered architecture with clear separation of concerns:

- **Commands**: Represent operations (CreateRoom, JoinRoom, LeaveRoom)
- **Dispatcher**: Routes commands to appropriate handlers
- **Handlers**: Execute business logic for each command type
- **Core Models**: Room, User/Player, with automatic host election
- **Results**: Typed Success/Failure responses with structured error information

Key architectural principles:
- **Transport Independent**: No built-in networking—integrate via the command/result pattern
- **Modular**: Each component has a single responsibility
- **Type Safe**: Results explicitly communicate success or failure
- **Testable**: Dependency injection throughout enables easy testing

## Design Goals

The Room Engine prioritizes:

- **Reusability**: A self-contained library that works in any Python application
- **Transport Independence**: No assumptions about networking (WebSockets, HTTP, etc.)
- **Modularity**: Clear separation between core logic, commands, handlers, and models
- **Ease of Integration**: Simple facade (`RoomEngine`) for basic usage
- **Testability**: Comprehensive test coverage with isolated components

## Future Integrations

The engine's design enables easy integration with:

- **FastAPI** / REST APIs for web applications
- **WebSockets** for real-time multiplayer
- **Discord** bots for community spaces
- **CLI** tools for terminal-based applications
- **Multiplayer games** via game engine SDKs (Unity, Godot, etc.)

These integrations would handle networking, serialization, and UI—while Room Engine provides the core business logic.

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

**Created with ❤️ for building reusable, modular systems**
