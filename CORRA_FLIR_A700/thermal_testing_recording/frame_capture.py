import PySpin
from collections import deque
import time
from threading import Event

# Shared queue to hold frames and an event to control capture thread
frame_queue = deque(maxlen=10)
capture_event = Event()  # This will signal the capture thread to stop

def start_frame_capture(camera):
    """Capture frames continuously and add to frame_queue."""
    while not capture_event.is_set():  # Check event instead of stop flag
        image_result = camera.GetNextImage(1000)  # 1000 ms timeout to avoid blocking indefinitely
        if image_result.IsIncomplete():
            print("Image incomplete with image status %d ..." % image_result.GetImageStatus())
            continue
        image_data = image_result.GetNDArray()
        frame_queue.append(image_data)
        image_result.Release()

        time.sleep(0.01)  # Small delay to allow graceful termination
