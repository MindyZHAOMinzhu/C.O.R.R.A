import PySpin

def configure_camera_for_thermal(camera):
    nodemap = camera.GetNodeMap()
    pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode('PixelFormat'))
    if not PySpin.IsAvailable(pixel_format) or not PySpin.IsWritable(pixel_format):
        print("Unable to set Pixel Format to Mono16.")
        return False

    pixel_format_mono16 = pixel_format.GetEntryByName('Mono16')
    pixel_format.SetIntValue(pixel_format_mono16.GetValue())
    print("Pixel Format set to Mono16 for thermal imaging.")
    return True
