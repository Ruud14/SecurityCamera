from server import Streamer
from detector import Detector
import os


def change_exec_dir():
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)


if __name__ == '__main__':
    change_exec_dir()
    detector = Detector()
    streamer = Streamer(detector)
    streamer.start()


