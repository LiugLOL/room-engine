from room_engine.commands import (
    CreateRoomCommand,
    JoinRoomCommand,
    LeaveRoomCommand,
)

from room_engine.engine import RoomEngine
from room_engine.core.result import Success

engine = RoomEngine()

create_result = engine.execute(CreateRoomCommand(user_id=1))

assert isinstance(create_result, Success)

room_code = create_result.value.room.code

join_result = engine.execute(
    JoinRoomCommand(
        user_id=2,
        room_code=room_code,
    )
)

leave_result = engine.execute(
    LeaveRoomCommand(
        user_id=2,
        room_code=room_code,
    )
)

print(create_result)
print(join_result)
print(leave_result)