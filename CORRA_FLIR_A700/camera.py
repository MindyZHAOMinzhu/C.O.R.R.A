# Defining "FLIRCamera" class
# initialization and setup of the camera


# Usage Examples
# camera = FLIRCamera()  # Initialize the camera
# frame = camera.acquire_frame()  # Acquire a single frame (frame.shape [shape of the image NumPy array format])
# camera.release()  # Ensure proper cleanup

import PySpin

class FLIRCamera:
    # Initialization
    def __init__(self):
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        self.cam = self.cam_list.GetByIndex(0) # Selects the first camera in the list
        self.cam.Init() # Initializes the selected camera for use.
        self.cam.BeginAcquisition() # Starts the camera's image acquisition process, enabling frame capture.


3   def acquire_frame(self):
        image_result = self.cam.GetNextImage() # store captured the next image from the camera's acquisition stream
        
        # check if the image_result
        if image_result.IsIncomplete():
            print("Image incomplete with image status %d ..." % image_result.GetImageStatus())
            return None
        else: # if the image_result is complete
            image_data = image_result.GetNDArray() # converting image to NumPy array format for further analysis
            image_result.Release() # after converting this image to NumPy array, releasing the acquired image from the camera's memory
            return image_data

    def release(self): # for the camera, Cleanup
        self.cam.EndAcquisition() # Stops the camera's acquisition process.
        self.cam.DeInit()
        self.cam_list.Clear() # Clears the list of connected cameras
        self.system.ReleaseInstance()