from quart import Quart, websocket, jsonify, render_template
from picamera2 import Picamera2
import cv2
import base64
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Quart(__name__)

# Configure Picamera2
picam2 = Picamera2()
main_stream = {"size": [dim // 2 for dim in picam2.sensor_resolution]}  # Half-resolution for photos
lores_stream = {"size": (640, 480)}  # Low-resolution for video feed
video_config = picam2.create_video_configuration(main_stream, lores_stream, encode="lores")
picam2.configure(video_config)
picam2.start()

@app.route('/')
async def index():
    """Serve the homepage template."""
    return await render_template('index_video.html')

@app.websocket('/video_feed')
async def video_feed():
    """WebSocket endpoint for streaming video frames."""
    try:
        while True:
            # Capture a frame using the request object
            request = picam2.capture_request()
            try:
                # Get the lores frame as a numpy array
                lores_frame = request.make_array("lores")
                if lores_frame is None:
                    logging.warning("Lores frame is None.")
                    continue

                logging.debug(f"Lores frame shape: {lores_frame.shape}")

                # Encode the frame as JPEG using OpenCV
                success, encoded_frame = cv2.imencode(".jpg", lores_frame)
                if not success:
                    logging.warning("Failed to encode lores frame.")
                    continue

                # Convert to Base64 for WebSocket transmission
                frame_data = base64.b64encode(encoded_frame).decode('utf-8')
                await websocket.send(frame_data)
            finally:
                # Release the request to avoid memory leaks
                request.release()
    except asyncio.CancelledError:
        logging.info("WebSocket connection closed.")
    except Exception as e:
        logging.error(f"Error in video feed: {e}")

@app.route('/capture_photo', methods=['POST'])
async def capture_photo():
    """Capture a high-resolution photo."""
    try:
        logging.info("Capturing high-resolution photo.")
        request = picam2.capture_request()
        request.save("main", "photo.jpg")  # Save from high-resolution stream
        request.release()
        logging.info("Photo captured successfully.")

        return jsonify({"message": "Photo captured successfully!", "file": "photo.jpg"})
    except Exception as e:
        logging.error(f"Error capturing photo: {e}")
        return jsonify({"error": f"Failed to capture photo. Reason: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
