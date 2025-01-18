from quart import Quart, render_template, jsonify, websocket
from picamera2 import Picamera2
import cv2
import base64
import os
from time import strftime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("picamera2").setLevel(logging.WARNING)

app = Quart(__name__)
camera = Picamera2()
executor = ThreadPoolExecutor()
camera_lock = asyncio.Lock()

# Camera configurations
photo_config = camera.create_still_configuration({"size": (4056, 3040)})
video_config = camera.create_video_configuration({"size": (640, 480)})

@app.route('/')
async def index():
    """Render the homepage."""
    logging.info("Rendering index page.")
    return await render_template('index_video.html')  # Adjust HTML to include video preview and capture button

@app.websocket('/video_feed')
async def video_feed():
    """WebSocket endpoint to stream video frames."""
    async with camera_lock:
        try:
            logging.info("Starting video feed.")
            camera.stop()
            await asyncio.get_event_loop().run_in_executor(executor, camera.configure, video_config)
            camera.start()
            logging.debug("Camera configured for video feed.")

            while True:
                try:
                    frame = await asyncio.get_event_loop().run_in_executor(
                        executor, camera.capture_array
                    )
                    if frame is None:
                        logging.warning("Failed to capture video frame.")
                        continue

                    success, buffer = cv2.imencode('.jpg', frame)
                    if not success:
                        logging.warning("Failed to encode video frame.")
                        continue

                    frame_data = base64.b64encode(buffer).decode('utf-8')
                    await websocket.send(frame_data)
                except asyncio.CancelledError:
                    logging.info("WebSocket connection closed by client.")
                    break
                except Exception as e:
                    logging.error(f"Error during video streaming: {e}")
                    break
        finally:
            logging.info("Stopping video feed and reconfiguring for photo mode.")
            camera.stop()
            await asyncio.get_event_loop().run_in_executor(executor, camera.configure, photo_config)
            camera.start()

@app.route('/capture_photo', methods=['POST'])
async def capture_photo():
    """Capture a high-resolution photo."""
    async with camera_lock:
        try:
            logging.info("Starting photo capture process.")
            camera.stop()
            await asyncio.get_event_loop().run_in_executor(executor, camera.configure, photo_config)
            camera.start()

            frame = await asyncio.get_event_loop().run_in_executor(executor, camera.capture_array)
            if frame is None:
                logging.error("Failed to capture a valid frame.")
                return jsonify({"error": "Capture failed."}), 500

            timestamp = strftime("%Y-%m-%d_%H-%M-%S")
            cv2.putText(frame, timestamp, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

            filename = f"photo_{timestamp}.jpg"
            file_path = os.path.join('photos', filename)
            os.makedirs('photos', exist_ok=True)
            if not cv2.imwrite(file_path, frame):
                logging.error(f"Failed to save photo at {file_path}.")
                return jsonify({"error": "Failed to save photo."}), 500
            logging.info(f"Photo saved at {file_path}.")

            return jsonify({"message": "Photo captured successfully!", "file": filename})
        except Exception as e:
            logging.error(f"Error capturing photo: {e}")
            return jsonify({"error": f"Failed to capture photo. Reason: {e}"}), 500

@app.before_serving
async def start_camera():
    """Start the camera when the server starts."""
    global camera
    if not camera:
        camera = Picamera2()
        camera.configure(photo_config)
        camera.start()
        logging.info("Camera started.")

@app.after_serving
async def release_camera():
    """Release the camera when the server stops."""
    global camera
    if camera:
        camera.stop()
        logging.info("Camera released.")

if __name__ == '__main__':
    logging.info("Starting Quart app.")
    app.run(host='0.0.0.0', port=5000, debug=True)
