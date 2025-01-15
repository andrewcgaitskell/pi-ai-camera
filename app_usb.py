from quart import Quart, Response, render_template, request, send_file
import cv2
import os
from datetime import datetime
from PIL import Image, ExifTags

app = Quart(__name__)

# Base directory to store all photos
BASE_PHOTO_DIR = 'photos'
os.makedirs(BASE_PHOTO_DIR, exist_ok=True)

camera = cv2.VideoCapture(0)  # Use 0 for the default webcam


def generate_frames():
    while True:
        # Capture frame-by-frame
        success, frame = camera.read()
        if not success:
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

    success, frame = camera.read()
    if success:
        # Generate a timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        photo_path = os.path.join(folder_path, f'photo_{timestamp}.jpg')
        
        # Save the photo using OpenCV
        cv2.imwrite(photo_path, frame)
        
        # Add metadata (tags) to the photo
        with Image.open(photo_path) as img:
            img = img.convert("RGB")
            exif_data = img.getexif()
            
            # Add custom tag metadata
            exif_data[ExifTags.TAGS["ImageDescription"]] = tags
            
            # Save the updated photo
            img.save(photo_path, "JPEG", exif=exif_data)
        
        return {"message": "Photo captured successfully.", "photo_path": photo_path}, 200
    return {"error": "Failed to capture photo."}, 500


@app.route('/get_photo/<path:filepath>')
async def get_photo(filepath):
    """Serve the captured photo."""
    photo_path = os.path.join(BASE_PHOTO_DIR, filepath)
    if os.path.exists(photo_path):
        return await send_file(photo_path, mimetype='image/jpeg')
    return {"error": "Photo not found."}, 404


@app.before_serving
async def start_camera():
    """Start the camera when the server starts."""
    global camera
    if not camera.isOpened():
        camera.open(0)


@app.after_serving
async def release_camera():
    """Release the camera when the server stops."""
    global camera
    if camera.isOpened():
        camera.release()


if __name__ == '__main__':
    # Set the app to listen on all network interfaces and a specific port (e.g., 5000)
    app.run(host='0.0.0.0', port=5000, debug=True)
