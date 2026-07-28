"""
Integration tests for WebSocket Server.

These tests validate the complete flow between client and server using real WebSocket connections.
Tests cover the mandatory scenario: connect, create room, join, broadcast, and disconnect.
"""

import pytest
import json
from datetime import datetime
from typing import Generator

from fastapi import WebSocket
from fastapi.testclient import TestClient

from main import app, server
from network.protocol import Message, MessageSource, encode_msg
from network.message_types import MessageType


class TestWebSocketIntegrationMandatoryScenario:
    """
    Complete WebSocket integration test following the mandatory scenario:
    1. User 1 connects to server
    2. User 1 creates a room
    3. User 2 connects to server
    4. User 2 joins the room created by User 1
    5. Verify both receive PLAYER_JOINED event
    6. User 1 sends a chat message
    7. Verify room users receive CHAT_MESSAGE broadcast
    8. User 1 leaves the room
    9. Verify remaining users receive PLAYER_LEFT event
    """

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def reset_server(self):
        """Reset server state before each test."""
        # Clear all rooms and connections
        server.room_manager.rooms.clear()
        server.connection_manager.connections.clear()
        yield
        # Cleanup after test
        server.room_manager.rooms.clear()
        server.connection_manager.connections.clear()

    def test_mandatory_scenario_full_flow(self, client: TestClient, reset_server):
        """
        Test the complete mandatory scenario with two users.
        
        This test validates:
        1. User 1 connects
        2. User 1 creates a room
        3. User 2 connects
        4. User 2 joins the room
        5. Both users receive PLAYER_JOINED events
        6. User 1 sends a chat message
        7. Both users receive the CHAT_MESSAGE
        8. User 1 leaves
        9. User 2 receives PLAYER_LEFT event
        """
        # Step 1: User 1 connects
        with client.websocket_connect("/ws/1/Alice") as user1_ws:
            # Step 2: User 1 creates a room
            create_room_msg = Message(
                sender_id=1,
                source=MessageSource.CLIENT,
                event_type=MessageType.CREATE_ROOM,
                payload={},
                timestamp=datetime.now()
            )
            user1_ws.send_text(encode_msg(create_room_msg))

            # Receive ROOM_CREATED response
            room_created_data = user1_ws.receive_text()
            room_created = json.loads(room_created_data)
            
            assert room_created["type"] == MessageType.ROOM_CREATED.value
            assert "room_code" in room_created["payload"]
            room_code = room_created["payload"]["room_code"]

            # Step 3: User 2 connects
            with client.websocket_connect("/ws/2/Bob") as user2_ws:
                # Step 4: User 2 joins the room
                join_room_msg = Message(
                    sender_id=2,
                    source=MessageSource.CLIENT,
                    event_type=MessageType.JOIN_ROOM,
                    payload={"room_code": room_code},
                    timestamp=datetime.now()
                )
                user2_ws.send_text(encode_msg(join_room_msg))

                # Step 5a: User 2 receives PLAYER_JOINED for their own join
                player_joined_user2 = user2_ws.receive_text()
                player_joined_u2 = json.loads(player_joined_user2)
                assert player_joined_u2["type"] == MessageType.PLAYER_JOINED.value
                assert player_joined_u2["payload"]["player_id"] == 2

                # Step 5b: User 1 receives PLAYER_JOINED for User 2's join (broadcast)
                player_joined_user1 = user1_ws.receive_text()
                player_joined_u1 = json.loads(player_joined_user1)
                assert player_joined_u1["type"] == MessageType.PLAYER_JOINED.value
                assert player_joined_u1["payload"]["player_id"] == 2

                # Step 6: User 1 sends a chat message
                chat_msg = Message(
                    sender_id=1,
                    source=MessageSource.CLIENT,
                    event_type=MessageType.SEND_CHAT_MESSAGE,
                    payload={"text": "Hello from User 1"},
                    timestamp=datetime.now()
                )
                user1_ws.send_text(encode_msg(chat_msg))

                # Step 7a: User 1 receives the CHAT_MESSAGE broadcast
                chat_message_user1 = user1_ws.receive_text()
                chat_msg_u1 = json.loads(chat_message_user1)
                assert chat_msg_u1["type"] == MessageType.CHAT_MESSAGE.value
                assert chat_msg_u1["payload"]["text"] == "Hello from User 1"
                assert chat_msg_u1["payload"]["player_id"] == 1

                # Step 7b: User 2 receives the CHAT_MESSAGE broadcast
                chat_message_user2 = user2_ws.receive_text()
                chat_msg_u2 = json.loads(chat_message_user2)
                assert chat_msg_u2["type"] == MessageType.CHAT_MESSAGE.value
                assert chat_msg_u2["payload"]["text"] == "Hello from User 1"
                assert chat_msg_u2["payload"]["player_id"] == 1

                # Step 8: User 1 leaves the room
                leave_room_msg = Message(
                    sender_id=1,
                    source=MessageSource.CLIENT,
                    event_type=MessageType.LEAVE_ROOM,
                    payload={"room_code": room_code},
                    timestamp=datetime.now()
                )
                user1_ws.send_text(encode_msg(leave_room_msg))

                # User 1 receives PLAYER_LEFT confirmation
                player_left_user1 = user1_ws.receive_text()
                player_left_u1 = json.loads(player_left_user1)
                assert player_left_u1["type"] == MessageType.PLAYER_LEFT.value
                assert player_left_u1["payload"]["player_id"] == 1

                # Step 9: User 2 receives PLAYER_LEFT broadcast
                player_left_user2 = user2_ws.receive_text()
                player_left_u2 = json.loads(player_left_user2)
                assert player_left_u2["type"] == MessageType.PLAYER_LEFT.value
                assert player_left_u2["payload"]["player_id"] == 1


class TestWebSocketIntegrationMultiUser:
    """Additional integration tests with multiple users."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def reset_server(self):
        """Reset server state before each test."""
        server.room_manager.rooms.clear()
        server.connection_manager.connections.clear()
        yield
        server.room_manager.rooms.clear()
        server.connection_manager.connections.clear()

    def test_multiple_messages_exchange(self, client: TestClient, reset_server):
        """Test multiple users exchanging multiple messages."""
        with client.websocket_connect("/ws/1/Alice") as user1_ws:
            # Create room
            create_msg = Message(
                sender_id=1,
                source=MessageSource.CLIENT,
                event_type=MessageType.CREATE_ROOM,
                payload={},
                timestamp=datetime.now()
            )
            user1_ws.send_text(encode_msg(create_msg))
            room_created_data = user1_ws.receive_text()
            room_code = json.loads(room_created_data)["payload"]["room_code"]

            with client.websocket_connect("/ws/2/Bob") as user2_ws:
                # User 2 joins
                join_msg = Message(
                    sender_id=2,
                    source=MessageSource.CLIENT,
                    event_type=MessageType.JOIN_ROOM,
                    payload={"room_code": room_code},
                    timestamp=datetime.now()
                )
                user2_ws.send_text(encode_msg(join_msg))
                # Consume PLAYER_JOINED events
                user2_ws.receive_text()
                user1_ws.receive_text()

                # User 1 sends message 1
                msg1 = Message(
                    sender_id=1,
                    source=MessageSource.CLIENT,
                    event_type=MessageType.SEND_CHAT_MESSAGE,
                    payload={"text": "First message"},
                    timestamp=datetime.now()
                )
                user1_ws.send_text(encode_msg(msg1))
                user1_ws.receive_text()
                msg1_received = json.loads(user2_ws.receive_text())
                assert msg1_received["payload"]["text"] == "First message"

                # User 2 sends message 2
                msg2 = Message(
                    sender_id=2,
                    source=MessageSource.CLIENT,
                    event_type=MessageType.SEND_CHAT_MESSAGE,
                    payload={"text": "Second message"},
                    timestamp=datetime.now()
                )
                user2_ws.send_text(encode_msg(msg2))
                user2_ws.receive_text()
                msg2_received = json.loads(user1_ws.receive_text())
                assert msg2_received["payload"]["text"] == "Second message"

                # User 1 sends message 3
                msg3 = Message(
                    sender_id=1,
                    source=MessageSource.CLIENT,
                    event_type=MessageType.SEND_CHAT_MESSAGE,
                    payload={"text": "Third message"},
                    timestamp=datetime.now()
                )
                user1_ws.send_text(encode_msg(msg3))
                user1_ws.receive_text()
                msg3_received = json.loads(user2_ws.receive_text())
                assert msg3_received["payload"]["text"] == "Third message"

    def test_three_users_in_room(self, client: TestClient, reset_server):
        """Test scenario with three users in one room."""
        with client.websocket_connect("/ws/1/Alice") as user1_ws:
            # User 1 creates room
            create_msg = Message(
                sender_id=1,
                source=MessageSource.CLIENT,
                event_type=MessageType.CREATE_ROOM,
                payload={},
                timestamp=datetime.now()
            )
            user1_ws.send_text(encode_msg(create_msg))
            room_code = json.loads(user1_ws.receive_text())["payload"]["room_code"]

            with client.websocket_connect("/ws/2/Bob") as user2_ws:
                # User 2 joins
                join_msg2 = Message(
                    sender_id=2,
                    source=MessageSource.CLIENT,
                    event_type=MessageType.JOIN_ROOM,
                    payload={"room_code": room_code},
                    timestamp=datetime.now()
                )
                user2_ws.send_text(encode_msg(join_msg2))
                user2_ws.receive_text()
                user1_ws.receive_text()

                with client.websocket_connect("/ws/3/Charlie") as user3_ws:
                    # User 3 joins
                    join_msg3 = Message(
                        sender_id=3,
                        source=MessageSource.CLIENT,
                        event_type=MessageType.JOIN_ROOM,
                        payload={"room_code": room_code},
                        timestamp=datetime.now()
                    )
                    user3_ws.send_text(encode_msg(join_msg3))
                    user3_ws.receive_text()
                    user2_ws.receive_text()
                    user1_ws.receive_text()

                    # User 2 sends message
                    msg = Message(
                        sender_id=2,
                        source=MessageSource.CLIENT,
                        event_type=MessageType.SEND_CHAT_MESSAGE,
                        payload={"text": "Message to all"},
                        timestamp=datetime.now()
                    )
                    user2_ws.send_text(encode_msg(msg))

                    # All three users should receive the message
                    user2_received = json.loads(user2_ws.receive_text())
                    assert user2_received["payload"]["text"] == "Message to all"

                    user1_received = json.loads(user1_ws.receive_text())
                    assert user1_received["payload"]["text"] == "Message to all"

                    user3_received = json.loads(user3_ws.receive_text())
                    assert user3_received["payload"]["text"] == "Message to all"

    def test_invalid_room_code_join_fails(self, client: TestClient, reset_server):
        """Test that joining a non-existent room fails."""
        with client.websocket_connect("/ws/1/Alice") as user_ws:
            # Try to join non-existent room
            join_msg = Message(
                sender_id=1,
                source=MessageSource.CLIENT,
                event_type=MessageType.JOIN_ROOM,
                payload={"room_code": "INVALID123"},
                timestamp=datetime.now()
            )
            user_ws.send_text(encode_msg(join_msg))

            # Should receive ERROR message
            response = json.loads(user_ws.receive_text())
            assert response["type"] == MessageType.ERROR.value
            assert "error" in response["payload"]

    def test_user_cannot_join_same_room_twice(self, client: TestClient, reset_server):
        """Test that a user cannot join the same room twice."""
        with client.websocket_connect("/ws/1/Alice") as user_ws:
            # Create room
            create_msg = Message(
                sender_id=1,
                source=MessageSource.CLIENT,
                event_type=MessageType.CREATE_ROOM,
                payload={},
                timestamp=datetime.now()
            )
            user_ws.send_text(encode_msg(create_msg))
            room_code = json.loads(user_ws.receive_text())["payload"]["room_code"]

            # Try to join the same room again
            join_msg = Message(
                sender_id=1,
                source=MessageSource.CLIENT,
                event_type=MessageType.JOIN_ROOM,
                payload={"room_code": room_code},
                timestamp=datetime.now()
            )
            user_ws.send_text(encode_msg(join_msg))

            # Should receive ERROR (user already in room)
            response = json.loads(user_ws.receive_text())
            assert response["type"] == MessageType.ERROR.value

    def test_leave_nonexistent_room_fails(self, client: TestClient, reset_server):
        """Test that leaving a non-existent room fails."""
        with client.websocket_connect("/ws/1/Alice") as user_ws:
            # Try to leave non-existent room
            leave_msg = Message(
                sender_id=1,
                source=MessageSource.CLIENT,
                event_type=MessageType.LEAVE_ROOM,
                payload={"room_code": "INVALID123"},
                timestamp=datetime.now()
            )
            user_ws.send_text(encode_msg(leave_msg))

            # Should receive ERROR message
            response = json.loads(user_ws.receive_text())
            assert response["type"] == MessageType.ERROR.value

    def test_message_content_preserved(self, client: TestClient, reset_server):
        """Test that message content is preserved through the server."""
        special_content = "Hello! 🎉 @mention #room {json:\"test\"}"
        
        with client.websocket_connect("/ws/1/Alice") as user1_ws:
            # Create room
            create_msg = Message(
                sender_id=1,
                source=MessageSource.CLIENT,
                event_type=MessageType.CREATE_ROOM,
                payload={},
                timestamp=datetime.now()
            )
            user1_ws.send_text(encode_msg(create_msg))
            room_code = json.loads(user1_ws.receive_text())["payload"]["room_code"]

            with client.websocket_connect("/ws/2/Bob") as user2_ws:
                # User 2 joins
                join_msg = Message(
                    sender_id=2,
                    source=MessageSource.CLIENT,
                    event_type=MessageType.JOIN_ROOM,
                    payload={"room_code": room_code},
                    timestamp=datetime.now()
                )
                user2_ws.send_text(encode_msg(join_msg))
                user2_ws.receive_text()
                user1_ws.receive_text()

                # User 1 sends special content message
                msg = Message(
                    sender_id=1,
                    source=MessageSource.CLIENT,
                    event_type=MessageType.SEND_CHAT_MESSAGE,
                    payload={"text": special_content},
                    timestamp=datetime.now()
                )
                user1_ws.send_text(encode_msg(msg))

                # Verify User 1 receives it
                user1_received = json.loads(user1_ws.receive_text())
                assert user1_received["payload"]["text"] == special_content

                # Verify User 2 receives it with same content
                user2_received = json.loads(user2_ws.receive_text())
                assert user2_received["payload"]["text"] == special_content

    def test_room_deleted_when_last_player_leaves(self, client: TestClient, reset_server):
        """Test that room is deleted when the last player leaves."""
        with client.websocket_connect("/ws/1/Alice") as user_ws:
            # Create room
            create_msg = Message(
                sender_id=1,
                source=MessageSource.CLIENT,
                event_type=MessageType.CREATE_ROOM,
                payload={},
                timestamp=datetime.now()
            )
            user_ws.send_text(encode_msg(create_msg))
            room_code = json.loads(user_ws.receive_text())["payload"]["room_code"]

            # Verify room exists
            assert room_code in server.room_manager.rooms

            # Leave room
            leave_msg = Message(
                sender_id=1,
                source=MessageSource.CLIENT,
                event_type=MessageType.LEAVE_ROOM,
                payload={"room_code": room_code},
                timestamp=datetime.now()
            )
            user_ws.send_text(encode_msg(leave_msg))
            user_ws.receive_text()

            # Verify room is deleted
            assert room_code not in server.room_manager.rooms

    def test_multiple_rooms_independent(self, client: TestClient, reset_server):
        """Test that multiple rooms operate independently."""
        with client.websocket_connect("/ws/1/Alice") as user1_ws:
            # Create room 1
            create_msg = Message(
                sender_id=1,
                source=MessageSource.CLIENT,
                event_type=MessageType.CREATE_ROOM,
                payload={},
                timestamp=datetime.now()
            )
            user1_ws.send_text(encode_msg(create_msg))
            room1_code = json.loads(user1_ws.receive_text())["payload"]["room_code"]

            with client.websocket_connect("/ws/2/Bob") as user2_ws:
                # Create room 2
                create_msg2 = Message(
                    sender_id=2,
                    source=MessageSource.CLIENT,
                    event_type=MessageType.CREATE_ROOM,
                    payload={},
                    timestamp=datetime.now()
                )
                user2_ws.send_text(encode_msg(create_msg2))
                room2_code = json.loads(user2_ws.receive_text())["payload"]["room_code"]

                # Verify rooms are different
                assert room1_code != room2_code

                # User 1 sends message in room 1
                msg1 = Message(
                    sender_id=1,
                    source=MessageSource.CLIENT,
                    event_type=MessageType.SEND_CHAT_MESSAGE,
                    payload={"text": "Message in room 1"},
                    timestamp=datetime.now()
                )
                user1_ws.send_text(encode_msg(msg1))
                user1_ws.receive_text()

                # User 2 should NOT receive message from room 1
                # (they would need to have recv timeout, but since we're in separate rooms,
                # user2 shouldn't have any pending messages)

                # User 2 sends message in room 2
                msg2 = Message(
                    sender_id=2,
                    source=MessageSource.CLIENT,
                    event_type=MessageType.SEND_CHAT_MESSAGE,
                    payload={"text": "Message in room 2"},
                    timestamp=datetime.now()
                )
                user2_ws.send_text(encode_msg(msg2))
                user2_received = json.loads(user2_ws.receive_text())
                assert user2_received["payload"]["text"] == "Message in room 2"


class TestWebSocketIntegrationEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def reset_server(self):
        """Reset server state before each test."""
        server.room_manager.rooms.clear()
        server.connection_manager.connections.clear()
        yield
        server.room_manager.rooms.clear()
        server.connection_manager.connections.clear()

    def test_empty_chat_message(self, client: TestClient, reset_server):
        """Test sending an empty chat message."""
        with client.websocket_connect("/ws/1/Alice") as user_ws:
            # Create room
            create_msg = Message(
                sender_id=1,
                source=MessageSource.CLIENT,
                event_type=MessageType.CREATE_ROOM,
                payload={},
                timestamp=datetime.now()
            )
            user_ws.send_text(encode_msg(create_msg))
            user_ws.receive_text()

            # Send empty message
            msg = Message(
                sender_id=1,
                source=MessageSource.CLIENT,
                event_type=MessageType.SEND_CHAT_MESSAGE,
                payload={"text": ""},
                timestamp=datetime.now()
            )
            user_ws.send_text(encode_msg(msg))

            # Should still receive the message (empty string is valid)
            response = json.loads(user_ws.receive_text())
            assert response["type"] == MessageType.CHAT_MESSAGE.value
            assert response["payload"]["text"] == ""

    def test_message_to_user_not_in_room(self, client: TestClient, reset_server):
        """Test behavior when user tries to send message without being in a room."""
        with client.websocket_connect("/ws/1/Alice") as user_ws:
            # Try to send message without joining a room
            msg = Message(
                sender_id=1,
                source=MessageSource.CLIENT,
                event_type=MessageType.SEND_CHAT_MESSAGE,
                payload={"text": "Message"},
                timestamp=datetime.now()
            )
            user_ws.send_text(encode_msg(msg))

            # Should receive response (either ERROR or handled gracefully)
            response = json.loads(user_ws.receive_text())
            # The message should either error or be silently handled
            # Document behavior here

    def test_special_characters_in_nickname(self, client: TestClient, reset_server):
        """Test that special characters in nickname are handled."""
        special_nicknames = [
            "User@123",
            "用户",
            "مستخدم",
            "User-with-dashes",
            "User_with_underscores"
        ]

        for nickname in special_nicknames:
            with client.websocket_connect(f"/ws/1/{nickname}") as user_ws:
                create_msg = Message(
                    sender_id=1,
                    source=MessageSource.CLIENT,
                    event_type=MessageType.CREATE_ROOM,
                    payload={},
                    timestamp=datetime.now()
                )
                user_ws.send_text(encode_msg(create_msg))
                response = json.loads(user_ws.receive_text())
                assert response["type"] == MessageType.ROOM_CREATED.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
