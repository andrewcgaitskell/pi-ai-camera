import os
from picamera2 import Picamera2

# Create an output folder to save the photos
output_folder = "photos"
os.makedirs(output_folder, exist_ok=True)

# Initialize the camera
picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration())

try:
    # Start the camera
    picam2.start()

    # Capture the image
    file_path = os.path.join(output_folder, "photo.jpg")
    print(f"Capturing photo and saving to {file_path}...")
    picam2.capture_file(file_path)

    print("Photo captured successfully!")
finally:
    # Stop the camera
    picam2.stop()
    print("Camera stopped.")

