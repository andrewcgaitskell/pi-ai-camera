from quart import Quart, websocket, render_template
from picamera2 import Picamera2
import cv2
import base64
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Quart(__name__)

camera = Picamera2()

# Configure the camera for live streaming
camera.configure(camera.create_preview_configuration())

# Start the camera
camera.start()

# Adjust initial controls for better color rendering
camera.set_controls({
    "AwbEnable": False,           # Disable auto white balance for manual control
    "ColourGains": (2.0, 1.5),    # Adjust red (2.0) and blue (1.5) gains
    "ColourMatrix": [
        1.5, 0.0, 0.0,           # Boost red channel
        0.0, 1.0, 0.0,           # Keep green neutral
        0.0, 0.0, 0.8            # Reduce blue influence
    ],
    "Saturation": 1.3,            # Increase saturation for more vivid colors
    "Contrast": 1.2,              # Enhance contrast for better differentiation
    "ExposureTime": 8000,         # Set exposure time in microseconds
    "AnalogueGain": 1.0           # Lower gain to prevent oversaturation
})

# Allow the camera to stabilize
sleep(2)

@app.route('/')
async def index():
    """Render the homepage."""
    return await render_template('index_ws.html')

@app.websocket('/video_feed')
async def video_feed():
    """WebSocket endpoint to stream video frames."""
    while True:
        try:
            # Capture a frame
            frame = camera.capture_array()

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
