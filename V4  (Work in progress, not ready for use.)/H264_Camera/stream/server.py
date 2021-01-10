import tornado.web, tornado.ioloop, tornado.websocket  
from picamera import PiCamera, PiVideoFrameType
from string import Template
import io, os, socket
import cv2
import numpy as np

# start configuration
serverPort = 8000
delayed_seconds = 5

camera = PiCamera(sensor_mode=4, resolution='1296x972', framerate=15)
camera.vflip = False
camera.hflip = False
camera.video_denoise = True

recordingOptions = {
    'format' : 'h264',
    #'bitrate' : 25000000,
    'quality' : 25,
    'profile' : 'high',
    'level' : '4.2',
    'intra_period' : 15,
    'intra_refresh' : 'both',
    'inline_headers' : True,
    'sps_timing' : True
}
# end configuration

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 0))
serverIp = s.getsockname()[0]

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

def getFile(filePath):
    file = open(filePath,'r')
    content = file.read()
    file.close()
    return content

def templatize(content, replacements):
    tmpl = Template(content)
    return tmpl.substitute(replacements)

appHtml = templatize(getFile('index.html'), {'ip':serverIp, 'port':serverPort, 'fps':camera.framerate})
delayed_appHtml = templatize(getFile('delayed_index.html'), {'ip':serverIp, 'port':serverPort, 'fps':camera.framerate})
appJs = getFile('jmuxer.min.js')

class StreamBuffer(object):
    def __init__(self,camera):
        self.frameTypes = PiVideoFrameType()
        self.loop = None
        self.buffer = io.BytesIO()
        self.camera = camera
        self.frame = None

    def setLoop(self, loop):
        self.loop = loop

    def write(self, buf):
        if self.camera.frame.complete and self.camera.frame.frame_type != self.frameTypes.sps_header:
            self.buffer.write(buf)
            self.frame = self.buffer.getvalue()
            if self.loop is not None and wsHandler.hasConnections():
                self.loop.add_callback(callback=wsHandler.broadcast, message=self.frame)
            if self.loop is not None and delayedwsHandler.hasConnections():
                self.loop.add_callback(callback=delayedwsHandler.broadcast, message=self.frame)
            self.buffer.seek(0)
            self.buffer.truncate()
        else:
            self.buffer.write(buf)


class DetectionBuffer(object):
    def __init__(self):
        self.buffer = io.BytesIO()
        self.previous_frame = b''
        self.current_frame = b''

    def convert_frame_data_to_opencv_frame(self, frame_data):
        data = np.fromstring(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(data, 1)
        return frame

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame
            self.buffer.truncate()
            read_frame_data = self.buffer.getvalue()
            if read_frame_data != b'':
                self.previous_frame = self.current_frame
                self.current_frame = self.convert_frame_data_to_opencv_frame(read_frame_data)
                if self.previous_frame != b'' and self.current_frame != b'':
                    self.detect_motion()
            self.buffer.seek(0)

        return self.buffer.write(buf)

    def detect_motion(self):
        blur = (5, 5)
        # convert the previous frame to grey scale and apply blur.
        start_frame = cv2.cvtColor(self.previous_frame, cv2.COLOR_BGR2GRAY)
        start_frame = cv2.GaussianBlur(start_frame, blur, 0)

        # convert the current frame to grey scale and apply blur.
        next_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2GRAY)
        next_frame = cv2.GaussianBlur(next_frame, blur, 0)

        # Calculate the difference between the current and previous frame.
        frame_difference = cv2.absdiff(next_frame, start_frame)
        thresh = cv2.threshold(frame_difference, 25, 255, cv2.THRESH_BINARY)[1]

        # Start recording when the difference between the frames is too big.
        if thresh.sum() > 100:
            print("Movement detected!")
            #self.recorder.report_motion()


class wsHandler(tornado.websocket.WebSocketHandler):
    connections = []

    def open(self):
        self.connections.append(self)

    def on_close(self):
        self.connections.remove(self)

    def on_message(self, message):
        pass

    @classmethod
    def hasConnections(cl):
        if len(cl.connections) == 0:
            return False
        return True

    @classmethod
    async def broadcast(cl, message):
        for connection in cl.connections:
            try:
                await connection.write_message(message, True)
            except tornado.websocket.WebSocketClosedError:
                pass
            except tornado.iostream.StreamClosedError:
                pass

class delayedwsHandler(tornado.websocket.WebSocketHandler):
    connections = []
    messages = []

    def open(self):
        self.connections.append(self)

    def on_close(self):
        self.connections.remove(self)

    def on_message(self, message):
        pass

    @classmethod
    def hasConnections(cl):
        if len(cl.connections) == 0:
            return False
        return True

    @classmethod
    async def broadcast(cl, message):
        if len(cl.messages) <= delayed_seconds * camera.framerate:
            cl.messages.append(message)
        else:
            del cl.messages[0] # Remove the oldest message
            cl.messages.append(message) # Add the new message.

        for connection in cl.connections:
            try:
                await connection.write_message(cl.messages[0], True) # Display the delayed message.
            except tornado.websocket.WebSocketClosedError:
                pass
            except tornado.iostream.StreamClosedError:
                pass


class htmlHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(appHtml)

class delayedhtmlHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(delayed_appHtml)

class jsHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(appJs)

requestHandlers = [
    (r"/ws/", wsHandler),
    (r"/delayed_ws/", delayedwsHandler),
    (r"/", htmlHandler),
    (r"/delayed/", delayedhtmlHandler),
    (r"/jmuxer.min.js", jsHandler),
    (r"/delayed/jmuxer.min.js", jsHandler)
]

try:
    streamBuffer = StreamBuffer(camera)
    detectionBuffer = DetectionBuffer()
    camera.start_recording(streamBuffer, **recordingOptions)
    camera.start_recording(detectionBuffer, splitter_port=2, resize=(80, 45), format='mjpeg')
    application = tornado.web.Application(requestHandlers)
    application.listen(serverPort)
    loop = tornado.ioloop.IOLoop.current()
    streamBuffer.setLoop(loop)
    loop.start()
except KeyboardInterrupt:
    camera.stop_recording()
    camera.close()
    loop.stop()
