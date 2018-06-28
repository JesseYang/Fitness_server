import pickle
import os
import numpy as np
import matplotlib
import matplotlib.cm as cm
import cv2

from cfgs.config import cfg

class Tip:
    def __init__(self):
        pass

    def _tip_path(self, tip_name):
        return os.path.join('tips', self.action_name, "%s.wav" % tip_name)

    def check(self, frame):
        if self.tip not in frame.tips and self._check(frame):
            frame.tips.append(self.tip)
            return self.tip, self.text
        else:
            return None, None


class Action:
    def __init__(self, data_path, frame_interval):
        f = open(data_path, 'rb')
        std_data = pickle.load(f)
        self.std_masks = [e[0] for idx, e in enumerate(std_data) if idx % frame_interval == 0]
        self.std_imgs = [e[1] for idx, e in enumerate(std_data) if idx % frame_interval == 0]
        self.std_peaks = [e[2] for idx, e in enumerate(std_data) if idx % frame_interval == 0]

        self.std_height, self.std_width, _ = self.std_imgs[0].shape

        self.frame_idx = -1

        self.info_buffer = []

        # for each frame, each peak has the format (x_coord, y_coord)
        x_min = np.min([np.min([e[0] for e in one_frame_peaks if len(e) > 0]) for one_frame_peaks in self.std_peaks])
        x_max = np.max([np.max([e[0] for e in one_frame_peaks if len(e) > 0]) for one_frame_peaks in self.std_peaks])
        y_min = np.min([np.min([e[1] for e in one_frame_peaks if len(e) > 0]) for one_frame_peaks in self.std_peaks])
        y_max = np.max([np.max([e[1] for e in one_frame_peaks if len(e) > 0]) for one_frame_peaks in self.std_peaks])

        self.net_width = x_max - x_min
        self.net_height = y_max - y_min
        self.std_crop_width = int(self.net_width * 1.8)
        self.std_crop_height = int(self.net_height * 1.8)

        if self.std_crop_width / cfg.output_width > self.std_crop_height / cfg.output_height:
            self.std_crop_height = int(self.std_crop_width / cfg.output_width * cfg.output_height)
        else:
            self.std_crop_width = int(self.std_crop_height / cfg.output_height * cfg.output_width)

        std_x_center = (x_max + x_min) / 2
        std_y_center = (y_max + y_min) / 2

        self.std_crop_x_start = int(std_x_center - self.std_crop_width / 2)
        self.std_crop_x_end = int(std_x_center + self.std_crop_width / 2)
        self.std_crop_y_start = int(std_y_center - self.std_crop_height / 2)
        self.std_crop_y_end = int(std_y_center + self.std_crop_height / 2)

        self.frame_num = len(self.std_masks)

        self.trans_std_imgs = []
        self.trans_std_masks = []
        self.trans_std_peaks = []

        for std_idx in range(self.frame_num):
            self._transform_std_img(std_idx)

    def _transform_std_img(self, std_idx):
        if len(self.trans_std_imgs) > std_idx:
            return [self.trans_std_imgs[std_idx], self.trans_std_masks[std_idx], self.trans_std_peaks[std_idx]]

        pad_left = np.maximum(0, 0 - self.std_crop_x_start)
        pad_top = np.maximum(0, 0 - self.std_crop_y_start)
        pad_right = np.maximum(0, self.std_crop_x_end - self.std_width)
        pad_bot = np.maximum(0, self.std_crop_y_end - self.std_height)

        pad_top = pad_top + 60
        pad_bot = pad_bot - 60

        trans_std_img = np.pad(self.std_imgs[std_idx], ((pad_top, pad_bot), (pad_left, pad_right), (0, 0)), 'edge')
        trans_std_mask = np.pad(self.std_masks[std_idx], ((pad_top, pad_bot), (pad_left, pad_right)), 'constant', constant_values=0)

        trans_std_img = trans_std_img[self.std_crop_y_start + pad_top:self.std_crop_y_end + pad_top,
                                      self.std_crop_x_start + pad_left:self.std_crop_x_end + pad_left]
        trans_std_mask = trans_std_mask[self.std_crop_y_start + pad_top:self.std_crop_y_end + pad_top,
                                        self.std_crop_x_start + pad_left:self.std_crop_x_end + pad_left]

        trans_std_img = cv2.resize(trans_std_img, (cfg.output_width, cfg.output_height))
        trans_std_mask = cv2.resize(trans_std_mask, (cfg.output_width, cfg.output_height), cv2.INTER_NEAREST)

        scale = cfg.output_width / self.std_crop_width
        trans_std_peaks = [((e[0] - self.std_crop_x_start) * scale, (e[1] - self.std_crop_y_start) * scale) if len(e) > 0 else () for e in self.std_peaks[std_idx]]

        self.trans_std_imgs.append(cv2.resize(trans_std_img, (cfg.output_width, cfg.output_height)))
        self.trans_std_masks.append(cv2.resize(trans_std_mask, (cfg.output_width, cfg.output_height), cv2.INTER_NEAREST))
        self.trans_std_peaks.append(trans_std_peaks)

        return [self.trans_std_imgs[std_idx], self.trans_std_masks[std_idx], self.trans_std_peaks[std_idx]]

    def _draw_result(self, img, peaks):
        canvas = np.copy(img) # B,G,R order
        cmap = cm.get_cmap('hsv')
        for i, peak in enumerate(peaks):
            if len(peak) == 0 or i not in self.shown_part:
                continue
            rgba = np.array(cmap(1 - i/18. - 1./36))
            rgba[0:3] *= 255
            cv2.circle(img, peaks[i][0:2], 4, cfg.part_colors[i], thickness=-1)
            img_with_result = cv2.addWeighted(img, 0.5, canvas, 0.5, 0)
        return img_with_result

    def next_frame(self):
        self.frame_idx = (self.frame_idx + 1) % self.frame_num
        return [self.trans_std_imgs[self.frame_idx], self.trans_std_masks[self.frame_idx]]

