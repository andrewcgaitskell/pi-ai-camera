from quart import Quart, websocket, render_template
import threading
import time
from picamera2 import Picamera2, Preview
import cv2
import asyncio
from datetime import datetime
import os
import logging

# Create a Quart app instance
app = Quart(__name__)

# Global variables
video_frame = None
use_roi = False  # Switch for ROI or full frame
lock = threading.Lock()
photo_dir = "/home/scanpi/photos"
os.makedirs(photo_dir, exist_ok=True)

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (1280, 960)}))  # Doubled resolution
picam2.start()

# Function to crop a region of interest (ROI)
def crop_roi(frame, x, y, width, height):
    return frame[y:y+height, x:x+width]

# Function to capture video frames
def video_stream():
    global video_frame, use_roi
    while True:
        frame = picam2.capture_array()
        if use_roi:
            # Define ROI (e.g., center 640x480 region)
            center_x, center_y = frame.shape[1] // 2, frame.shape[0] // 2
            roi_width, roi_height = 640, 480
            x_start = center_x - roi_width // 2
            y_start = center_y - roi_height // 2
            frame = crop_roi(frame, x_start, y_start, roi_width, roi_height)
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

@app.route("/toggle_roi", methods=["POST"])
async def toggle_roi():
    global use_roi
    use_roi = not use_roi
    logging.info(f"ROI mode set to: {use_roi}")
    return "", 204

@app.route("/capture", methods=["POST"])
async def capture():
    # Use a thread-safe mechanism to avoid locking issues
    def safe_capture():
        with lock:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            photo_path = os.path.join(photo_dir, f"photo_{timestamp}.jpg")
            capture_config = picam2.create_still_configuration(main={"size": (4056, 3040)})  # Full 12MP resolution
            array = picam2.switch_mode_and_capture_array(capture_config, "main")
            cv2.imwrite(photo_path, array)
            logging.info(f"Photo saved: {photo_path}")

    await asyncio.to_thread(safe_capture)
    return "", 204

@app.route("/")
async def index():
    return await render_template("index_roi.html")

if __name__ == "__main__":
    # Start the video stream thread
    video_thread = threading.Thread(target=video_stream, daemon=True)
    video_thread.start()

    # Run the Quart app
    app.run(host="0.0.0.0", port=5000)
