from quart import Quart, websocket, render_template
import threading
import time
from picamera2 import Picamera2, Preview
import cv2

# Create a Quart app instance
app = Quart(__name__)

# Global variable
video_frame = None

# Initialize Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.start()

# Function to capture video frames
def video_stream():
    global video_frame
    while True:
        frame = picam2.capture_array()
        _, buffer = cv2.imencode('.jpg', frame)
        video_frame = buffer.tobytes()
        time.sleep(0.03)  # Approx. 30 FPS

@app.websocket("/ws")
async def ws():
    global video_frame
    while True:
        if video_frame:
            await websocket.send(video_frame)
        await asyncio.sleep(0.03)

@app.route("/")
async def index():
    return await render_template("threaded_simple_video_index.html")

if __name__ == "__main__":
    # Start the video stream thread
    video_thread = threading.Thread(target=video_stream, daemon=True)
    video_thread.start()

    # Run the Quart app
    app.run(host="0.0.0.0", port=5000)
