import cv2
import numpy


class Frame(object):
    def __init__(self, mat: cv2.Mat):
        # 获取宽度和高度
        self._height, self._width = mat.shape[:2]

        # 获取通道数
        if len(mat.shape) == 3:
            self._channels = mat.shape[2]
        else:
            self._channels = 1

        # 获取格式
        if mat.dtype == numpy.uint8:
            if len(mat.shape) == 3:
                if mat.shape[2] == 3:
                    self._format = cv2.CAP_PVAPI_PIXELFORMAT_BGR24
                else:
                    raise ValueError("Unsupported channels")
            else:
                self._format = cv2.CAP_PVAPI_PIXELFORMAT_MONO8
        else:
            raise ValueError("Unsupported dtype")

        self._bytes = mat.tobytes()

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def channels(self):
        return self._channels

    @property
    def format(self):
        return self._format

    def bytes(self):
        return self._bytes
