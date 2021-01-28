import tornado.web, tornado.ioloop, tornado.websocket
import socket
import os


# Checks there is internet connectivity.
def has_internet_connectivity(host="8.8.8.8", port=53):
    try:
        socket.socket().connect((host, port))
        return True
    except socket.error:
        print("No internet connectivity could be established. Trying again in a second.")
        return False


# function the get the content of a file.
def get_file_content(relative_file_path):
    directory_name = get_exec_dir()
    file = open(os.path.join(directory_name, relative_file_path), 'r')
    content = file.read()
    file.close()
    return content


# Returns the full file path of the script.
def get_exec_dir():
    abspath = os.path.abspath(__file__)
    directory_name = os.path.dirname(abspath)
    return directory_name


# WebSocket for streaming to the web page.
class WebSocketHandler(tornado.websocket.WebSocketHandler):
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
