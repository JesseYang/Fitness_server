import pickle
import cv2
import numpy as np
import uuid
from enum import Enum

from queue import Queue
from threading import Thread
from threading import Lock
from threading import Event

from detect import DetectThread
from capture import CaptureThread
from visualize import VisualizeGUI
from audio import AudioThread

from cfgs.config import cfg

from actions import *

if __name__ == "__main__":

    capture_queue = Queue(maxsize=cfg.max_queue_len)
    result_queue = Queue(maxsize=cfg.max_queue_len)
    enable_capture = Event()
    enable_predict = Event()

    capture_thread = CaptureThread(capture_queue, enable_capture)
    capture_thread.start()

    detect_thread = DetectThread(capture_queue, result_queue, enable_capture, enable_predict)
    detect_thread.start()

    audio_thread = AudioThread()
    audio_thread.start()

    output_path = "output_%s.mp4" % str(uuid.uuid4())
    deep_squat = DeepSquat()
    back_squat = BackSquat()

    visualize_gui = VisualizeGUI(result_queue, audio_thread, enable_predict, back_squat, output_path=output_path)

