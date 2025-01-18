from quart import Quart, websocket, render_template
from picamera2 import Picamera2
import cv2
import base64
import logging
import asyncio
import signal

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Quart(__name__)

camera = Picamera2()

camera.configure(camera.create_preview_configuration())
camera.start()

@app.route('/')
async def index():
    """Render the homepage."""
    return await render_template('index_ws.html')

@app.websocket('/video_feed')
async def video_feed():
    """WebSocket endpoint to stream video frames."""
    try:
        while True:
            if websocket.closed:  # Check if the WebSocket connection is closed
                logging.info("WebSocket closed.")
                break

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

            # Prevent CPU overload
            await asyncio.sleep(0.03)  # Approx. 30 FPS
    except Exception as e:
        logging.error(f"Error during video feed streaming: {e}")
    finally:
        logging.info("WebSocket connection terminated.")

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

def shutdown_handler(*_):
    """Handle application shutdown."""
    global camera
    if camera:
        camera.stop()
        logging.info("Camera released.")
    logging.info("Application shutdown.")

if __name__ == '__main__':
    # Handle shutdown signals
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Run the Quart app
    app.run(host='0.0.0.0', port=5000, debug=True)
