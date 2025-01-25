from quart import Quart, render_template, jsonify
from picamera2 import Picamera2
import cv2
import os
from time import strftime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Quart(__name__)
camera = Picamera2()
executor = ThreadPoolExecutor()

# Configure camera for still photo capture
photo_config = camera.create_still_configuration({"size": (4056, 3040)})
camera.configure(photo_config)
camera.start()

@app.route('/')
async def index():
    """Render the homepage."""
    logging.info("Rendering index page.")
    return await render_template('index_photo.html')

@app.route('/capture_photo', methods=['POST'])
async def capture_photo():
    """Capture a high-resolution photo."""
    try:
        logging.info("Starting photo capture process.")

        # Capture a high-resolution frame
        frame = await asyncio.get_event_loop().run_in_executor(
            executor, camera.capture_array
        )
        if frame is None:
            logging.error("Failed to capture a valid frame.")
            return jsonify({"error": "Capture failed."}), 500

        logging.debug(f"Captured frame with shape: {frame.shape}")

        # Add a timestamp overlay
        timestamp = strftime("%Y-%m-%d_%H-%M-%S")
        cv2.putText(frame, timestamp, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        # Save the photo
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
    # Run the Quart app
    logging.basicConfig(level=logging.DEBUG)
    logging.info("Starting Quart app.")
    app.run(host='0.0.0.0', port=5000, debug=True)
