import cv2
import numpy as np
from frame_capture import frame_queue
from face_detection import detect_face_and_roi
from collections import deque
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
import time
import dlib
from collections import deque

# Paths and model initialization
predictor_path = r"C:\Users\Lenovo\source\repos\NaloxSAVER_FLIR_A700\thermal_testing\shape_predictor_68_face_landmarks.dat"
predictor = dlib.shape_predictor(predictor_path)
detector = dlib.get_frontal_face_detector()

# Global variable for full-screen toggle
full_screen = False

# Temperature threshold for alerts
ALERT_THRESHOLD = 5

# Initialize variables for overlay and plotting
mouth_intensity_history = deque(maxlen=50)
nose_intensity_history = deque(maxlen=50)  # Track intensity for the nose region

# Matplotlib setup for real-time plotting
plt.style.use("ggplot")
fig, ax = plt.subplots()
line_mouth, = ax.plot([], [], label="Mouth Intensity", color="red")
line_nose, = ax.plot([], [], label="Nose Intensity", color="blue")
ax.set_ylim(0, 255)
ax.set_xlim(0, 50)
ax.set_xlabel("Time (frames)")
ax.set_ylabel("Intensity")
ax.legend(loc="upper left")

def init_plot():
    line_mouth.set_data([], [])
    line_nose.set_data([], [])
    return line_mouth, line_nose

def update_plot(frame):
    line_mouth.set_data(range(len(mouth_intensity_history)), list(mouth_intensity_history))
    line_nose.set_data(range(len(nose_intensity_history)), list(nose_intensity_history))
    return line_mouth, line_nose

# Disable caching to suppress warning
ani = FuncAnimation(fig, update_plot, init_func=init_plot, blit=True, cache_frame_data=False)

# Function to convert pixel intensity to temperature
def pixel_to_temperature(pixel_value, min_temp=20.0, max_temp=40.0):
    return min_temp + (pixel_value / 255) * (max_temp - min_temp)

# Initialize deque to hold recent positions for smoothing
nostril_positions_left = deque(maxlen=5)  # Hold up to 5 recent positions for left nostril
nostril_positions_right = deque(maxlen=5)  # Hold up to 5 recent positions for right nostril

def detect_nostrils_and_mouth(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    for face in faces:
        landmarks = predictor(gray, face)

        # Mouth points for tracking
        mouth_points = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(48, 68)]
        mouth_center_x = int(np.mean([point[0] for point in mouth_points]))
        mouth_center_y = int(np.mean([point[1] for point in mouth_points]))

        # Nostril points (using landmarks 31 for left and 35 for right nostril)
        left_nostril_x, left_nostril_y = landmarks.part(31).x, landmarks.part(31).y
        right_nostril_x, right_nostril_y = landmarks.part(35).x, landmarks.part(35).y

        # Smooth the nostril positions
        nostril_positions_left.append((left_nostril_x, left_nostril_y))
        nostril_positions_right.append((right_nostril_x, right_nostril_y))
        
        smoothed_left_nostril = np.mean(nostril_positions_left, axis=0).astype(int)
        smoothed_right_nostril = np.mean(nostril_positions_right, axis=0).astype(int)
        
        # Define a slightly larger ROI around each nostril
        left_nostril_roi = gray[smoothed_left_nostril[1] - 5: smoothed_left_nostril[1] + 5,
                                smoothed_left_nostril[0] - 5: smoothed_left_nostril[0] + 5]
        right_nostril_roi = gray[smoothed_right_nostril[1] - 5: smoothed_right_nostril[1] + 5,
                                 smoothed_right_nostril[0] - 5: smoothed_right_nostril[0] + 5]
        
        avg_intensity_left_nostril = np.mean(left_nostril_roi)
        avg_intensity_right_nostril = np.mean(right_nostril_roi)
        
        # Convert intensity to temperature
        left_nostril_temp = pixel_to_temperature(avg_intensity_left_nostril)
        right_nostril_temp = pixel_to_temperature(avg_intensity_right_nostril)
        avg_nose_temperature = (left_nostril_temp + right_nostril_temp) / 2  # Average temperature of both nostrils

        # Draw circles and display temperatures for each nostril
        cv2.circle(image, (smoothed_left_nostril[0], smoothed_left_nostril[1]), 5, (255, 0, 0), -1)
        cv2.circle(image, (smoothed_right_nostril[0], smoothed_right_nostril[1]), 5, (255, 0, 0), -1)
        cv2.putText(image, f"{left_nostril_temp:.1f}°C", (smoothed_left_nostril[0] + 10, smoothed_left_nostril[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(image, f"{right_nostril_temp:.1f}°C", (smoothed_right_nostril[0] + 10, smoothed_right_nostril[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Display average nose temperature near the mouth or at a central position
        cv2.putText(image, f"Avg Nose Temp: {avg_nose_temperature:.1f}°C", (mouth_center_x, mouth_center_y - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Draw circle on the mouth for additional tracking
        cv2.circle(image, (mouth_center_x, mouth_center_y), 10, (0, 255, 255), -1)
        mouth_roi = gray[mouth_center_y - 5:mouth_center_y + 5, mouth_center_x - 10:mouth_center_x + 10]
        avg_intensity_mouth = np.mean(mouth_roi)
        mouth_temperature = pixel_to_temperature(avg_intensity_mouth)
        cv2.putText(image, f"{mouth_temperature:.1f}°C", (mouth_center_x + 15, mouth_center_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    return image


def display_frames(face_detector_algorithm="dlib", delay=0.05):
    cv2.namedWindow('Thermal Display', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Thermal Display', 640, 480)

    while True:
        if frame_queue:
            image_data = frame_queue.popleft()
            normalized_image = cv2.normalize(image_data, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            colored_image = cv2.applyColorMap(normalized_image, cv2.COLORMAP_INFERNO)

            # Detect and display with chosen algorithm
            marked_image = detect_face_and_roi(colored_image, algorithm=face_detector_algorithm)

            # Display the marked image
            cv2.imshow('Thermal Display', marked_image)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):  # Press 'q' to quit
                break

            time.sleep(delay)

    cv2.destroyAllWindows()
