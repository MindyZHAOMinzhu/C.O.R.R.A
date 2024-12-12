from flask import Flask, render_template, Response
from flask_socketio import SocketIO
import cv2
import mediapipe as mp
import numpy as np
import time
import secrets

app = Flask(__name__)
secret_key = secrets.token_urlsafe(24)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

mp_face_detection = mp.solutions.face_detection
mp_face_mesh = mp.solutions.face_mesh
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=5, min_detection_confidence=0.5)

zoom_factor = 2.45
offset_y_inches = -0.2
offset_x_inches = 0.8
dpi = 30
offset_y_pixels = int(offset_y_inches * dpi)
offset_x_pixels = int(offset_x_inches * dpi)

last_extraction_time = time.time()

try:
    regular_cam = cv2.VideoCapture(1)
    thermal_cam = cv2.VideoCapture(2)
except Exception as e:
    print(f"Error initializing cameras: {e}")

class Person:
    def __init__(self, id, bbox):
        self.id = id
        self.bbox = bbox
        self.temperatures = []
        self.last_detected = time.time()
        self.alarm_on = False
        self.alarm_start_time = None
        self.previous_avg_temp = None
        self.death_detected_count = 0  # Track consecutive death detections

    def update_bbox(self, bbox):
        self.bbox = bbox
        self.last_detected = time.time()

    def add_temperature(self, temp):
        self.temperatures.append(temp)
        if len(self.temperatures) > 5:
            self.temperatures.pop(0)
    
    def check_death(self):
         if len(self.temperatures) >= 2: 
            if abs(self.temperatures[-2] - self.temperatures[-1]) <= 0.15:
                    self.death_detected_count += 1
                    if self.death_detected_count >= 6:  # Require two consecutive detections
                        self.death_detected_count = 0 
                        return True
            else:
                self.death_detected_count = 0  # Reset count if temperature data is incomplete
            return False

persons = []
next_person_id = 0

def pixel_to_temperature(pixel_value, min_temp=20, max_temp=100):
    return min_temp + (pixel_value / 255) * (max_temp - min_temp)

def crop_above(frame, zoom_factor, offset_y_pixels, offset_x_pixels):
    height, width = frame.shape[:2]
    new_height, new_width = int(height / zoom_factor), int(width / zoom_factor)
    
    # Adjust the starting row to account for the vertical offset due to camera position
    start_row = int((height - new_height) / 2) - offset_y_pixels
    start_row = max(0, start_row)  # Ensure the start row is not negative
    end_row = start_row + new_height
    if end_row > height:
        end_row = height
        start_row = height - new_height

    # Adjust the starting column to account for the horizontal offset
    start_col = int((width - new_width) / 2) - offset_x_pixels
    start_col = max(0, start_col)  # Ensure the start column is not negative
    end_col = start_col + new_width
    if end_col > width:
        end_col = width
        start_col = width - new_width

    return frame[start_row:end_row, start_col:end_col]

def get_person_id(bbox):
    global next_person_id
    x, y, w, h = bbox
    for person in persons:
        px, py, pw, ph = person.bbox
        if abs(x - px) < 75 and abs(y - py) < 75:
            return person.id
    return None

def generate_frames():
    global last_extraction_time, flash_counter, persons, next_person_id
    while True:
        current_time = time.time()
        ret1, regular_frame = regular_cam.read()
        ret2, thermal_frame = thermal_cam.read()

        if not ret1 or not ret2:
            print("failed to capture frames")
            break

        # Crop the regular camera frame with vertical and horizontal offsets
        zoomed_frame = crop_above(regular_frame, zoom_factor, offset_y_pixels, offset_x_pixels)
        
        # Resize the cropped frame to match the thermal frame size
        thermal_height, thermal_width = thermal_frame.shape[:2]
        zoomed_frame_resized = cv2.resize(zoomed_frame, (thermal_width, thermal_height))

        if current_time - last_extraction_time >= 1:
            last_extraction_time = current_time

            rgb_frame = cv2.cvtColor(zoomed_frame_resized, cv2.COLOR_BGR2RGB)
            results = face_detection.process(rgb_frame)

            if results.detections:
                for detection in results.detections:
                    bboxC = detection.location_data.relative_bounding_box
                    ih, iw, _ = rgb_frame.shape
                    x, y, w, h = int(bboxC.xmin * iw), int(bboxC.ymin * ih), int(bboxC.width * iw), int(bboxC.height * ih)
                    person_id = get_person_id((x, y, w, h))
                    if person_id is None:
                        person_id = next_person_id
                        persons.append(Person(person_id, (x, y, w, h)))
                        next_person_id += 1
                    person = [p for p in persons if p.id == person_id][0]
                    person.update_bbox((x, y, w, h))

                    face_results = face_mesh.process(rgb_frame)
                    if face_results.multi_face_landmarks:
                        for face_landmarks in face_results.multi_face_landmarks:
                            nose_tip = face_landmarks.landmark[1]
                            nose_center_x = int(nose_tip.x * iw)
                            nose_center_y = int(nose_tip.y * ih)

                            cv2.rectangle(zoomed_frame_resized, (x, y), (x + w, y + h), (255, 0, 0), 2)
                            cv2.circle(zoomed_frame_resized, (nose_center_x, nose_center_y), 5, (0, 0, 255), -1)

                            if len(thermal_frame.shape) == 3 and thermal_frame.shape[2] == 3:
                                thermal_frame_gray = cv2.cvtColor(thermal_frame, cv2.COLOR_BGR2GRAY)
                            else:
                                thermal_frame_gray = thermal_frame

                            nose_temperature_pixel_value = thermal_frame_gray[nose_center_y, nose_center_x]
                            nose_temperature = pixel_to_temperature(nose_temperature_pixel_value, min_temp=17.2, max_temp=33.4)

                            person.add_temperature(nose_temperature)
                            if person.check_death():
                                socketio.emit('death_detected', {'person_id': person_id}, namespace='/')
                                persons = [] 
                                next_person_id = 0

                            print(f'Temperature at nose for person {person_id}: {nose_temperature:.2f} °C')
                            cv2.putText(zoomed_frame_resized, f'{nose_temperature:.2f} °C', (nose_center_x, nose_center_y - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                            
                

        persons = [person for person in persons if current_time - person.last_detected <= 10]

        ret, buffer = cv2.imencode('.jpg', zoomed_frame_resized)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/narcan_video')
def narcan_video():
    return render_template('preloaded_video.html')

@socketio.on('connect', namespace='/')
def test_connect():
    print('Client connected')

@socketio.on('test_client_to_server')
def handle_test_event(data):
    print('Client says:', data['message'])
    socketio.emit('test_server_to_client', {'message': 'Hello from server'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)