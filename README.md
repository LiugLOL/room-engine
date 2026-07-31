# Room Engine

A reusable room management engine written in Python.

The goal of this project is to provide a transport-independent foundation for real-time applications such as chats, multiplayer games and collaborative systems.

The engine contains only business logic.

It has no knowledge of:

- FastAPI
- WebSockets
- JSON
- HTTP
- CLI
- Discord
- any other transport layer

## Current features

- Room creation
- Join and leave rooms
- Automatic host transfer
- Typed result objects
- Command/Handler architecture
- Unit tested with pytest

## Project status

This project is under active development.

Current roadmap:

- [x] Core room management
- [x] Handler architecture
- [x] Unit tests
- [ ] Dispatcher
- [ ] Engine facade
- [ ] Transport adapters
- [ ] Event system

## Project structure

```

src/
room_engine/
tests/
examples/

```

## Philosophy

The engine should be reusable by different interfaces without changing its business rules.

Possible integrations include:

- FastAPI
- WebSockets
- CLI
- Discord bots
- Multiplayer games
