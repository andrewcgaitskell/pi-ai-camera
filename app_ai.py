from quart import Quart, Response, render_template, request, send_file
import os
from datetime import datetime
from PIL import Image
import piexif  # Ensure piexif is installed for robust EXIF handling
import logging
from picamera2 import Picamera2, Preview

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Quart(__name__)

# Base directory to store all photos
BASE_PHOTO_DIR = 'photos'
os.makedirs(BASE_PHOTO_DIR, exist_ok=True)

# Initialize the PiCamera2 instance
camera = Picamera2()
camera.configure(camera.create_preview_configuration())
camera.start()


def generate_frames():
    while True:
        # Capture a frame
        frame = camera.capture_array()
        if frame is None:
            logging.error("Failed to read frame from the camera.")
            break
        else:
            # Encode the frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Yield the frame as part of a multipart HTTP response
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
async def index():
    """Render the homepage."""
    return await render_template('index.html')


@app.route('/video_feed')
async def video_feed():
    """Route to stream the video feed."""
    return Response(generate_frames(),
                    content_type='multipart/x-mixed-replace; boundary=frame')


@app.route('/capture_photo', methods=['POST'])
async def capture_photo():
    """Capture a still photo, save it with a timestamp, and embed tags."""
    data = await request.form
    tags = data.get('tags', 'No tags provided')
    folder_name = data.get('folder_name', 'default_folder')

    # Ensure folder_name is safe and create nested directories inside the base photo directory
    sanitized_folder_name = os.path.normpath(folder_name)
    folder_path = os.path.join(BASE_PHOTO_DIR, sanitized_folder_name)
    os.makedirs(folder_path, exist_ok=True)

    # Capture the photo
    photo_path = os.path.join(folder_path, f'photo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg')
    camera.capture_file(photo_path)

    logging.info(f"Photo saved at {photo_path}")

    try:
        # Add metadata (tags) to the photo using piexif
        exif_dict = piexif.load(photo_path)
        exif_dict["0th"][piexif.ImageIFD.ImageDescription] = tags.encode('utf-8')
        exif_bytes = piexif.dump(exif_dict)

        # Save the updated photo with EXIF
        with Image.open(photo_path) as img:
            img.save(photo_path, "jpeg", exif=exif_bytes)

        logging.info(f"EXIF metadata updated for {photo_path} with tags: {tags}")
        return {"message": "Photo captured successfully.", "photo_path": photo_path}, 200
    except Exception as e:
        logging.error(f"Failed to add EXIF metadata: {e}")
        return {"message": "Photo saved, but failed to update EXIF metadata.", "photo_path": photo_path}, 200


@app.route('/get_photo/<path:filepath>')
async def get_photo(filepath):
    """Serve the captured photo."""
    photo_path = os.path.join(BASE_PHOTO_DIR, filepath)
    if os.path.exists(photo_path):
        return await send_file(photo_path, mimetype='image/jpeg')
    logging.error(f"Photo not found at {photo_path}")
    return {"error": "Photo not found."}, 404


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
    # Set the app to listen on all network interfaces and a specific port (e.g., 5000)
    app.run(host='0.0.0.0', port=5000, debug=True)
