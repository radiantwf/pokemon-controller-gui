import cv2

background_subtractor_list: list = [None, None, None]


def cv_process_init(id: int):
    try:
        global background_subtractor_list
        background_subtractor_list[id-1] = [None]
    except:
        pass


def cv_process_decorator_copy_frame(func):
    def wrapper(*args, **kwargs):
        src_frame = args[1]
        dst_frame = src_frame.copy()
        return func(args[0], dst_frame)
    return wrapper


def cv_process_decorator_bgr2gray(func):
    def wrapper(*args, **kwargs):
        src_frame = args[1]
        dst_frame = cv2.cvtColor(src_frame, cv2.COLOR_BGR2GRAY)
        return func(args[0], dst_frame)
    return wrapper


def cv_process_decorator_background_subtract_MOG(func):
    def wrapper(*args, **kwargs):
        global background_subtractor_list
        background_subtractor = background_subtractor_list[args[0]-1]
        if background_subtractor is None:
            background_subtractor = cv2.bgsegm.createBackgroundSubtractorMOG()
            background_subtractor_list[args[0]-1] = background_subtractor
        src_frame = args[1]
        dst_frame = background_subtractor.apply(src_frame)
        return func(args[0], dst_frame)
    return wrapper


def cv_process_decorator_background_subtract_GMG(func):
    def wrapper(*args, **kwargs):
        global background_subtractor_list
        background_subtractor = background_subtractor_list[args[0]-1]
        if background_subtractor is None:
            background_subtractor = cv2.bgsegm.createBackgroundSubtractorGMG()
            background_subtractor_list[args[0]-1] = background_subtractor
        src_frame = args[1]
        dst_frame = background_subtractor.apply(src_frame)
        return func(args[0], dst_frame)
    return wrapper


def cv_process_decorator_background_subtract_MOG2(func):
    def wrapper(*args, **kwargs):
        global background_subtractor_list
        background_subtractor = background_subtractor_list[args[0]-1]
        if background_subtractor is None:
            background_subtractor = cv2.createBackgroundSubtractorMOG2(
                history=10, detectShadows=False)
            background_subtractor_list[args[0]-1] = background_subtractor
        src_frame = args[1]
        dst_frame = background_subtractor.apply(src_frame)
        return func(args[0], dst_frame)
    return wrapper


@cv_process_decorator_copy_frame
def cv_process(id, frame):
    return frame


@cv_process_decorator_copy_frame
def cv_process_1(id, frame):
    return frame


@cv_process_decorator_bgr2gray
def cv_process_2(id, frame):
    return frame


@cv_process_decorator_background_subtract_MOG
def cv_process_3(id, frame):
    return frame
