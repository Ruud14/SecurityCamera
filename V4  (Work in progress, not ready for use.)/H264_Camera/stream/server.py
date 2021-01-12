import tornado.web, tornado.ioloop, tornado.websocket  
from picamera import PiCamera, PiVideoFrameType
from string import Template
import socket
from websockethandler import WebSocketHandler
from buffers import StreamBuffer, DetectionBuffer
import time


def get_file(filePath):
    file = open(filePath, 'r')
    content = file.read()
    file.close()
    return content


def templatize(content, replacements):
    template = Template(content)
    return template.substitute(replacements)


appHtml = None


class HTMLHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(appHtml)


class JSHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(get_file('jmuxer.min.js'))


class Streamer:
    def __init__(self, motion_detector, streaming_resolution='1296x972', detection_resolution=(80,46), fps=15, port=8000, vflip=False, hflip=False, denoise=True):
        self.motion_detector = motion_detector
        self.server_port = port
        self.server_ip = self._socket_setup()
        self.streaming_resolution = streaming_resolution
        self.detection_resolution = detection_resolution
        self.fps = fps
        self.camera = PiCamera(sensor_mode=4, resolution=streaming_resolution, framerate=fps)
        self.camera.vflip = vflip
        self.camera.hflip = hflip
        self.delayed_seconds = 5
        self.camera.video_denoise = denoise
        self.request_handlers = None
        self.detection_buffer = None

    # Sets up the request handlers for tornado.
    def _setup_request_handlers(self):
        self.request_handlers = [
            (r"/ws/", WebSocketHandler),
            (r"/", HTMLHandler),
            (r"/jmuxer.min.js", JSHandler),
            (r"/delayed/jmuxer.min.js", JSHandler)
        ]
        global appHtml
        appHtml = templatize(get_file('index.html'),
                                   {'ip': self.server_ip, 'port': self.server_port, 'fps': self.fps})

    # Set up the web socket.
    def _socket_setup(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 0))
        serverIp = s.getsockname()[0]
        return serverIp

    # Start streaming.
    def start(self):
        self._setup_request_handlers()

        try:
            # Create the stream and detection buffers.
            stream_buffer = StreamBuffer(self.camera, self.fps,self.delayed_seconds)
            self.detection_buffer = DetectionBuffer(self.motion_detector)

            # Start sending frames to the streaming thread.
            self.camera.start_recording(stream_buffer, **{
                    'format' : 'h264',
                    #'bitrate' : 25000000,
                    'quality' : 25,
                    'profile' : 'high',
                    'level' : '4.2',
                    'intra_period' : 15,
                    'intra_refresh' : 'both',
                    'inline_headers' : True,
                    'sps_timing' : True
                })
            # Start sending frames to the detection thread.
            self.camera.start_recording(self.detection_buffer, splitter_port=2, resize=self.detection_resolution, format='mjpeg')

            # Create and loop the tornado application.
            application = tornado.web.Application(self.request_handlers)
            application.listen(self.server_port)
            loop = tornado.ioloop.IOLoop.current()
            stream_buffer.setLoop(loop)
            loop.start()
        except KeyboardInterrupt:
            self.camera.stop_recording()
            self.camera.close()
            loop.stop()

    # return the detection_buffer to the detector.
    def get_detection_buffer(self):
        while not self.detection_buffer:
            time.sleep(0.01)
        return self.detection_buffer
