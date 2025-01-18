from quart import Quart, render_template, Response, redirect, url_for
from picamera2 import Picamera2
import cv2
import os
import logging
from datetime import datetime

app = Quart(__name__)
picam2 = Picamera2()

# Configure preview and capture modes
preview_config = picam2.create_preview_configuration()
capture_config = picam2.create_still_configuration()
picam2.configure(preview_config)
picam2.start(show_preview=False)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Application started.")

# Ensure the capture directory exists
CAPTURE_DIR = '/home/scanpi/photos'
os.makedirs(CAPTURE_DIR, exist_ok=True)

@app.route('/')
async def index():
    """Render the main page."""
    return await render_template('index_switch.html')

def generate_frames():
    """Generator for video feed frames."""
    while True:
        try:
            frame = picam2.capture_array("main")  # Capture frame in preview mode
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            logging.error(f"Error generating video feed: {e}")
            break

@app.route('/video_feed')
async def video_feed():
    """Route for video feed."""
    return Response(generate_frames(),
                    content_type='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture')
async def capture():
    """Capture a high-resolution image."""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(CAPTURE_DIR, f'capture_{timestamp}.jpg')
        logging.info(f"Capturing photo: {filename}")

        # Capture and save the photo
        array = picam2.switch_mode_and_capture_array(capture_config, "main")
        cv2.imwrite(filename, array)
        logging.info(f"Photo saved: {filename}")

        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Error capturing photo: {e}")
        return "Error capturing photo", 500

if __name__ == '__main__':
    logging.info("Starting Quart app.")
    app.run(host='0.0.0.0', port=5000, debug=True)
