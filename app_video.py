from quart import Quart, websocket, jsonify, render_template
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
import asyncio
import base64
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Quart(__name__)

picam2 = Picamera2()
half_resolution = [dim // 2 for dim in picam2.sensor_resolution]
main_stream = {"size": half_resolution}
lores_stream = {"size": (640, 480)}
video_config = picam2.create_video_configuration(main_stream, lores_stream, encode="lores")
picam2.configure(video_config)

picam2.start()

@app.route('/')
async def index():
    """Serve the homepage template."""
    logging.info("Serving index page.")
    return await render_template('index_video.html')

@app.websocket('/video_feed')
async def video_feed():
    """WebSocket endpoint for streaming video frames."""
    encoder = JpegEncoder()
    try:
        while True:
            # Capture a frame using the request object
            request = picam2.capture_request()
            try:
                # Encode the lores stream directly using the request object
                encoded_frame = encoder.encode(request, "lores")
                if encoded_frame is None:
                    logging.warning("Encoded frame is None.")
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
