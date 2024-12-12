import cv2
import numpy as np
from frame_capture import frame_queue
import time

# Global variable for full-screen toggle
full_screen = False

def display_frames(output_file="output_video.avi", delay=0.05):
    """Display and record frames from the thermal camera."""
    global full_screen
    frame_count = 0

    # Initialize video writer for recording
    fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Use XVID codec for .avi format
    video_writer = None  # Define later when first frame size is known
    recording = False  # To ensure video writer starts only if frames are available

    # Start with a small, resizable window
    cv2.namedWindow('Thermal Display', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Thermal Display', 640, 480)

    try:
        while True:
            if frame_queue:
                frame_count += 1
                image_data = frame_queue.popleft()
                normalized_image = cv2.normalize(image_data, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                colored_image = cv2.applyColorMap(normalized_image, cv2.COLORMAP_INFERNO)

                # Initialize video writer once the frame size is known
                if not recording:
                    height, width = colored_image.shape[:2]
                    video_writer = cv2.VideoWriter(output_file, fourcc, 20.0, (width, height))
                    recording = True

                # Write frame to the video file
                if recording:
                    video_writer.write(colored_image)

                # Display the frame
                cv2.imshow('Thermal Display', colored_image)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('f'):
                    # Full-screen toggle
                    if full_screen:
                        cv2.setWindowProperty('Thermal Display', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                        cv2.resizeWindow('Thermal Display', 640, 480)
                        full_screen = False
                    else:
                        cv2.setWindowProperty('Thermal Display', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                        full_screen = True

                time.sleep(delay)

    finally:
        # Release video writer and close display
        if recording:
            video_writer.release()
        cv2.destroyAllWindows()
