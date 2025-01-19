import PySpin
from collections import deque
import time
from threading import Event # Provides an event (capture_event) to signal when to stop capturing frames.
# ref: https://superfastpython.com/thread-event-object-in-python/


# Shared queue to hold frames and an event to control capture thread
frame_queue = deque(maxlen=10) 
# Stores the most recent frames pulled from the camera (with maxlen=10, 
# so it automatically discards the oldest frames if the queue is full).


capture_event = Event()  # This will signal the capture thread to stop | used to stop the continuous capture loop

#  constantly pulling frames from the camera.
# 1. continuously acquiring frames from the given camera in a background thread 
# 2. storing those frames into a shared queue (frame_queue)

def start_frame_capture(camera):
    """Capture frames continuously and add to frame_queue."""
    
    while not capture_event.is_set():  # Check event instead of stop flag
        image_result = camera.GetNextImage(1000)  # 1000 ms timeout to avoid blocking indefinitely
        if image_result.IsIncomplete(): # CHECK if the image is complete or not => if not complete, skipping
            print("Image incomplete with image status %d ..." % image_result.GetImageStatus())
            continue
        
        image_data = image_result.GetNDArray()
        frame_queue.append(image_data) # storing all the images
        image_result.Release()

        time.sleep(0.01)  # Small delay to allow graceful termination
