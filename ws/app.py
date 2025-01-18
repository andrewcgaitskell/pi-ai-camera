from quart import Quart, render_template, websocket
from asyncio import create_task

app = Quart(__name__)

# Store connected WebSocket clients
connected_clients = set()

@app.route('/')
async def index():
    return await render_template('message.html')

@app.websocket('/ws')
async def ws():
    # Add the client to the set of connected clients
    connected_clients.add(websocket._get_current_object())
    try:
        while True:
            # Receive a message from the client
            message = await websocket.receive()
            
            # Broadcast the message to all connected clients
            for client in connected_clients:
                if client != websocket._get_current_object():
                    await client.send(message)
    finally:
        # Remove the client when the connection is closed
        connected_clients.remove(websocket._get_current_object())

if __name__ == '__main__':
    # Run the Quart app
    app.run(host='0.0.0.0', port=5000, debug=True)
