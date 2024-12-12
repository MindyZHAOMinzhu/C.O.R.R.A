import cv2
import dlib

# Initialize various detectors
dlib_detector = dlib.get_frontal_face_detector()
opencv_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def detect_with_dlib(gray_image):
    faces = dlib_detector(gray_image)
    return [(face.left(), face.top(), face.width(), face.height()) for face in faces]

def detect_with_opencv(gray_image):
    faces = opencv_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return faces
