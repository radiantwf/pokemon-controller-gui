import platform
import subprocess
import re
import imageio_ffmpeg


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
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        system = platform.system()
        
        try:
            if system == 'Darwin':
                # macOS: ffmpeg -f avfoundation -list_devices true -i ""
                cmd = [ffmpeg_exe, '-f', 'avfoundation', '-list_devices', 'true', '-i', '']
                result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, encoding='utf-8')
                lines = result.stderr.split('\n')
                # Parse stderr
                # [AVFoundation indev @ ...] AVFoundation video devices:
                # [AVFoundation indev @ ...] [0] FaceTime HD Camera
                # [AVFoundation indev @ ...] [1] Capture
                is_video = False
                for line in lines:
                    if "AVFoundation video devices:" in line:
                        is_video = True
                        continue
                    if "AVFoundation audio devices:" in line:
                        break
                    if is_video:
                        match = re.search(r'\[(\d+)\] (.+)', line)
                        if match:
                            dev_id = match.group(1)
                            name = match.group(2).strip()
                            # 默认支持 1080P 60FPS
                            cameras.append(CameraDevice(dev_id, name, 1920, 1080, None, 30, 60))
                            
            elif system == 'Windows':
                # Windows: ffmpeg -list_devices true -f dshow -i dummy
                cmd = [ffmpeg_exe, '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy']
                result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
                lines = result.stderr.split('\n')
                # Parse stderr
                # [dshow @ ...] DirectShow video devices (some may be both video and audio devices)
                # [dshow @ ...]  "Integrated Camera"
                is_video = False
                for line in lines:
                    if "DirectShow video devices" in line:
                        is_video = True
                        continue
                    if "DirectShow audio devices" in line:
                        break
                    if is_video:
                        match = re.search(r'\"(.+?)\"', line)
                        if match:
                            name = match.group(1)
                            # Windows dshow use video="name"
                            cameras.append(CameraDevice(f"video={name}", name, 1920, 1080, None, 30, 60))
        except Exception as e:
            print(f"Error listing devices with ffmpeg: {e}")
            
        return cameras
