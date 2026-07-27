from fastapi import FastAPI, WebSocket
from network.server import Server


server = Server()
test_id = 1

app = FastAPI(
    title="Realtime Chat Engine",
    version="0.1.0-alpha"
)

@app.get("/")
def root():
    return {"status": "ok"}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await server.handle_connection(user_id, websocket)