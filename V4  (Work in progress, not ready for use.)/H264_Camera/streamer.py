import tornado.web, tornado.ioloop, tornado.websocket
from string import Template
import socket
from websockethandler import WebSocketHandler
from buffers import StreamBuffer
import time


# function the get the content of a file.
def get_file(filePath):
    file = open(filePath, 'r')
    content = file.read()
    file.close()
    return content


# Function to substitute content into the template.
def templatize(content, replacements):
    template = Template(content)
    return template.substitute(replacements)


appHtml = None


# Handler for the html of the streaming page.
class HTMLHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(appHtml)


# Handler for the javascript of the streaming page.
class JSHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(get_file('jmuxer.min.js'))


# Class that is responsible for streaming the camera footage to the web-page.
class Streamer:
    def __init__(self, camera, h264_args, streaming_resolution='1296x972', fps=15, port=8000):
        self.camera = camera
        self.h264_args = h264_args
        self.server_port = port
        self.server_ip = self._socket_setup()
        self.streaming_resolution = streaming_resolution
        self.fps = fps

        self.request_handlers = None
        self.detection_buffer = None

    # Set up the request handlers for tornado.
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
        server_ip = s.getsockname()[0]
        return server_ip

    # Start streaming.
    def start(self):
        self._setup_request_handlers()
        try:
            # Create the stream and detection buffers.
            stream_buffer = StreamBuffer(self.camera, self.fps)

            # Start sending frames to the streaming thread.
            self.camera.start_recording(stream_buffer, splitter_port=2, **self.h264_args)

            # Create and loop the tornado application.
            application = tornado.web.Application(self.request_handlers)
            application.listen(self.server_port)
            loop = tornado.ioloop.IOLoop.current()
            stream_buffer.setLoop(loop)
            print("Streamer started on http://{}:{}".format(self.server_ip, self.server_port))
            loop.start()

        except KeyboardInterrupt:
            self.camera.stop_recording() #TODO: move this to main.
            self.camera.close()
            loop.stop()

    # return the detection_buffer to the detector.
    def get_detection_buffer(self):
        while not self.detection_buffer:
            time.sleep(0.01)
        return self.detection_buffer
