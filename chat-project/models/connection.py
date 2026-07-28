""""
Connection model, shows how the user is connected for the connection_manager
"""
from dataclasses import dataclass
from fastapi import WebSocket
from models.user import User

@dataclass
class Connection:
    user: User
    websocket: WebSocket
