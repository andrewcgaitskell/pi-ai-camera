from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from picamera2 import Picamera2
import io
import threading
from time import sleep
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# HTTP Request Handler for MJPEG Streaming
class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/video_feed':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except BrokenPipeError:
                logging.info("Client disconnected from video feed.")
            except Exception as e:
                logging.error(f"Streaming error: {e}")
        else:
            self.send_error(404)
            self.end_headers()

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
    server = ThreadedHTTPServer(address, StreamingHandler)
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
