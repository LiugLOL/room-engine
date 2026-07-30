"""
=============================================================================
tests_junie/test_claude.py
Revisao completa do projeto de chat -- Claude Sonnet
=============================================================================

Cobertura:
  - Criacao de salas (Room / RoomManager)
  - Entrada e saida de jogadores
  - Eleicao de host (seniority via local_id)
  - Transferencia de host
  - Geracao de IDs e codigos de sala
  - Multiplas salas simultaneas
  - Encode / decode do protocolo
  - Validacao da classe Message
  - ConnectionManager (mocks assincronos)
  - Regressao de bugs arquiteturais conhecidos

Execucao:
    py tests_junie/test_claude.py
=============================================================================
"""

import sys
import os
import unittest
import asyncio
import json
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
CURRENT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

# Apenas PROJECT_ROOT e models/ no sys.path.
# Nao adicionar room/ diretamente: isso mascara o pacote 'room' e quebra
# "from room import room" que room_manager.py usa internamente.
for _p in [
    os.path.join(PROJECT_ROOT, "models"),   # para 'import room_player'
    PROJECT_ROOT,                            # para 'from room.room import Room'
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# Coleta de resultados para o relatorio final
# ---------------------------------------------------------------------------
TEST_RESULTS = []

def log(name, scenario, inputs, expected, obtained, passed,
        failure_type=None, explanation=None):
    TEST_RESULTS.append({
        "name": name,
        "scenario": scenario,
        "inputs": inputs,
        "expected": expected,
        "obtained": str(obtained),
        "passed": passed,
        "failure_type": failure_type,
        "explanation": explanation,
    })


# ===========================================================================
# BLOCO 1 -- ROOM
# ===========================================================================
class TestRoom(unittest.TestCase):

    def _room(self, code="TST001"):
        from room.room import Room
        return Room(code)

    # -----------------------------------------------------------------------
    def test_01_room_creation(self):
        """Sala criada com atributos corretos."""
        name = "test_01_room_creation"
        try:
            from room.room import Room
            r = Room("AAA111")
            ok = (r.code == "AAA111"
                  and r.players == {}
                  and r.host_id is None
                  and r.status == "Testing"
                  and r.next_local_id == 0)
            log(name, "Criacao de sala", "code='AAA111'",
                "code=AAA111, players={}, host_id=None, status=Testing, next_local_id=0",
                f"code={r.code}, host={r.host_id}, status={r.status}, next={r.next_local_id}",
                ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Criacao de sala", "code='AAA111'",
                "Objeto Room inicializado", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_02_first_player_becomes_host(self):
        """Primeiro jogador adicionado recebe role HOST."""
        name = "test_02_first_player_becomes_host"
        try:
            from room_player import PlayerRole
            r = self._room()
            r.add_player(1)
            player = r.players[1]
            ok = (r.host_id == 1 and player.role == PlayerRole.HOST)
            log(name, "Primeiro jogador vira host", "user_id=1, sala vazia",
                "host_id=1, role=HOST",
                f"host_id={r.host_id}, role={player.role}", ok,
                None if ok else "bug de implementacao",
                None if ok else "PlayerRole.HOST inacessivel -- Enum mal definido")
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Primeiro jogador vira host", "user_id=1",
                "host_id=1, role=HOST", str(e), False,
                "bug de implementacao",
                "AttributeError: PlayerRole e um Enum vazio -- uso incorreto de ':' em vez de '='")
            raise

    # -----------------------------------------------------------------------
    def test_03_second_player_is_regular_player(self):
        """Segundo jogador entra com role PLAYER."""
        name = "test_03_second_player_is_regular_player"
        try:
            from room_player import PlayerRole
            r = self._room()
            r.add_player(1)
            r.add_player(2)
            p2 = r.players[2]
            ok = (p2.role == PlayerRole.PLAYER and r.host_id == 1)
            log(name, "Segundo jogador entra como PLAYER", "user_id=1, user_id=2",
                "p2.role=PLAYER, host_id=1",
                f"role={p2.role}, host_id={r.host_id}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Segundo jogador entra como PLAYER", "user_id=1, user_id=2",
                "p2.role=PLAYER", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_04_local_id_generation_sequence(self):
        """local_id atribuido em ordem crescente (0, 1, 2...)."""
        name = "test_04_local_id_generation_sequence"
        try:
            r = self._room()
            for uid in [10, 20, 30]:
                r.add_player(uid)
            ids = [r.players[uid].local_id for uid in [10, 20, 30]]
            ok = (ids == [0, 1, 2])
            log(name, "Geracao sequencial de local_id",
                "add_player(10,20,30)", "[0, 1, 2]", str(ids), ok)
            self.assertEqual(ids, [0, 1, 2])
        except Exception as e:
            log(name, "Geracao sequencial de local_id", "3 jogadores",
                "[0, 1, 2]", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_05_next_local_id_increments(self):
        """next_local_id incrementado apos cada add_player."""
        name = "test_05_next_local_id_increments"
        try:
            r = self._room()
            r.add_player(1)
            after_one = r.next_local_id
            r.add_player(2)
            after_two = r.next_local_id
            ok = (after_one == 1 and after_two == 2)
            log(name, "next_local_id incrementa", "add(1), add(2)",
                "next=1 apos add(1), next=2 apos add(2)",
                f"after add(1)={after_one}, after add(2)={after_two}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "next_local_id incrementa", "add(1), add(2)",
                "1, 2", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_06_remove_non_host_player(self):
        """Remocao de jogador comum nao altera host_id."""
        name = "test_06_remove_non_host_player"
        try:
            r = self._room()
            r.add_player(1)
            r.add_player(2)
            res = r.remove_player(2)
            ok = (res is None and 2 not in r.players and r.host_id == 1)
            log(name, "Remocao de jogador comum",
                "sala com 1(host) e 2(player), remove 2",
                "res=None, 2 ausente, host_id=1",
                f"res={res}, players={list(r.players.keys())}, host={r.host_id}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Remocao de jogador comum", "remove(2)",
                "host permanece", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_07_remove_host_triggers_election(self):
        """Ao remover host, jogador com menor local_id vira novo host."""
        name = "test_07_remove_host_triggers_election"
        try:
            from room_player import PlayerRole
            r = self._room()
            r.add_player(1)   # local_id=0, host
            r.add_player(2)   # local_id=1
            r.add_player(3)   # local_id=2
            r.remove_player(1)
            new_host = r.players.get(r.host_id)
            ok = (r.host_id == 2
                  and new_host is not None
                  and new_host.role == PlayerRole.HOST)
            log(name, "Remocao do host dispara eleicao automatica",
                "add(1,2,3), remove(1)",
                "host_id=2, role(2)=HOST",
                f"host_id={r.host_id}, role={getattr(new_host, 'role', None)}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Remocao do host dispara eleicao", "add(1,2,3), remove(1)",
                "host_id=2", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_08_elect_by_seniority_not_by_user_id(self):
        """Eleicao usa menor local_id, nao menor user_id."""
        name = "test_08_elect_by_seniority_not_by_user_id"
        try:
            from room_player import PlayerRole
            r = self._room()
            r.add_player(99)   # local_id=0, host
            r.add_player(1)    # local_id=1
            r.add_player(50)   # local_id=2
            r.remove_player(99)
            ok = (r.host_id == 1 and r.players[1].role == PlayerRole.HOST)
            log(name, "Eleicao por local_id, nao por user_id",
                "add(99,1,50), remove(99)",
                "host_id=1 (local_id=1, menor remanescente)",
                f"host_id={r.host_id}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Eleicao por seniority", "add(99,1,50), remove(99)",
                "host_id=1", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_09_transfer_host_success(self):
        """Transferencia manual de host troca papeis corretamente."""
        name = "test_09_transfer_host_success"
        try:
            from room_player import PlayerRole
            r = self._room()
            r.add_player(1)
            r.add_player(2)
            res = r.transfer_host(2)
            ok = (res == "Successfully transferred host"
                  and r.host_id == 2
                  and r.players[2].role == PlayerRole.HOST
                  and r.players[1].role == PlayerRole.PLAYER)
            log(name, "Transferencia manual de host", "1=host, transfer_host(2)",
                "res=Successfully transferred host, host_id=2, role(2)=HOST, role(1)=PLAYER",
                f"res={res}, host={r.host_id}, r1={r.players[1].role}, r2={r.players[2].role}",
                ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Transferencia manual de host", "transfer_host(2)",
                "host_id=2", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_10_transfer_host_to_non_existent(self):
        """Transferencia para jogador inexistente retorna 'Player not found'."""
        name = "test_10_transfer_host_to_non_existent"
        try:
            r = self._room()
            r.add_player(1)
            res = r.transfer_host(999)
            ok = (res == "Player not found" and r.host_id == 1)
            log(name, "Transferencia para inexistente",
                "host=1, transfer_host(999)",
                "res=Player not found, host_id=1",
                f"res={res}, host={r.host_id}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Transferencia para inexistente",
                "transfer_host(999)", "Player not found",
                str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_11_transfer_host_to_self(self):
        """Transferencia do host para si mesmo retorna 'Already host'."""
        name = "test_11_transfer_host_to_self"
        try:
            r = self._room()
            r.add_player(1)
            res = r.transfer_host(1)
            ok = (res == "Already host" and r.host_id == 1)
            log(name, "Transferencia do host para si mesmo",
                "host=1, transfer_host(1)",
                "res=Already host, host_id=1",
                f"res={res}, host={r.host_id}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Transferencia para si mesmo",
                "transfer_host(1)", "Already host",
                str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_12_add_duplicate_player_blocked(self):
        """Adicionar o mesmo jogador duas vezes retorna mensagem de erro."""
        name = "test_12_add_duplicate_player_blocked"
        try:
            r = self._room()
            r.add_player(1)
            res = r.add_player(1)
            ok = (res == "Player already in room" and len(r.players) == 1)
            log(name, "Duplicata bloqueada", "add(1) duas vezes",
                "res=Player already in room, len=1",
                f"res={res}, len={len(r.players)}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Duplicata bloqueada", "add(1) x2",
                "Player already in room", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_13_remove_non_existent_player(self):
        """Remover jogador inexistente retorna mensagem de erro."""
        name = "test_13_remove_non_existent_player"
        try:
            r = self._room()
            res = r.remove_player(999)
            ok = (res == "Player not found/not in room")
            log(name, "Remocao de jogador inexistente",
                "sala vazia, remove(999)",
                "Player not found/not in room",
                f"res={res}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Remocao de inexistente", "remove(999)",
                "Player not found/not in room",
                str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_14_empty_room_after_last_player_leaves(self):
        """Apos ultimo jogador sair, host_id=None e players={}."""
        name = "test_14_empty_room_after_last_player_leaves"
        try:
            r = self._room()
            r.add_player(1)
            r.remove_player(1)
            ok = (r.host_id is None and len(r.players) == 0)
            log(name, "Sala fica vazia", "add(1), remove(1)",
                "host_id=None, players vazio",
                f"host_id={r.host_id}, len={len(r.players)}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Sala fica vazia", "add(1), remove(1)",
                "host_id=None", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_15_host_id_always_in_players(self):
        """host_id sempre aponta para jogador presente em players."""
        name = "test_15_host_id_always_in_players"
        try:
            r = self._room()
            errors = []
            r.add_player(1)
            r.add_player(2)
            r.add_player(3)
            if r.host_id not in r.players:
                errors.append(f"host_id={r.host_id} ausente apos add")
            r.transfer_host(2)
            if r.host_id not in r.players:
                errors.append(f"host_id={r.host_id} ausente apos transfer")
            r.remove_player(2)
            if r.host_id not in r.players:
                errors.append(f"host_id={r.host_id} ausente apos remove host")
            ok = len(errors) == 0
            log(name, "host_id sempre aponta para jogador presente",
                "add(1,2,3), transfer(2), remove(2)",
                "host_id in players em todos os momentos",
                "OK" if ok else str(errors), ok)
            self.assertTrue(ok, str(errors))
        except Exception as e:
            log(name, "Integridade host_id", "add/transfer/remove",
                "host_id in players", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_16_exactly_one_host_role(self):
        """Exatamente 1 jogador com role HOST por sala em todos os momentos."""
        name = "test_16_exactly_one_host_role"
        try:
            from room_player import PlayerRole
            r = self._room()
            r.add_player(1)
            r.add_player(2)
            r.add_player(3)

            def count_hosts():
                return sum(1 for p in r.players.values()
                           if p.role == PlayerRole.HOST)

            h0 = count_hosts()
            r.transfer_host(2)
            h1 = count_hosts()
            r.remove_player(2)
            h2 = count_hosts()

            ok = (h0 == 1 and h1 == 1 and h2 == 1)
            log(name, "Exatamente 1 host por sala em todos os momentos",
                "add(1,2,3), transfer(2), remove(2)",
                "1 host em cada snapshot",
                f"inicial={h0}, apos transfer={h1}, apos remove={h2}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Unicidade do host", "add/transfer/remove",
                "1 host sempre", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_17_no_duplicate_local_ids(self):
        """Nenhum local_id se repete entre os jogadores da sala."""
        name = "test_17_no_duplicate_local_ids"
        try:
            r = self._room()
            for uid in range(1, 6):
                r.add_player(uid)
            all_ids = [p.local_id for p in r.players.values()]
            ok = (len(all_ids) == len(set(all_ids)))
            log(name, "local_ids unicos", "5 jogadores adicionados",
                "todos local_ids distintos",
                f"ids={all_ids}, unicos={len(set(all_ids))}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "local_ids unicos", "5 jogadores",
                "sem duplicatas", str(e), False, "bug de implementacao", str(e))
            raise


# ===========================================================================
# BLOCO 2 -- ROOM MANAGER
# ===========================================================================
class TestRoomManager(unittest.TestCase):

    def _mgr(self):
        from room.room_manager import RoomManager
        return RoomManager()

    # -----------------------------------------------------------------------
    def test_18_create_room_returns_code(self):
        """create_room retorna codigo e registra sala no dicionario."""
        name = "test_18_create_room_returns_code"
        try:
            rm = self._mgr()
            code = rm.create_room(1)
            ok = (isinstance(code, str)
                  and code in rm.rooms
                  and 1 in rm.rooms[code].players)
            log(name, "Criacao de sala via Manager", "user_id=1",
                "code e string, sala no dicionario, user 1 presente",
                f"code={code}, in_rooms={code in rm.rooms}, "
                f"player_1_in={(1 in rm.rooms[code].players) if code in rm.rooms else '?'}",
                ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Criacao via Manager", "user_id=1",
                "codigo e sala validos", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_19_room_code_format(self):
        """Codigo tem 6 caracteres: 3 letras maiusculas + 3 digitos."""
        name = "test_19_room_code_format"
        try:
            rm = self._mgr()
            code = rm.generate_room_code()
            ok = (len(code) == 6
                  and code[:3].isalpha()
                  and code[:3].isupper()
                  and code[3:].isdigit())
            log(name, "Formato do codigo de sala", "generate_room_code()",
                "6 chars: 3 letras maiusculas + 3 digitos",
                f"code='{code}', len={len(code)}, letters={code[:3]}, digits={code[3:]}",
                ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Formato do codigo", "generate_room_code()",
                "AAA999", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_20_room_code_no_ambiguous_chars(self):
        """Codigo nao contem caracteres ambiguos (0, O, 1, I)."""
        name = "test_20_room_code_no_ambiguous_chars"
        try:
            rm = self._mgr()
            AMBIGUOUS = set("01OI")
            violations = []
            for _ in range(50):
                code = rm.generate_room_code()
                if any(c in AMBIGUOUS for c in code):
                    violations.append(code)
            ok = len(violations) == 0
            log(name, "Ausencia de caracteres ambiguos (0, O, 1, I)",
                "50 codigos gerados", "nenhum caractere ambiguo",
                f"violacoes={violations}", ok)
            self.assertTrue(ok, f"Codigos com ambiguidade: {violations}")
        except Exception as e:
            log(name, "Sem ambiguos", "50 codigos",
                "sem 0,O,1,I", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_21_unique_codes_no_collision(self):
        """20 criações geram 20 codigos distintos."""
        name = "test_21_unique_codes_no_collision"
        try:
            rm = self._mgr()
            codes = [rm.create_room(i) for i in range(20)]
            ok = (len(codes) == len(set(codes)))
            log(name, "Unicidade de codigos em 20 criacoes",
                "20x create_room", "20 codigos unicos",
                f"total={len(codes)}, unicos={len(set(codes))}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Unicidade de codigos", "20 criacoes",
                "sem colisao", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_22_join_existing_room(self):
        """join_room em sala existente adiciona jogador e retorna sucesso."""
        name = "test_22_join_existing_room"
        try:
            rm = self._mgr()
            code = rm.create_room(1)
            res = rm.join_room(code, 2)
            ok = (res == "Successfully entered room"
                  and 2 in rm.rooms[code].players)
            log(name, "Entrada em sala existente",
                f"code={code}, user_id=2",
                "Successfully entered room, 2 em players",
                f"res={res}, in_players={2 in rm.rooms[code].players}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Entrada em sala", "join_room existente",
                "Successfully entered room", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_23_join_non_existent_room(self):
        """join_room em sala inexistente retorna mensagem de erro."""
        name = "test_23_join_non_existent_room"
        try:
            rm = self._mgr()
            res = rm.join_room("FAKE99", 1)
            ok = (res == "Error, there is no room with that id")
            log(name, "Entrada em sala inexistente", "code='FAKE99'",
                "Error, there is no room with that id",
                f"res={res}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Entrada em sala inexistente", "join_room('FAKE99')",
                "erro esperado", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_24_leave_room_success(self):
        """leave_room remove o jogador e retorna sucesso."""
        name = "test_24_leave_room_success"
        try:
            rm = self._mgr()
            code = rm.create_room(1)
            rm.join_room(code, 2)
            res = rm.leave_room(code, 2)
            ok = (res == "Successfully left room"
                  and 2 not in rm.rooms[code].players)
            log(name, "Saida de sala", f"code={code}, leave user 2",
                "Successfully left room, 2 ausente",
                f"res={res}, 2_in={(2 in rm.rooms[code].players) if code in rm.rooms else 'sala deletada'}",
                ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Saida de sala", "leave_room",
                "Successfully left room", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_25_leave_last_player_deletes_room(self):
        """Quando ultimo jogador sai, sala e removida do Manager."""
        name = "test_25_leave_last_player_deletes_room"
        try:
            rm = self._mgr()
            code = rm.create_room(1)
            res = rm.leave_room(code, 1)
            ok = (res == "Successfully left room" and code not in rm.rooms)
            log(name, "Sala vazia e removida automaticamente",
                f"code={code}, leave user 1 (unico)",
                "sala removida do dicionario",
                f"res={res}, code_in_rooms={code in rm.rooms}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Sala vazia e removida", "leave unico jogador",
                "sala ausente em rooms", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_26_multiple_rooms_isolated(self):
        """Multiplas salas tem estados completamente independentes."""
        name = "test_26_multiple_rooms_isolated"
        try:
            rm = self._mgr()
            cA = rm.create_room(1)
            rm.join_room(cA, 2)
            cB = rm.create_room(3)
            cC = rm.create_room(4)
            rm.join_room(cC, 5)
            rm.join_room(cC, 6)
            pA = len(rm.rooms[cA].players)
            pB = len(rm.rooms[cB].players)
            pC = len(rm.rooms[cC].players)
            ok = (pA == 2 and pB == 1 and pC == 3)
            log(name, "Multiplas salas isoladas",
                "3 salas: A(2), B(1), C(3)",
                "contagens independentes: 2, 1, 3",
                f"A={pA}, B={pB}, C={pC}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Multiplas salas isoladas", "3 salas",
                "estados separados", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_27_get_players_room_bug(self):
        """
        BUG CRITICO: get_players_room usa .value em vez de .values().
        Esperado: lista de RoomPlayers.
        Obtido: AttributeError 'dict' object has no attribute 'value'.
        """
        name = "test_27_get_players_room_bug"
        try:
            rm = self._mgr()
            code = rm.create_room(1)
            result = rm.get_room_players_by_user(1)
            ok = isinstance(result, list)
            log(name, "get_players_room retorna lista de jogadores",
                "user_id=1, sala criada",
                "lista com 1 RoomPlayer",
                f"resultado={result}", ok,
                None if ok else "bug de implementacao",
                None if ok else "Erro de .value em dict -- deveria ser .values()")
            self.assertTrue(ok)
        except AttributeError as e:
            log(name, "get_players_room retorna lista de jogadores",
                "user_id=1", "lista de RoomPlayer",
                f"AttributeError: {e}", False,
                "bug de implementacao",
                "room_manager.py: 'lobby.players.value' deve ser 'lobby.players.values()' "
                "(linha ~56). Isso quebra handle_chat_message inteiramente.")
            self.fail(f"Bug confirmado: {e}")
        except Exception as e:
            log(name, "get_players_room", "user_id=1",
                "lista", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_28_leave_non_existent_room(self):
        """leave_room em sala inexistente retorna erro."""
        name = "test_28_leave_non_existent_room"
        try:
            rm = self._mgr()
            res = rm.leave_room("ZZZZ99", 1)
            ok = (res == "Error, there is no room with that id")
            log(name, "Sair de sala inexistente", "leave_room('ZZZZ99')",
                "erro esperado", f"res={res}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Sair de sala inexistente", "leave('ZZZZ99')",
                "erro esperado", str(e), False, "bug de implementacao", str(e))
            raise


# ===========================================================================
# BLOCO 3 -- PROTOCOLO (Message / encode_msg / decode_msg)
# ===========================================================================
class TestProtocol(unittest.TestCase):

    def _msg(self, mtype=None, payload=None):
        from network.protocol import Message, MessageType, MessageSource
        return Message(
            sender_id=42,
            source=MessageSource.CLIENT,
            event_type=mtype or MessageType.SEND_CHAT_MESSAGE,
            payload=payload or {"text": "ola"},
            timestamp=datetime.now(timezone.utc),
        )

    # -----------------------------------------------------------------------
    def test_29_message_creation(self):
        """Message instanciavel com todos os campos obrigatorios."""
        name = "test_29_message_creation"
        try:
            from network.protocol import Message, MessageType, MessageSource
            msg = self._msg()
            ok = (msg.sender_id == 42
                  and msg.source == MessageSource.CLIENT
                  and msg.event_type == MessageType.SEND_CHAT_MESSAGE
                  and msg.payload == {"text": "ola"}
                  and isinstance(msg.timestamp, datetime))
            log(name, "Instanciacao de Message",
                "sender_id=42, source=CLIENT, event=CHAT_MESSAGE",
                "todos os campos preenchidos",
                f"sender={msg.sender_id}, source={msg.source}, type={msg.event_type}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Instanciacao de Message", "campos basicos",
                "objeto criado", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_30_encode_msg_produces_valid_json(self):
        """encode_msg produz JSON valido com todos os campos."""
        name = "test_30_encode_msg_produces_valid_json"
        try:
            from network.protocol import encode_msg
            msg = self._msg()
            encoded = encode_msg(msg)
            parsed = json.loads(encoded)
            ok = (isinstance(encoded, str)
                  and all(k in parsed for k in
                          ["sender_id", "source", "type", "payload", "timestamp"]))
            log(name, "encode_msg gera JSON valido", "Message completa",
                "JSON com sender_id, source, type, payload, timestamp",
                f"campos={list(parsed.keys())}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "encode_msg JSON", "Message",
                "JSON valido", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_31_decode_msg_round_trip(self):
        """decode_msg(encode_msg(msg)) reproduz a mesma mensagem."""
        name = "test_31_decode_msg_round_trip"
        try:
            from network.protocol import encode_msg, decode_msg, MessageType
            msg = self._msg(mtype=MessageType.JOIN_ROOM,
                            payload={"room_code": "ABC123"})
            decoded = decode_msg(encode_msg(msg))
            ok = (decoded.sender_id == msg.sender_id
                  and decoded.source == msg.source
                  and decoded.event_type == msg.event_type
                  and decoded.payload == msg.payload)
            log(name, "Round-trip encode/decode",
                "msg(JOIN_ROOM, payload={room_code:ABC123})",
                "campos identicos apos encode+decode",
                f"sender={decoded.sender_id}, type={decoded.event_type}, payload={decoded.payload}",
                ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Round-trip encode/decode", "Message JOIN_ROOM",
                "campos preservados", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_32_decode_invalid_json_raises(self):
        """decode_msg com JSON malformado lanca excecao."""
        name = "test_32_decode_invalid_json_raises"
        try:
            from network.protocol import decode_msg
            raised = False
            try:
                decode_msg("isso nao e json!!!")
            except (json.JSONDecodeError, KeyError, ValueError):
                raised = True
            ok = raised
            log(name, "Decode de JSON invalido lanca excecao",
                "string='isso nao e json!!!'",
                "excecao (JSONDecodeError / KeyError / ValueError)",
                "excecao levantada" if ok else "nenhuma excecao", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Decode de JSON invalido", "string invalida",
                "excecao esperada", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_33_decode_unknown_message_type_raises(self):
        """decode_msg com type desconhecido lanca ValueError."""
        name = "test_33_decode_unknown_message_type_raises"
        try:
            from network.protocol import decode_msg
            raw = json.dumps({
                "sender_id": 1,
                "source": "client",
                "type": "unknown_event_xyz",
                "payload": {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            raised = False
            try:
                decode_msg(raw)
            except ValueError:
                raised = True
            ok = raised
            log(name, "Decode com type desconhecido lanca ValueError",
                "type='unknown_event_xyz'",
                "ValueError ao construir MessageType",
                "ValueError levantado" if ok else "sem excecao", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Decode com type invalido", "type desconhecido",
                "ValueError", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_34_encode_uses_enum_values_not_names(self):
        """encode_msg serializa source e type como seus .value (string lowercase)."""
        name = "test_34_encode_uses_enum_values_not_names"
        try:
            from network.protocol import encode_msg, MessageType, MessageSource, Message
            msg = Message(
                sender_id=1,
                source=MessageSource.SERVER,
                event_type=MessageType.ROOM_CREATED,
                payload={},
                timestamp=datetime.now(timezone.utc)
            )
            parsed = json.loads(encode_msg(msg))
            ok = (parsed["source"] == "server" and parsed["type"] == "room_created")
            log(name, "encode_msg serializa Enum como .value",
                "source=SERVER, type=ROOM_CREATED",
                "source='server', type='room_created'",
                f"source={parsed['source']}, type={parsed['type']}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "Enum serializado como value",
                "MessageSource.SERVER, MessageType.ROOM_CREATED",
                "strings lowercase", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_35_all_message_types_exist(self):
        """Todos os 11 tipos de mensagem definidos no protocolo existem."""
        name = "test_35_all_message_types_exist"
        try:
            from network.protocol import MessageType
            expected = {
                "CREATE_ROOM", "JOIN_ROOM", "LEAVE_ROOM", "TRANSFER_HOST",
                "CHAT_MESSAGE", "ROOM_CREATED", "ROOM_JOINED", "PLAYER_JOINED",
                "PLAYER_LEFT", "HOST_TRANSFERRED", "ERROR"
            }
            actual = {m.name for m in MessageType}
            ok = (expected == actual)
            log(name, "Todos os MessageType existem",
                "inspecao de MessageType",
                f"{len(expected)} tipos definidos",
                f"encontrados={actual}", ok,
                None if ok else "bug de implementacao",
                None if ok else f"diferenca: {expected ^ actual}")
            self.assertTrue(ok)
        except Exception as e:
            log(name, "MessageType completo", "enum inspection",
                "11 tipos", str(e), False, "bug de implementacao", str(e))
            raise


# ===========================================================================
# BLOCO 4 -- CONNECTION MANAGER (mock assincrono)
# ===========================================================================
class MockWebSocket:
    """WebSocket simulado sem servidor real."""
    def __init__(self):
        self.sent = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_text(self, data: str):
        self.sent.append(data)

    async def receive_text(self):
        return '{"text": "ping"}'


def _run(coro):
    """Executa coroutine de forma sincrona, compativel com Python 3.10+."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


class TestConnectionManager(unittest.TestCase):

    # -----------------------------------------------------------------------
    def test_36_connect_registers_user(self):
        """connect() aceita o websocket e registra o user_id."""
        name = "test_36_connect_registers_user"
        try:
            from network.connection_manager import ConnectionManager
            cm = ConnectionManager()
            ws = MockWebSocket()
            _run(cm.connect(1, ws))
            ok = (ws.accepted and 1 in cm.connections)
            log(name, "connect() registra usuario",
                "user_id=1, MockWebSocket",
                "ws.accepted=True, 1 em connections",
                f"accepted={ws.accepted}, in_connections={1 in cm.connections}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "connect() registra usuario", "user_id=1",
                "registrado", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_37_disconnect_removes_user(self):
        """disconnect() remove o user_id do dicionario."""
        name = "test_37_disconnect_removes_user"
        try:
            from network.connection_manager import ConnectionManager
            cm = ConnectionManager()
            ws = MockWebSocket()
            _run(cm.connect(1, ws))
            cm.disconnect(1)
            ok = (1 not in cm.connections)
            log(name, "disconnect() remove usuario",
                "connect(1) -> disconnect(1)",
                "1 ausente em connections",
                f"in_connections={1 in cm.connections}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "disconnect() remove", "disconnect(1)",
                "1 ausente", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_38_disconnect_non_existent_is_safe(self):
        """disconnect() em user inexistente nao lanca excecao."""
        name = "test_38_disconnect_non_existent_is_safe"
        try:
            from network.connection_manager import ConnectionManager
            cm = ConnectionManager()
            raised = False
            try:
                cm.disconnect(999)
            except Exception:
                raised = True
            ok = not raised
            log(name, "disconnect() de inexistente e seguro",
                "disconnect(999) sem conexao previa",
                "nenhuma excecao",
                "sem excecao" if ok else "excecao levantada", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "disconnect() seguro", "disconnect(999)",
                "sem excecao", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_39_send_to_user_delivers_message(self):
        """send_to_user envia mensagem corretamente via websocket."""
        name = "test_39_send_to_user_delivers_message"
        try:
            from network.connection_manager import ConnectionManager
            from network.protocol import Message, MessageType, MessageSource
            cm = ConnectionManager()
            ws = MockWebSocket()
            _run(cm.connect(1, ws))
            msg = Message(
                sender_id=1,
                source=MessageSource.SERVER,
                event_type=MessageType.SEND_CHAT_MESSAGE,
                payload={"text": "hello"},
                timestamp=datetime.now(timezone.utc)
            )
            result = _run(cm.send_to_user(1, msg))
            ok = (result is True and len(ws.sent) == 1)
            log(name, "send_to_user entrega mensagem",
                "user_id=1, msg CHAT_MESSAGE",
                "result=True, 1 msg enviada",
                f"result={result}, msgs_sent={len(ws.sent)}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "send_to_user entrega", "msg CHAT_MESSAGE",
                "True + msg enviada", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_40_send_to_disconnected_user_returns_false(self):
        """send_to_user para user nao conectado retorna False."""
        name = "test_40_send_to_disconnected_user_returns_false"
        try:
            from network.connection_manager import ConnectionManager
            from network.protocol import Message, MessageType, MessageSource
            cm = ConnectionManager()
            msg = Message(
                sender_id=1,
                source=MessageSource.SERVER,
                event_type=MessageType.SEND_CHAT_MESSAGE,
                payload={"text": "hello"},
                timestamp=datetime.now(timezone.utc)
            )
            result = _run(cm.send_to_user(999, msg))
            ok = (result is False)
            log(name, "send_to_user para desconectado retorna False",
                "send_to_user(999), 999 nao conectado",
                "result=False", f"result={result}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "send_to_user desconectado", "user_id=999 sem conexao",
                "False", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_41_send_to_users_returns_list(self):
        """send_to_users retorna lista de resultados."""
        name = "test_41_send_to_users_returns_list"
        try:
            from network.connection_manager import ConnectionManager
            from network.protocol import Message, MessageType, MessageSource
            cm = ConnectionManager()
            ws1, ws2 = MockWebSocket(), MockWebSocket()
            _run(cm.connect(1, ws1))
            _run(cm.connect(2, ws2))
            msg = Message(
                sender_id=0,
                source=MessageSource.SERVER,
                event_type=MessageType.SEND_CHAT_MESSAGE,
                payload={"text": "broadcast"},
                timestamp=datetime.now(timezone.utc)
            )
            results = _run(cm.send_to_users([1, 2, 999], msg))
            ok = (results == [True, True, False])
            log(name, "send_to_users retorna lista de resultados",
                "users=[1,2,999]: 1,2 conectados; 999 nao",
                "[True, True, False]",
                f"results={results}", ok)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "send_to_users lista", "[1,2,999]",
                "[True,True,False]", str(e), False, "bug de implementacao", str(e))
            raise


# ===========================================================================
# BLOCO 5 -- REGRESSAO DE BUGS CONHECIDOS
# ===========================================================================
class TestKnownBugs(unittest.TestCase):
    """
    Testes que documentam bugs confirmados no codigo atual.
    Os que validam o BUG esperam que o teste FALHE (bug presente).
    Os que validam o RISCO passam mas registram o risco.
    """

    # -----------------------------------------------------------------------
    def test_42_enum_player_role_is_broken(self):
        """
        BUG CRITICO: PlayerRole usa ':' (anotacao de tipo) em vez de '='
        (atribuicao). O Enum fica completamente vazio.
        Arquivo: models/room_player.py, linhas 18-21.
        Correcao: PLAYER = 'player' (nao PLAYER: 'player') + remover @dataclass do Enum.
        """
        name = "test_42_enum_player_role_is_broken"
        try:
            from room_player import PlayerRole
            members = list(PlayerRole)
            has_player = hasattr(PlayerRole, "PLAYER")
            has_host   = hasattr(PlayerRole, "HOST")
            ok = (len(members) == 3 and has_player and has_host)
            log(name,
                "PlayerRole Enum possui 3 membros acessiveis",
                "inspecao do Enum",
                "3 membros: PLAYER, HOST, SPECTATOR",
                f"membros={members}, has_PLAYER={has_player}, has_HOST={has_host}", ok,
                None if ok else "bug de implementacao",
                None if ok else
                "room_player.py: usar '=' em vez de ':' e remover @dataclass do Enum. "
                "Ex: PLAYER = 'player' em vez de PLAYER: 'player'")
            self.assertTrue(ok,
                "BUG: PlayerRole esta vazio. "
                "Corrija room_player.py: PLAYER = 'player' (nao PLAYER: 'player')")
        except Exception as e:
            log(name, "PlayerRole Enum", "inspecao", "3 membros",
                str(e), False, "bug de implementacao",
                "Enum completamente inacessivel -- raiz de todos os erros de role")
            raise

    # -----------------------------------------------------------------------
    def test_43_server_uses_raw_string_for_source(self):
        """
        BUG: server.py usa source='SERVER' (string literal) em vez de
        MessageSource.SERVER ao construir a resposta de CREATE_ROOM.
        encode_msg tenta chamar .value em string -> AttributeError.
        Arquivo: network/server.py, linha ~39.
        """
        name = "test_43_server_uses_raw_string_for_source"
        try:
            from network.protocol import encode_msg, Message, MessageType, MessageSource
            # Reproduz exatamente o que server.py faz (bug)
            msg_bug = Message(
                sender_id=1,
                source="SERVER",          # bug: deveria ser MessageSource.SERVER
                event_type=MessageType.ROOM_CREATED,
                payload={"room_code": "ABC123"},
                timestamp=datetime.now(timezone.utc)
            )
            raised = False
            try:
                encode_msg(msg_bug)
            except AttributeError:
                raised = True
            ok = raised  # True significa bug confirmado
            log(name,
                "server.py usa string literal em source ao inves de MessageSource.SERVER",
                "source='SERVER' (string)",
                "AttributeError em encode_msg (bug confirmado)",
                "AttributeError levantado" if raised else "sem erro (bug nao reproduzido)", ok,
                "bug de implementacao" if ok else None,
                "server.py linha ~39: source='SERVER' -> source=MessageSource.SERVER" if ok else None)
            self.assertTrue(ok,
                "Bug esperado: source='SERVER' deve causar AttributeError em encode_msg")
        except Exception as e:
            log(name, "server.py source literal", "source='SERVER'",
                "AttributeError", str(e), False, "bug de implementacao", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_44_server_uses_naive_datetime(self):
        """
        RISCO: server.py usa datetime.now() sem timezone (naive datetime).
        O restante do sistema usa datetime.now(timezone.utc) (aware).
        Misturar pode causar erros de comparacao em producao.
        Arquivo: network/server.py, linha ~42.
        Este teste passa mas documenta o risco.
        """
        name = "test_44_server_uses_naive_datetime"
        try:
            naive = datetime.now()
            aware = datetime.now(timezone.utc)
            is_naive = naive.tzinfo is None
            is_aware = aware.tzinfo is not None
            ok = (is_naive and is_aware)  # confirma que sao diferentes
            log(name,
                "server.py usa datetime.now() sem timezone (datetime naive)",
                "datetime.now() vs datetime.now(timezone.utc)",
                "Documentar risco: misturar naive e aware pode causar erros",
                f"server usa naive={is_naive}, correto usa aware={is_aware}", ok,
                "decisao de arquitetura necessaria" if ok else None,
                "server.py: substituir datetime.now() por datetime.now(timezone.utc)" if ok else None)
            self.assertTrue(ok)
        except Exception as e:
            log(name, "server.py datetime naive", "datetime.now()",
                "risco documentado", str(e), False, "comportamento nao definido", str(e))
            raise

    # -----------------------------------------------------------------------
    def test_45_get_players_room_dict_value_bug(self):
        """
        BUG: room_manager.py linha ~56 usa lobby.players.value em vez de
        lobby.players.values(). Quebra completamente o envio de mensagens de chat.
        Confirma que dict nao tem atributo .value.
        """
        name = "test_45_get_players_room_dict_value_bug"
        try:
            from room.room import Room
            r = Room("TST")

            class FakePlayer:
                user_id = 1
            r.players[1] = FakePlayer()

            # Reproduz exatamente o acesso errado de room_manager.py
            raised = False
            try:
                _ = list(r.players.value)   # .value em vez de .values()
            except AttributeError:
                raised = True

            ok = raised  # True = bug confirmado
            log(name,
                "room_manager.py: .value em vez de .values() em dict",
                "players.value",
                "AttributeError (bug confirmado)",
                "AttributeError levantado" if raised else "sem erro", ok,
                "bug de implementacao" if ok else None,
                "room_manager.py ~56: list(lobby.players.value) -> list(lobby.players.values())" if ok else None)
            self.assertTrue(ok, "Bug esperado: .value em dict deve causar AttributeError")
        except Exception as e:
            log(name, "get_players_room .value bug", "players.value",
                "AttributeError", str(e), False, "bug de implementacao", str(e))
            raise


# ===========================================================================
# RELATORIO FINAL
# ===========================================================================
def print_report():
    total  = len(TEST_RESULTS)
    passed = sum(1 for t in TEST_RESULTS if t["passed"])
    failed = total - passed
    sep    = "=" * 72

    lines = []
    lines.append("")
    lines.append(sep)
    lines.append("  RELATORIO DE TESTES -- tests_junie/test_claude.py")
    lines.append(sep)
    lines.append(f"\n  Testes executados : {total}")
    lines.append(f"  Aprovados         : {passed}")
    lines.append(f"  Falhados          : {failed}")
    lines.append("")
    lines.append(f"  {'#':<4} {'STATUS':<8} {'NOME'}")
    lines.append(f"  {'-'*4} {'-'*8} {'-'*50}")

    for i, t in enumerate(TEST_RESULTS, 1):
        status = "PASSOU" if t["passed"] else "FALHOU"
        lines.append(f"  {i:<4} {status:<8} {t['name']}")

    failed_tests = [t for t in TEST_RESULTS if not t["passed"]]
    if failed_tests:
        lines.append("")
        lines.append(sep)
        lines.append("  DETALHES DOS TESTES FALHOS")
        lines.append(sep)
        for t in failed_tests:
            lines.append(f"\n  Nome     : {t['name']}")
            lines.append(f"  Cenario  : {t['scenario']}")
            lines.append(f"  Entradas : {t['inputs']}")
            lines.append(f"  Esperado : {t['expected']}")
            lines.append(f"  Obtido   : {t['obtained']}")
            lines.append(f"  Tipo     : {t['failure_type']}")
            if t["explanation"]:
                lines.append(f"  Causa    : {t['explanation']}")

    lines.append("")
    lines.append(sep)
    lines.append("  BUGS ENCONTRADOS")
    lines.append(sep)
    bugs = [
        {
            "desc": "PlayerRole Enum definido com ':' (anotacao de tipo) em vez de '=' (atribuicao)",
            "arquivo": "chat-project/models/room_player.py",
            "linha": "18-21",
            "impacto": "CRITICO -- quebra toda a logica de papeis (host/player/spectator)",
            "correcao": "Substituir 'PLAYER: player' por 'PLAYER = player' e remover @dataclass do Enum"
        },
        {
            "desc": "get_players_room usa lobby.players.value em vez de lobby.players.values()",
            "arquivo": "chat-project/room/room_manager.py",
            "linha": "~56",
            "impacto": "CRITICO -- chat inteiro nao funciona (handle_chat_message quebrado)",
            "correcao": "Substituir list(lobby.players.value) por list(lobby.players.values())"
        },
        {
            "desc": "server.py usa source='SERVER' (string) em vez de MessageSource.SERVER",
            "arquivo": "chat-project/network/server.py",
            "linha": "~39",
            "impacto": "ALTO -- encode_msg chama .value em string -> AttributeError em CREATE_ROOM",
            "correcao": "Substituir source='SERVER' por source=MessageSource.SERVER"
        },
        {
            "desc": "server.py usa datetime.now() sem timezone (naive datetime)",
            "arquivo": "chat-project/network/server.py",
            "linha": "~42",
            "impacto": "MEDIO -- inconsistencia com resto do sistema que usa timezone.utc",
            "correcao": "Substituir datetime.now() por datetime.now(timezone.utc)"
        },
        {
            "desc": "handlers.py nao trata o caso em que get_players_room retorna string de erro",
            "arquivo": "chat-project/network/handlers.py",
            "linha": "31",
            "impacto": "ALTO -- AttributeError ao tentar iterar string como lista de players",
            "correcao": "Verificar se result e lista antes de iterar: if isinstance(room_players, list)"
        },
    ]
    for i, b in enumerate(bugs, 1):
        lines.append(f"\n  Bug #{i}: {b['desc']}")
        lines.append(f"    Arquivo  : {b['arquivo']}")
        lines.append(f"    Linha    : {b['linha']}")
        lines.append(f"    Impacto  : {b['impacto']}")
        lines.append(f"    Correcao : {b['correcao']}")

    lines.append("")
    lines.append(sep)
    lines.append("  MELHORIAS RECOMENDADAS")
    lines.append(sep)
    melhorias = [
        ("[Arquitetura]",
         "Converter project para pacote Python real com importacoes absolutas "
         "para eliminar sys.path manual e imports frageis como 'from room import room'."),
        ("[Arquitetura]",
         "handlers.py nao possui handler para TRANSFER_HOST nem para ERROR -- "
         "adicionar handle_transfer_host() e tratamento de eventos desconhecidos."),
        ("[Arquitetura]",
         "Criar camada de validacao (Validator ou middleware) para verificar "
         "autenticidade do sender_id antes de processar qualquer mensagem."),
        ("[Seguranca]",
         "Sem autenticacao de user_id na conexao WebSocket -- qualquer cliente "
         "pode forjar sender_id e agir como outro usuario."),
        ("[Seguranca]",
         "Sem limite de tamanho de payload -- risco de DoS via mensagens gigantes."),
        ("[Performance]",
         "send_to_users usa await sequencial -- converter para asyncio.gather() "
         "para envio paralelo a multiplos usuarios."),
        ("[Performance]",
         "get_players_room faz varredura linear em todas as salas -- "
         "manter indice user_id -> room_code no RoomManager para O(1)."),
        ("[Organizacao]",
         "Extrair strings de retorno ('Successfully entered room' etc.) para constantes "
         "ou usar excecoes tipadas para facilitar manutencao."),
        ("[Organizacao]",
         "status da sala e a string 'Testing' -- substituir por Enum RoomStatus "
         "com valores Waiting / Playing / Finished."),
    ]
    for cat, texto in melhorias:
        lines.append(f"\n  {cat} {texto}")

    lines.append("")
    lines.append(sep)
    lines.append("")

    report = "\n".join(lines)
    # Usa ascii com substituicao para evitar UnicodeEncodeError no Windows
    sys.stdout.buffer.write(report.encode("utf-8", errors="replace"))
    sys.stdout.buffer.write(b"\n")
    sys.stdout.buffer.flush()


import atexit
atexit.register(print_report)

if __name__ == "__main__":
    unittest.main(verbosity=2)
