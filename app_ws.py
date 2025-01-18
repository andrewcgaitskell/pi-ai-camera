from quart import Quart, websocket, render_template
from picamera2 import Picamera2
import cv2
import base64
import logging
import asyncio
import signal
import subprocess

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Quart(__name__)

# Initialize the PiCamera2 instance
camera = None

async def reset_camera():
    """Reset the camera hardware."""
    try:
        logging.info("Resetting camera hardware.")
        subprocess.run(['sudo', 'modprobe', '-r', 'bcm2835_v4l2'], check=True)
        await asyncio.sleep(1)
        subprocess.run(['sudo', 'modprobe', 'bcm2835_v4l2'], check=True)
        logging.info("Camera hardware reset completed.")
    except Exception as e:
        logging.error(f"Failed to reset camera hardware: {e}")

async def safe_stop_camera():
    """Safely stop and release the camera."""
    global camera
    if camera:
        try:
            camera.stop()
            logging.info("Camera stopped and released.")
        except Exception as e:
            logging.error(f"Error while stopping the camera: {e}")
        finally:
            camera = None

async def initialize_camera():
    """Initialize and start the camera, resetting if needed."""
    global camera
    try:
        if not camera:
            camera = Picamera2()
            camera.configure(camera.create_preview_configuration())
            camera.start()
            logging.info("Camera started successfully.")
    except Exception as e:
        logging.error(f"Error initializing the camera: {e}")
        await safe_stop_camera()
        logging.info("Resetting the camera and retrying initialization.")
        await reset_camera()
        await asyncio.sleep(1)  # Allow time for the hardware to reset
        await initialize_camera()  # Retry initialization

def handle_exit_signal(loop):
    """Handle termination signals."""
    logging.info("Received exit signal.")
    loop.create_task(safe_stop_camera())

@app.route('/')
async def index():
    """Render the homepage."""
    return await render_template('index_ws.html')

@app.websocket('/video_feed')
async def video_feed():
    """WebSocket endpoint to stream video frames."""
    global camera
    try:
        while True:
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
    except asyncio.CancelledError:
        logging.info("WebSocket connection cancelled.")
    except Exception as e:
        logging.error(f"Error during video feed streaming: {e}")
    finally:
        logging.info("WebSocket connection closed.")

@app.before_serving
async def start_camera():
    """Start the camera when the server starts."""
    await initialize_camera()

@app.after_serving
async def cleanup():
    """Release resources when the server stops."""
    await safe_stop_camera()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    # Attach signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: handle_exit_signal(loop))

    # Run the Quart app
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        loop.run_until_complete(safe_stop_camera())
