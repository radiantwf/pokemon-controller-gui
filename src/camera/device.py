from PySide6.QtMultimedia import QMediaDevices, QVideoFrameFormat


class CameraDevice(object):
    def __init__(self, id, name, width, height, pixelFormat, min_fps, max_fps):
        self._id = id
        self._name = name
        self._width = width
        self._height = height
        self._pixelFormat = pixelFormat
        self._min_fps = min_fps
        self._max_fps = max_fps
        self._fps = max_fps

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def fps(self):
        return self._fps

    @property
    def min_fps(self):
        return self._min_fps

    @property
    def max_fps(self):
        return self._max_fps

    def setFps(self, fps: int):
        if fps < self._min_fps:
            self._fps = self._min_fps
        elif fps > self._max_fps:
            self._fps = self._max_fps
        else:
            self._fps = fps

        # 列出当前设备的所有摄像头
    @staticmethod
    def list_device():
        cameras = []
        inputs = QMediaDevices.videoInputs()
        inputs.sort(key=lambda x: x.id().data())
        for camera_info in inputs:
            name = camera_info.description()
            id = camera_info.id().data().decode()
            # 获取最适合的分辨率与帧数
            width = 99999
            height = 0
            max_fps = 0
            min_fps = 0
            pixelFormat = None
            for format in camera_info.videoFormats():
                resolution = format.resolution()
                maxFps = format.maxFrameRate()
                if resolution.width() > 1920 or resolution.width() < 720:
                    continue
                if resolution.height() != resolution.width() / 16 * 9:
                    continue
                if maxFps > 61 or maxFps < 29:
                    continue
                if resolution.width() > width:
                    continue
                if maxFps < max_fps:
                    continue
                if format.pixelFormat() == QVideoFrameFormat.PixelFormat.Format_NV12 and (pixelFormat is not None and pixelFormat != QVideoFrameFormat.PixelFormat.Format_NV12):
                    continue
                width = resolution.width()
                height = resolution.height()
                max_fps = maxFps
                min_fps = format.minFrameRate()
                pixelFormat = format.pixelFormat()
            if width == 99999:
                continue
            cameras.append(CameraDevice(id, name, width, height,
                           pixelFormat, min_fps, max_fps))
        return cameras
