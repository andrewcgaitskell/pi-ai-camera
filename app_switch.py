from quart import Quart, render_template, Response, redirect, url_for
from picamera2 import Picamera2
import cv2
import numpy as np

app = Quart(__name__)
picam2 = Picamera2()

# Configure preview mode
preview_config = picam2.create_preview_configuration()
capture_config = picam2.create_still_configuration()
picam2.configure(preview_config)
picam2.start(show_preview=False)

@app.route('/')
async def index():
    """Render the main page."""
    return await render_template('index_switch.html')

def generate_frames():
    """Generator for video feed frames."""
    while True:
        frame = picam2.capture_array("main")  # Capture frame in preview mode
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
async def video_feed():
    """Route for video feed."""
    return Response(generate_frames(),
                    content_type='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture')
async def capture():
    """Capture a high-resolution image."""
    array = picam2.switch_mode_and_capture_array(capture_config, "main")
    filename = 'static/capture.jpg'
    cv2.imwrite(filename, array)  # Save the captured image
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
