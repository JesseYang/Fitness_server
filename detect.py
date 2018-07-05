from queue import Queue
from threading import Thread
from threading import Lock
from threading import Event
import pdb
import time
from actions import *

try:
    from .code_model.predict import *
    from .code_model.cfgs.config import cfg as model_cfg
except Exception:
    from code_model.predict import *
    from code_model.cfgs.config import cfg as model_cfg

from cfgs.config import cfg

def detect(img, predict_func, scale=0.25, draw_result=False):
    # print("0: %f" % time.time())
    h, w, _ = img.shape

    scale_img = cv2.resize(img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC) if scale != 1 else img
    scale_img_expanded = np.expand_dims(scale_img, axis=0)

    # scale_img_expanded = np.concatenate([scale_img_expanded, scale_img_expanded, scale_img_expanded, scale_img_expanded, scale_img_expanded, scale_img_expanded, scale_img_expanded, scale_img_expanded], axis=0)

    heatmap, paf = predict_func(scale_img_expanded)
    heatmap = cv2.resize(heatmap[0], (0,0), fx=model_cfg.stride, fy=model_cfg.stride, interpolation=cv2.INTER_CUBIC)

    peaks = []

    for part in range(model_cfg.ch_heats - 1):
        part_heatmap = heatmap[:, :, part]
        y, x = unravel_index(part_heatmap.argmax(), part_heatmap.shape)
        # for opencv to draw, the x is before y
        peaks.append((x, y, part_heatmap[y, x]))

    if draw_result == False:
        return peaks, scale_img
    else:
        canvas = np.copy(scale_img) # B,G,R order
        colors = [[255, 0, 0], [255, 85, 0], [255, 170, 0], [255, 255, 0], [170, 255, 0], [85, 255, 0], [0, 255, 0], \
                  [0, 255, 85], [0, 255, 170], [0, 255, 255], [0, 170, 255], [0, 85, 255], [0, 0, 255], [85, 0, 255], \
                  [170, 0, 255], [255, 0, 255], [255, 0, 170], [255, 0, 85]]
        
        cmap = matplotlib.cm.get_cmap('hsv')
        for i in range(model_cfg.ch_heats - 1):
            rgba = np.array(cmap(1 - i/18. - 1./36))
            rgba[0:3] *= 255
            cv2.circle(canvas, peaks[i][0:2], 4, colors[i], thickness=-1)
            img_with_result = cv2.addWeighted(scale_img, 0.3, canvas, 0.7, 0)
        return peaks, img_with_result


class DetectThread(Thread):
    def __init__(self, capture_queue, result_queue):
        Thread.__init__(self)
        self.predict_func = initialize(cfg.model_path)
        self.capture_queue = capture_queue
        self.result_queue = result_queue
        self.action = BackSquat()


    def run(self):
        while True:
            client_addr, frame_id, frame = self.capture_queue.get()
           
            # print("detect", frame_id, frame.shape)
            if frame_id == -1:
                self.result_queue.put([frame_id, [], 0])
                continue
            start_time = time.time()
            peaks, img = detect(frame, self.predict_func, scale=0.5, draw_result=False)
            tips, text, result_img = self.action.push_new_frame(peaks, cv2.resize(frame, (0, 0), fx=0.25, fy=0.25, interpolation=cv2.INTER_CUBIC))

            if len(tips) >=1:
                print("tis-------------------------", frame_id, tips)
            # print("after detect")
            # print(img.shape)
            self.result_queue.put([frame_id, tips, result_img])
