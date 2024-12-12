import cv2
import dlib

# Initialize face detectors
dlib_detector = dlib.get_frontal_face_detector()
haar_cascade_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def detect_face_and_roi(thermal_image, algorithm="dlib"):
    """
    Detects the face and marks ROIs for nose and mouth.

    :param thermal_image: The input image in thermal mode
    :param algorithm: The face detection algorithm to use ("dlib" or "haar")
    :return: thermal_image with ROIs marked, or the original image if no face detected
    """
    if algorithm == "dlib":
        faces = dlib_detector(thermal_image, 1)
        for face in faces:
            x, y, w, h = (face.left(), face.top(), face.width(), face.height())
            cv2.rectangle(thermal_image, (x, y), (x + w, y + h), (255, 0, 0), 2)

            # Define ROIs
            nose_roi = thermal_image[y + int(h * 0.4): y + int(h * 0.6), x + int(w * 0.3): x + int(w * 0.7)]
            mouth_roi = thermal_image[y + int(h * 0.6): y + int(h * 0.8), x + int(w * 0.3): x + int(w * 0.7)]

            # Draw rectangles for the ROIs
            cv2.rectangle(thermal_image, (x + int(w * 0.3), y + int(h * 0.4)), 
                          (x + int(w * 0.7), y + int(h * 0.6)), (0, 255, 0), 1)
            cv2.rectangle(thermal_image, (x + int(w * 0.3), y + int(h * 0.6)), 
                          (x + int(w * 0.7), y + int(h * 0.8)), (0, 0, 255), 1)
            return thermal_image

    elif algorithm == "haar":
        # Convert to grayscale as Haar Cascade expects grayscale images
        gray_image = cv2.cvtColor(thermal_image, cv2.COLOR_BGR2GRAY)
        faces = haar_cascade_detector.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        for (x, y, w, h) in faces:
            cv2.rectangle(thermal_image, (x, y), (x + w, y + h), (255, 0, 0), 2)

            # Define ROIs
            nose_roi = thermal_image[y + int(h * 0.4): y + int(h * 0.6), x + int(w * 0.3): x + int(w * 0.7)]
            mouth_roi = thermal_image[y + int(h * 0.6): y + int(h * 0.8), x + int(w * 0.3): x + int(w * 0.7)]

            # Draw rectangles for the ROIs
            cv2.rectangle(thermal_image, (x + int(w * 0.3), y + int(h * 0.4)), 
                          (x + int(w * 0.7), y + int(h * 0.6)), (0, 255, 0), 1)
            cv2.rectangle(thermal_image, (x + int(w * 0.3), y + int(h * 0.6)), 
                          (x + int(w * 0.7), y + int(h * 0.8)), (0, 0, 255), 1)
            return thermal_image

    # If no face is detected, return the original image without modifications
    return thermal_image
