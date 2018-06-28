from queue import Queue
from threading import Thread
from threading import Lock
from threading import Event

import time

import numpy as np
import cv2

from cfgs.config import cfg

class CaptureThread(Thread):
    def __init__(self, capture_queue, enable_capture, video_file=None):
        Thread.__init__(self)
        self.capture_queue = capture_queue
        self.enable_capture = enable_capture

        # do initialization, either camera (online) or from file
        self.from_camera = video_file == None
        self.cap = cv2.VideoCapture(cfg.cam_idx) if self.from_camera else cv2.VideoCapture(video_file)

    def run(self):
        frame_idx = 0
        save_frame_idx = 0
        while (True if self.from_camera == True else self.cap.isOpened()):
            self.enable_capture.wait()
            ret, frame = self.cap.read()
            
            frame_idx = (frame_idx + 1) % 1e5

            if frame_idx % int(30 / cfg.fps) == 0:
                continue

            
            scale = 0.8

            y_start = int((480 - 480 * scale) / 2)
            y_end = int((480 - 480 * scale) / 2 + 480 * scale)

            x_start = int(640 - 640 * scale)

            frame = frame[y_start:y_end, x_start:]

            if self.from_camera:
                frame = cv2.transpose(frame)
                frame = cv2.flip(frame, 1)
            if ret == False or (cfg.capture_frame_num > 0 and save_frame_idx >= cfg.capture_frame_num):
                self.capture_queue.put(np.zeros((0,0)))
                break

            save_frame_idx += 1

            self.capture_queue.put(frame)
