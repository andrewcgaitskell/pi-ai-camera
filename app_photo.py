from quart import Quart, websocket, render_template, jsonify
from picamera2 import Picamera2
import cv2
import base64
import logging
from time import sleep, strftime
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Quart(__name__)

camera = Picamera2()

# Configure the camera
video_config = camera.create_video_configuration({"size": (1280, 720)})
camera.configure(video_config)
camera.set_controls({"AeEnable": True})

# Start the camera
camera.start()

# Allow the camera to stabilize
sleep(2)

@app.route('/')
async def index():
    """Render the homepage."""
    return await render_template('index_photo.html')

@app.websocket('/video_feed')
async def video_feed():
    """WebSocket endpoint to stream video frames."""
    while True:
        try:
            # Capture a frame
            frame = camera.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Encode frame as JPEG
            success, buffer = cv2.imencode('.jpg', frame)
            if not success:
                logging.warning("Failed to encode frame.")
                continue

            # Convert to base64 to send over WebSocket
            frame_data = base64.b64encode(buffer).decode('utf-8')

            # Send the frame over WebSocket
            await websocket.send(frame_data)
        except Exception as e:
            logging.error(f"Error during video feed streaming: {e}")
            break

@app.route('/capture_photo', methods=['POST'])
async def capture_photo():
    """Capture a timestamped photo."""
    try:
        # Capture a frame
        frame = camera.capture_array()

        # Add a timestamp overlay to the image
        timestamp = strftime("%Y-%m-%d_%H-%M-%S")
        cv2.putText(frame, timestamp, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        # Save the photo
        filename = f"photo_{timestamp}.jpg"
        file_path = os.path.join('photos', filename)
        os.makedirs('photos', exist_ok=True)
        cv2.imwrite(file_path, frame)

        logging.info(f"Photo captured and saved as {file_path}.")
        return jsonify({"message": "Photo captured successfully!", "file": filename})
    except Exception as e:
        logging.error(f"Error capturing photo: {e}")
        return jsonify({"error": "Failed to capture photo."}), 500

@app.before_serving
async def start_camera():
    """Start the camera when the server starts."""
    global camera
    if not camera:
        camera = Picamera2()
        camera.configure(camera.create_preview_configuration())
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
    app.run(host='0.0.0.0', port=5000, debug=True)
