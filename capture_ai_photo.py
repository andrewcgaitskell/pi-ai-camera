import os
import datetime
import sys
import termios
import tty
from picamera2 import Picamera2

# Create an output folder to save the photos
output_folder = "/home/scanpi/photos"
os.makedirs(output_folder, exist_ok=True)

# Initialize the camera
picam2 = Picamera2()

# Configure the camera in preview mode initially
preview_config = picam2.create_preview_configuration()
still_config = picam2.create_still_configuration()
picam2.configure(preview_config)
picam2.start()

print("Press 'c' to capture a photo or 'q' to quit.")

def get_key():
    """Reads a single character from standard input."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

try:
    while True:
        print("Awaiting input...")
        key = get_key()
        if key == 'c':
            # Generate a timestamped filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(output_folder, f"photo_{timestamp}.jpg")
            
            # Capture the photo
            picam2.switch_mode_and_capture_file(still_config, file_path)
            print(f"Photo captured and saved to {file_path}")

        elif key == 'q':
            print("Quitting the application.")
            break

finally:
    picam2.stop()
    print("Camera stopped.")
