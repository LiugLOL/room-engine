from enum import Enum


class ErrorType(Enum):
    """Stable categories for domain failures returned by room operations.

    These values let callers distinguish expected validation and state errors
    without parsing human-readable messages.
    """

    # Room errors
    ROOM_NOT_FOUND = "room_not_found"
    USER_ALREADY_IN_ROOM = "user_already_in_room"
    USER_NOT_IN_ROOM = "user_not_in_room"
    NO_HOST_IN_ROOM = "no_host_in_room"
    USER_ALREADY_HOST = "user_already_host"

    # Message errors
    UNKNOWN_MESSAGE_TYPE = "unknown_message_type"
    INVALID_PAYLOAD = "invalid_payload"

    # Permission errors
    PERMISSION_DENIED = "permission_denied"
