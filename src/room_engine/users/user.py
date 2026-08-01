from dataclasses import dataclass


@dataclass
class User:
    """Represent the user identity used by room-facing features.

    Args:
        id: Unique user identifier.
        nickname: Display name associated with the user.
    """

    id: int
    nickname: str
