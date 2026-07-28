""""
User model, shows the whole user structure and data
"""

from dataclasses import dataclass
@dataclass
class User:
    id: int
    nickname: str
