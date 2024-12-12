import PySpin

class FLIRCamera:
    def __init__(self):
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        self.cam = self.cam_list.GetByIndex(0)
        self.cam.Init()
        self.cam.BeginAcquisition()

    def acquire_frame(self):
        image_result = self.cam.GetNextImage()
        if image_result.IsIncomplete():
            print("Image incomplete with image status %d ..." % image_result.GetImageStatus())
            return None
        else:
            image_data = image_result.GetNDArray()
            image_result.Release()
            return image_data

    def release(self):
        self.cam.EndAcquisition()
        self.cam.DeInit()
        self.cam_list.Clear()
        self.system.ReleaseInstance()