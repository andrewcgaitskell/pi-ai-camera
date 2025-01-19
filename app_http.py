from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from picamera2 import Picamera2
import io
import threading
from time import sleep
import logging
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Directory to save captured photos
CAPTURE_DIR = "/home/scanpi/photos"
os.makedirs(CAPTURE_DIR, exist_ok=True)

# MJPEG Streaming Output Class
class StreamingOutput:
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def write(self, buf):
        """Write the new frame and notify clients."""
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

# HTTP Request Handler for Web Page, Video Feed, and Photo Capture
class StreamingHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, picam2=None, output=None, **kwargs):
        self.picam2 = picam2
        self.output = output
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == '/':
            # Serve the main HTML page
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(self.render_html_page().encode("utf-8"))
        elif self.path == '/video_feed':
            # Serve the MJPEG video feed
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            try:
                while True:
                    with self.output.condition:
                        self.output.condition.wait()
                        frame = self.output.frame
                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except BrokenPipeError:
                logging.info("Client disconnected from video feed.")
            except Exception as e:
                logging.error(f"Streaming error: {e}")
        elif self.path == '/capture_photo':
            # Handle photo capture
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                photo_path = os.path.join(CAPTURE_DIR, f"photo_{timestamp}.jpg")
                logging.info(f"Capturing photo: {photo_path}")

                # Capture and save the photo
                self.picam2.switch_mode_and_capture_file(photo_path, self.picam2.create_still_configuration())
                
                # Respond with success
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Photo saved: {photo_path}".encode("utf-8"))
            except Exception as e:
                logging.error(f"Error capturing photo: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Error capturing photo")
        else:
            self.send_error(404)
            self.end_headers()

    def render_html_page(self):
        """Render the HTML page for the web interface."""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Camera Feed</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    background-color: #f4f4f9;
                    margin: 0;
                    padding: 0;
                }}
                h1 {{
                    color: #333;
                    margin: 20px 0;
                }}
                img {{
                    width: 100%;
                    max-width: 640px;
                    height: auto;
                    border: 2px solid black;
                    margin: 0 auto 20px;
                    display: block;
                }}
                button {{
                    padding: 10px 20px;
                    font-size: 16px;
                    color: white;
                    background-color: #007bff;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }}
                button:hover {{
                    background-color: #0056b3;
                }}
            </style>
        </head>
        <body>
            <h1>Camera Feed</h1>
            <!-- Live Video Feed -->
            <img src="/video_feed" alt="Video Feed">
            <!-- Capture Photo Button -->
            <button onclick="capturePhoto()">Capture Photo</button>
            <script>
                async function capturePhoto() {{
                    try {{
                        const response = await fetch('/capture_photo');
                        const message = await response.text();
                        alert(message);
                    }} catch (error) {{
                        alert('Failed to capture photo: ' + error);
                    }}
                }}
            </script>
        </body>
        </html>
        """

# Threaded HTTP Server
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

# Main Function
def main():
    global output
    output = StreamingOutput()

    # Initialize Picamera2
    picam2 = Picamera2()
    preview_config = picam2.create_video_configuration()
    picam2.configure(preview_config)
    picam2.start()

    # Continuously capture frames in a separate thread
    def capture_frames():
        while True:
            stream = io.BytesIO()
            picam2.capture_file(stream, format="jpeg")
            stream.seek(0)
            output.write(stream.read())
            stream.close()
            sleep(0.05)  # Adjust for frame rate

    # Start the capture thread
    capture_thread = threading.Thread(target=capture_frames)
    capture_thread.daemon = True
    capture_thread.start()

    # Set up the server
    address = ('', 5000)  # Serve on all interfaces, port 5000
    server = ThreadedHTTPServer(address, lambda *args, **kwargs: StreamingHandler(*args, picam2=picam2, output=output, **kwargs))
    logging.info("Starting server on http://0.0.0.0:5000...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        logging.info("Server stopped.")
        picam2.stop()

if __name__ == '__main__':
    main()
