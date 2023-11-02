import sys


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


@singleton
class ConstClass(object):
    DisplayCameraWidth = 640
    DisplayCameraHeight = 360

    RecognizeVideoWidth = 960
    RecognizeVideoHeight = 540
    RecognizeVideoFps = 10

    def __init__(self):
        pass
