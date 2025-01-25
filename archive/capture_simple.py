import cv2

# Initialize the camera (usually 0 for the default camera)
camera = cv2.VideoCapture(0)

# Check if the camera is opened successfully
if not camera.isOpened():
    print("Error: Could not access the camera.")
else:
    # Capture a single frame
    ret, frame = camera.read()
    if ret:
        # Save the frame to a file
        filename = "captured_image.jpg"
        cv2.imwrite(filename, frame)
        print(f"Image saved as {filename}")
    else:
        print("Error: Could not read the frame from the camera.")

# Release the camera
camera.release()

