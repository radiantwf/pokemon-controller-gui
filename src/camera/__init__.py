import multiprocessing
import subprocess
import time
import platform
import numpy as np
import imageio_ffmpeg
import hashlib

from camera.device import CameraDevice
from datatype.frame import Frame

system = platform.system()


def run(camera_device: CameraDevice, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, recognition_frame_queue: multiprocessing.Queue):
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    width = camera_device.width
    height = camera_device.height
    fps = camera_device.fps
    dev_id = camera_device.id

    # Construct ffmpeg command
    cmd = [ffmpeg_exe, '-fflags', 'nobuffer', '-flags', 'low_delay']
    
    if system == 'Darwin':
        # macOS: -f avfoundation -framerate 30 -video_size 1920x1080 -i "0" ...
        cmd.extend(['-f', 'avfoundation'])
        cmd.extend(['-framerate', str(fps)])
        cmd.extend(['-video_size', f"{width}x{height}"])
        cmd.extend(['-i', dev_id])
    elif system == 'Windows':
        # Windows: -f dshow -rtbufsize 100M -framerate 30 -video_size 1920x1080 -i "video=Name" ...
        cmd.extend(['-f', 'dshow'])
        cmd.extend(['-rtbufsize', '100M'])
        cmd.extend(['-framerate', str(fps)])
        cmd.extend(['-video_size', f"{width}x{height}"])
        cmd.extend(['-i', dev_id])
    else:
        # Fallback or other OS not implemented fully yet
        print(f"Unsupported OS for ffmpeg camera capture: {system}")
        return

    # Output to stdout: raw video, bgr24 pixel format
    # Force output scaling to ensure we get expected buffer size even if input is different
    cmd.extend(['-vcodec', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f"{width}x{height}", '-an', '-sn', '-vsync', '0', '-f', 'rawvideo', '-'])

    process = None
    frame_size = width * height * 3
    frame_count = 0
    last_log_time = time.monotonic()
    last_log_count = 0
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        while not stop_event.is_set():
            if process.stdout is None:
                break
            buffer = bytearray(frame_size)
            view = memoryview(buffer)
            read_size = 0
            while read_size < frame_size and not stop_event.is_set():
                chunk = process.stdout.read(frame_size - read_size)
                if not chunk:
                    if process.poll() is not None:
                        break
                    time.sleep(0.001)
                    continue
                view[read_size:read_size + len(chunk)] = chunk
                read_size += len(chunk)
            if stop_event.is_set():
                break
            if read_size < frame_size:
                if process.poll() is not None:
                    print(f"FFmpeg process exited with code {process.returncode}")
                    break
                continue
            try:
                frame = np.frombuffer(buffer, dtype=np.uint8).reshape((height, width, 3))
            except Exception as e:
                print(f"Frame reshape error: {e}")
                continue
            send_frame = Frame(frame)
            frame_count += 1
            if not frame_queue.full():
                try:
                    frame_queue.put_nowait(send_frame)
                except:
                    pass
            if not recognition_frame_queue.full():
                try:
                    recognition_frame_queue.put_nowait(send_frame)
                except:
                    pass
            # now = time.monotonic()
            # elapsed = now - last_log_time
            # if elapsed >= 1.0:
            #     current_hash = hashlib.md5(buffer).hexdigest()
            #     fps = (frame_count - last_log_count) / elapsed
            #     print(f"camera pipe fps={fps:.1f} hash={current_hash[:12]} size={frame_size}")
            #     last_log_time = now
            #     last_log_count = frame_count

    except Exception as e:
        print(f"Camera capture error: {e}")
    finally:
        if process:
            process.terminate()
            try:
                process.wait(timeout=1)
            except:
                process.kill()
