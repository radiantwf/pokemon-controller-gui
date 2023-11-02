class Frame(object):
    def __init__(self, width, height, channels, format, bytes):
        self._width: int = int(width)
        self._height: int = int(height)
        self._channels: int = int(channels)
        self._format = format
        self._bytes = bytes

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
