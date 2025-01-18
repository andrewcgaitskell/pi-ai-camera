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

# Initialize the PiCamera2 instance
camera = None
camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)}))

# Set white balance and other controls
camera.set_controls({
    "AwbEnable": True,  # Enable auto white balance
    "Saturation": 1.2,  # Boost saturation slightly
    "Contrast": 1.0,
    "Brightness": 0.5
})


async def safe_stop_camera():
    """Safely stop and release the camera."""
    global camera
    if camera:
        camera.stop()
        logging.info("Camera stopped and released.")
        camera = None

def handle_exit_signal(loop, task):
    """Handle termination signals."""
    logging.info("Received exit signal.")
    loop.run_until_complete(task)

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
            # Capture and process frames
            frame = camera.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert for OpenCV processing

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
    global camera
    if not camera:
        camera = Picamera2()
        camera.configure(camera.create_preview_configuration())
        camera.start()
        logging.info("Camera started.")

@app.after_serving
async def cleanup():
    """Release resources when the server stops."""
    await safe_stop_camera()

if __name__ == '__main__':
    # Create a cleanup task
    loop = asyncio.get_event_loop()
    cleanup_task = asyncio.ensure_future(safe_stop_camera())

    # Attach signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_exit_signal, loop, cleanup_task)

    # Run the Quart app
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        loop.run_until_complete(cleanup_task)
