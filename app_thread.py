from quart import Quart, websocket, render_template
import threading
import time
import asyncio

# Create a Quart app instance
app = Quart(__name__)

# Global variables
counter = 0
captured_numbers = []
lock = threading.Lock()

# Function to increment the counter every second
def increment_counter():
    global counter
    while True:
        counter += 1
        time.sleep(1)

@app.websocket("/ws")
async def ws():
    global counter, captured_numbers
    while True:
        await websocket.send_json({"counter": counter, "captured_numbers": captured_numbers})
        await asyncio.sleep(1)

@app.route("/")
async def index():
    return await render_template("index_thread.html")

@app.route("/capture", methods=["POST"])
async def capture():
    global counter, captured_numbers, lock
    async with asyncio.to_thread(lock.acquire):
        try:
            captured_numbers.append(counter)
        finally:
            lock.release()
    return "", 204

if __name__ == "__main__":
    # Start the increment thread
    counter_thread = threading.Thread(target=increment_counter, daemon=True)
    counter_thread.start()

    # Run the Quart app
    app.run(host="0.0.0.0", port=5000)
