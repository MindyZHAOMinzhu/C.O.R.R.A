import PySpin
import threading
from camera_config import configure_camera_for_thermal
from frame_capture import start_frame_capture, capture_event
from display import display_frames
import dlib

def main():
    # Initialize the camera system
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    camera = cam_list[0] if cam_list.GetSize() > 0 else None

    if camera is None:
        print("No camera detected.")
        return

    camera.Init()
    
    # Set camera to thermal mode
    if not configure_camera_for_thermal(camera):
        camera.DeInit()
        return

    # Start the acquisition to avoid the stream error
    camera.BeginAcquisition()

    # Start frame capture in a separate thread
    capture_thread = threading.Thread(target=start_frame_capture, args=(camera,))
    capture_thread.daemon = True
    capture_thread.start()

    # Display frames with overlays and real-time plotting
    display_frames(dlib.get_frontal_face_detector())

    # Signal the capture thread to stop and wait for it to finish
    capture_event.set()  # Signal the capture thread to stop
    capture_thread.join()  # Wait for the capture thread to finish

    # Clean up
    camera.EndAcquisition()
    camera.DeInit()
    del camera
    cam_list.Clear()
    system.ReleaseInstance()

if __name__ == '__main__':
    main()
