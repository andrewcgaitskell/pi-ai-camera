import os
from picamera2 import Picamera2

def capture_photo(output_file="photo.jpg"):
    # Initialize Picamera2
    picam2 = Picamera2()

    # Configure the camera for still capture
    capture_config = picam2.create_still_configuration()
    picam2.configure(capture_config)

    # Start the camera
    picam2.start()
    print("Camera started, taking photo...")

    # Capture the photo
    picam2.capture_file(output_file)
    print(f"Photo saved as {output_file}")

    # Stop the camera
    picam2.stop()
    print("Camera stopped.")

if __name__ == "__main__":
    # Ensure the output directory exists
    output_folder = "/home/scanpi/photos"
    if not os.path.exists(os.path.dirname(output_folder)):
        os.makedirs(os.path.dirname(output_folder))
    photo_name = "photo.jpg"
    full_output = output_folder  + "/" + photo_name
    capture_photo(full_output)
