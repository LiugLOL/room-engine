from room import room
import random
from models.user import User
class RoomManager:
    def __init__(self):
        self.rooms = {}

    def generate_room_code(self):
        letras = "ABCDEFGHJKLMNPQRSTUVWXYZ"
        numeros = "23456789"
        while True:
            codigo = ""
            for _ in range(3):
                letra = random.choice(letras)
                codigo += letra
            for _ in range(3):
                numero = random.choice(numeros)
                codigo += numero
            if codigo in self.rooms:
                continue
            break
        return codigo
    def create_room(self, user_id: int):
        room_code = self.generate_room_code()
        new_room = room.Room(room_code)

        self.rooms[room_code] = new_room

        new_room.add_player(user_id)
        return room_code

    def join_room(self, room_code: str, user_id: int):
        if room_code not in self.rooms:
            return "Error, there is no room with that id"

        room_selected = self.rooms[room_code]

        room_selected.add_player(user_id)
        return "Successfully entered room"

    def leave_room(self, room_code: str, user_id: int):
        if room_code not in self.rooms:
            return "Error, there is no room with that id"

        room_selected = self.rooms[room_code]
        room_selected.remove_player(user_id)

        #If the room is empty, the room is deleted.
        if len(room_selected.players) == 0:
            del self.rooms[room_code]

        return "Successfully left room"
    def get_players_room(self, user_id):
        for lobby in self.rooms.values():
            if user_id in lobby.players:
                return list(lobby.players.values())
        return None
