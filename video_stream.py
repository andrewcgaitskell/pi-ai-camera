from quart import Quart, websocket
import asyncio
import socket
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

app = Quart(__name__)
picam2 = Picamera2()
video_config = picam2.create_video_configuration({"size": (1280, 720)})
picam2.configure(video_config)
encoder = H264Encoder(1000000)

async def stream_video():
    """Streams video data to connected WebSocket clients."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", 10001))
            sock.listen()

            conn, addr = sock.accept()
            stream = conn.makefile("wb")
            encoder.output = FileOutput(stream)

            picam2.encoders = encoder
            picam2.start_encoder(encoder)
            picam2.start()
            
            while True:
                await asyncio.sleep(0.1)  # Simulate asynchronous handling

    except Exception as e:
        print(f"Error in video streaming: {e}")

    finally:
        picam2.stop()
        picam2.stop_encoder()
        conn.close()

@app.websocket('/video')
async def video_feed():
    """Handles WebSocket connection for video feed."""
    print("WebSocket connection established.")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(("localhost", 10001))
            with sock.makefile("rb") as stream:
                while True:
                    data = stream.read(1024)
                    if not data:
                        break
                    await websocket.send(data)
    except Exception as e:
        print(f"Error in WebSocket feed: {e}")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
