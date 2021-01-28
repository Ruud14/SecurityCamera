from .scripts.Cameras_Receiver import CameraReceiver
import os
from django.views.decorators import gzip
from django.http import HttpResponse
import os
from django.http import StreamingHttpResponse
from django.conf import settings

def gen(cam_number):
    while True:
        frame = cam.get_camera_frame_in_bytes(cam_number)
        if frame:
            yield(b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@gzip.gzip_page
def livefe(request,cam_number):
    cam_number=int(cam_number)
    if not cam_number <= cam.camera_count:
        return HttpResponse("This camera doesn't exist.")
    try:
        return StreamingHttpResponse(gen(cam_number), content_type="multipart/x-mixed-replace;boundary=frame")
    except:
        pass