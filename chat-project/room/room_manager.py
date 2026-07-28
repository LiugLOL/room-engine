from room import room
import random


class RoomManager:

    def __init__(self):
        self.rooms = {}


    def generate_room_code(self):
        letras = "ABCDEFGHJKLMNPQRSTUVWXYZ"
        numeros = "23456789"

        while True:
            codigo = ""

            for _ in range(3):
                codigo += random.choice(letras)

            for _ in range(3):
                codigo += random.choice(numeros)

            if codigo not in self.rooms:
                return codigo


    def create_room(self, user_id: int):

        room_code = self.generate_room_code()

        new_room = room.Room(room_code)

        self.rooms[room_code] = new_room

        result = new_room.add_player(user_id)

        return {
            "success": True,
            "room_code": room_code,
            "player": result["player"]
        }


    def join_room(self, room_code: str, user_id: int):

        if room_code not in self.rooms:
            return {
                "success": False,
                "error": "ROOM_NOT_FOUND"
            }


        selected_room = self.rooms[room_code]

        result = selected_room.add_player(user_id)

        return result



    def leave_room(self, room_code: str, user_id: int):

        if room_code not in self.rooms:
            return {
                "success": False,
                "error": "ROOM_NOT_FOUND"
            }


        selected_room = self.rooms[room_code]

        result = selected_room.remove_player(user_id)


        if not result["success"]:
            return result


        # guarda informações antes de apagar
        deleted = False

        if len(selected_room.players) == 0:
            del self.rooms[room_code]
            deleted = True


        return {
            "success": True,
            "player": result["player"],
            "room_deleted": deleted
        }



    def get_players_room(self, user_id: int):

        for lobby in self.rooms.values():

            if user_id in lobby.players:
                return list(lobby.players.values())

        return None



    def get_user_room(self, user_id: int):

        for lobby in self.rooms.values():

            if user_id in lobby.players:
                return lobby.code

        return None



    def get_room(self, room_code:str):

        return self.rooms.get(room_code)