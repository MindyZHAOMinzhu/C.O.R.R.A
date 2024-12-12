import cv2

def detect_face_and_roi(thermal_image, face_detector):
    faces = face_detector(thermal_image, 1)
    for face in faces:
        x, y, w, h = (face.left(), face.top(), face.width(), face.height())
        cv2.rectangle(thermal_image, (x, y), (x + w, y + h), (255, 0, 0), 2)

        nose_roi = thermal_image[y + int(h * 0.4): y + int(h * 0.6), x + int(w * 0.3): x + int(w * 0.7)]
        mouth_roi = thermal_image[y + int(h * 0.6): y + int(h * 0.8), x + int(w * 0.3): x + int(w * 0.7)]

        cv2.rectangle(thermal_image, (x + int(w * 0.3), y + int(h * 0.4)), 
                      (x + int(w * 0.7), y + int(h * 0.6)), (0, 255, 0), 1)
        cv2.rectangle(thermal_image, (x + int(w * 0.3), y + int(h * 0.8)), 
                      (x + int(w * 0.7), y + int(h * 0.8)), (0, 0, 255), 1)
        
        return nose_roi, mouth_roi, (x, y)  # (x, y) for overlay position
    return None, None, None
