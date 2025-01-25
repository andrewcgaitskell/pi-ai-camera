from picamera2 import Picamera2
from picamera2.devices.imx500 import IMX500

# Initialize IMX500 and Picamera2
model_file = "/usr/share/imx500-models/imx500_network_mobilenet_v2.rpk"
imx500 = IMX500(model_file)
picam2 = Picamera2()
picam2.start()

# Capture and test inference
request = picam2.capture_request()
outputs = imx500.get_outputs(request.get_metadata())
print("Model Outputs:", outputs)

picam2.close()
