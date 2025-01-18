import os
import datetime
import keyboard  # Requires the 'keyboard' library
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

try:
    while True:
        if keyboard.is_pressed('c'):
            # Generate a timestamped filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(output_folder, f"photo_{timestamp}.jpg")
            
            # Capture the photo
            picam2.switch_mode_and_capture_file(still_config, file_path)
            print(f"Photo captured and saved to {file_path}")

        elif keyboard.is_pressed('q'):
            print("Quitting the application.")
            break

finally:
    picam2.stop()
    print("Camera stopped.")
