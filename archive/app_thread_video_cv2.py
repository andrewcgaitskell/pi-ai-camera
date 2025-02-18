from quart import Quart, websocket, render_template, jsonify
import threading
import time
import asyncio
import cv2
from datetime import datetime
import os

# Create a Quart app instance
app = Quart(__name__)

# Global variables
video_frame = None
lock = threading.Lock()
photo_dir = "/home/scanpi/photos"
os.makedirs(photo_dir, exist_ok=True)

# Function to capture video frames
def video_stream():
    global video_frame
    cap = cv2.VideoCapture(0)  # Use the default camera
    while True:
        ret, frame = cap.read()
        if ret:
            _, buffer = cv2.imencode('.jpg', frame)
            video_frame = buffer.tobytes()
        time.sleep(0.03)  # Approx. 30 FPS

@app.websocket("/ws")
async def ws():
    global video_frame
    latest_photo = None
    while True:
        if os.path.exists(photo_dir):
            photos = sorted(os.listdir(photo_dir))
            latest_photo = os.path.join(photo_dir, photos[-1]) if photos else None
        await websocket.send_json({"latest_photo": latest_photo})
        await asyncio.sleep(1)

@app.route("/")
async def index():
    return await render_template("thread_video_index.html")

@app.route("/video_feed")
async def video_feed():
    global video_frame
    if video_frame is None:
        return "", 204
    return await jsonify({"frame": video_frame})

@app.route("/capture", methods=["POST"])
async def capture():
    global video_frame, lock
    # Use a thread-safe mechanism to avoid locking issues
    def safe_capture():
        with lock:
            if video_frame:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                photo_name = os.path.join(photo_dir, f"photo_{timestamp}.jpg")
                with open(photo_name, "wb") as f:
                    f.write(video_frame)

    await asyncio.to_thread(safe_capture)
    return "", 204

if __name__ == "__main__":
    # Start the video stream thread
    video_thread = threading.Thread(target=video_stream, daemon=True)
    video_thread.start()

    # Run the Quart app
    app.run(host="0.0.0.0", port=5000)
