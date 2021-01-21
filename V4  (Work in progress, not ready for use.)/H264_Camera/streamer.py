import tornado.web, tornado.ioloop, tornado.websocket
from websockethandler import WebSocketHandler
from buffers import StreamBuffer
from string import Template
import socket
import os


# Returns the full file path of the script.
def get_exec_dir():
    abspath = os.path.abspath(__file__)
    directory_name = os.path.dirname(abspath)
    return directory_name


# function the get the content of a file.
def get_file_content(relative_file_path):
    directory_name = get_exec_dir()
    file = open(os.path.join(directory_name, relative_file_path), 'r')
    content = file.read()
    file.close()
    return content


# Class that is responsible for streaming the camera footage to the web-page.
class Streamer:
    def __init__(self, camera, h264_args, streaming_resolution='1296x972', fps=15, port=8000):
        self.camera = camera
        self.h264_args = h264_args
        self.streaming_resolution = streaming_resolution
        self.fps = fps
        self.server_port = port
        self.server_ip = self._socket_setup()

        self.request_handlers = None

    # Set up the request handlers for tornado.
    def _setup_request_handlers(self):
        parent = self

        # Handler for the javascript of the streaming page.
        class JSHandler(tornado.web.RequestHandler):
            def get(self):
                self.write(Template(get_file_content('web/index.js')).substitute({'ip': parent.server_ip, 'port': parent.server_port, 'fps': parent.fps}))

        self.request_handlers = [
            (r"/ws/", WebSocketHandler),
            (r"/index.js", JSHandler),
            (r"/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(get_exec_dir(), "web/static/")})
        ]

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
            stream_buffer = StreamBuffer(self.camera)

            # Start sending frames to the streaming thread.
            self.camera.start_recording(stream_buffer, splitter_port=2, **self.h264_args, resize=self.streaming_resolution)

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
