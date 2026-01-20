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

    RecognizeVideoWidth = 1920
    RecognizeVideoHeight = 1080
    RecognizeVideoFps = 10

    LogSocketPort = 39008
    ActionDisplaySocketPort = 39009
    _AF_UNIX_FlAG = True

    def __init__(self):
        pass

    @property
    def AF_UNIX_FLAG(self) -> bool:
        return self._AF_UNIX_FlAG and (sys.platform.startswith("linux") or sys.platform.startswith("darwin"))
