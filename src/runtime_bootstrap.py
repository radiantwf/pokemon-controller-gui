import contextlib
import importlib
import os
import sys


@contextlib.contextmanager
def suppress_native_stderr():
    """Temporarily silence fd=2 to hide macOS duplicate-SDL objc warnings."""
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    saved_stderr_fd = os.dup(2)

    try:
        os.dup2(devnull_fd, 2)
        yield
    finally:
        os.dup2(saved_stderr_fd, 2)
        os.close(saved_stderr_fd)
        os.close(devnull_fd)


def preload_native_modules():
    if sys.platform != "darwin":
        return

    with suppress_native_stderr():
        importlib.import_module("pygame")
        importlib.import_module("cv2")


def configure_qt_logging():
    rules = os.environ.get("QT_LOGGING_RULES", "")
    ffmpeg_rule = "qt.multimedia.ffmpeg=false"
    if ffmpeg_rule in rules.split(";"):
        return

    if rules:
        os.environ["QT_LOGGING_RULES"] = f"{rules};{ffmpeg_rule}"
    else:
        os.environ["QT_LOGGING_RULES"] = ffmpeg_rule


def bootstrap_runtime():
    configure_qt_logging()
    preload_native_modules()
