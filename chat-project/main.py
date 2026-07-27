import uvicorn
from fastapi import FastAPI, WebSocket

from network.server import Server


app = FastAPI()
server = Server()


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await server.handle_connection(user_id, websocket)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )