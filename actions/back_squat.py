import numpy as np
import os
from enum import Enum
import time
import matplotlib
import cv2

from cfgs.config import cfg
from .action import Action, Tip
from .frame import *

'''
动作名称：箭步后蹲
动作要点：
1. 下蹲时膝盖是否到位：通过检测下蹲到最低点时膝盖的纵坐标和相应踝关节的纵坐标之间的关系判断
2. 下蹲时膝盖是否过于靠前：通过检测下蹲最低点时膝盖横坐标和踝关键横坐标的关系判断
3. 下蹲时腰部是否挺直：通过检测下蹲到最低点时肩部横坐标和胯部横坐标的关系判断
'''

class BackSquatTip1(Tip):
    def __init__(self):
        self.action_name = "back_squat"
        self.tip_name = "tip_1"
        self.text = "下蹲不到位"
        self.tip = self._tip_path(self.tip_name)

    def _check(self, frame):
        # check if the right hip is two much higher than the right knee
        if frame.r_knee.x != None and frame.l_knee.x != None and \
           frame.r_knee.x < frame.l_knee.x:
            # check right leg
            if frame.r_ankle.y != None and frame.r_knee.y != None and \
               frame.r_knee.y - frame.r_ankle.y > 10:
                return True
            else:
                return False
        elif frame.r_knee.x != None and frame.l_knee.x != None and \
             frame.r_knee.x > frame.l_knee.x:
            # check left leg
            if frame.l_ankle.y != None and frame.l_knee.y != None and \
               frame.l_knee.y - frame.l_ankle.y > 10:
                return True
            else:
                return False
        else:
            # wrong detection 
            return False


class BackSquatTip2(Tip):
    def __init__(self):
        self.action_name = "back_squat"
        self.tip_name = "tip_2"
        self.text = "膝盖太靠前了"
        self.tip = self._tip_path(self.tip_name)

    def _check(self, frame):
        # check if the right knee is two much in front of the right ankle
        if frame.r_knee.x != None and frame.l_knee.x != None and \
           frame.r_knee.x < frame.l_knee.x:
            # check right leg
            if frame.r_knee.x != None and frame.r_knee.x != None and \
                frame.r_knee.x - frame.r_ankle.x > 10:
                return True
            else:
                return False
        elif frame.r_knee.x != None and frame.l_knee.x != None and \
             frame.r_knee.x > frame.l_knee.x:
            # check left leg
            if frame.l_knee.x != None and frame.l_knee.x != None and \
                frame.l_knee.x - frame.l_ankle.x > 10:
                return True
            else:
                return False
        else:
            # wrong detection 
            return False


class BackSquatTip3(Tip):
    def __init__(self):
        self.action_name = "back_squat"
        self.tip_name = "tip_3"
        self.text = "腰背没有挺直"
        self.tip = self._tip_path(self.tip_name)

    def _check(self, frame):
        # check if the right shoulder is two much in front of the right hip
        if frame.r_shoulder.x != None and frame.r_hip.x != None and frame.l_hip.x != None and \
            frame.r_shoulder.x - np.max([frame.l_hip.x, frame.r_hip.x]) > 20:
            return True
        else:
            return False

class BackSquatTip4(Tip):
    def __init__(self):
        self.action_name = "back_squat"
        self.tip_name = "good_tip_1"
        self.text = "动作很到位"
        self.tip = self._tip_path(self.tip_name)

    def _check(self, frame):
        if len(frame.tips) == 0:
            return True
        else:
            return False


# the part oder:
# 0:nose         1:neck           2:right_shoulder   3:right_elbow
# 4:right_wrist  5:left_shoulder  6:left_elbow       7:left_wrist
# 8:right_hip    9:right_knee     10:right_ankle    11:left_hip
# 12:left_knee   13:left_ankle    14:right_eye       15:left_eye
# 16:right_ear   17:left_ear

class BackSquat(Action):
    def __init__(self):
        self.frame_interval = 2
        self.shown_part = [0, 1, 2, 3, 4, 8, 9, 10, 11, 12, 13, 14, 16]
        self.name = "back_squat"
        self.correct_tips = [BackSquatTip1(), BackSquatTip2(), BackSquatTip3()]
        self.praise_tips = [BackSquatTip4()]
        Action.__init__(self, os.path.join(cfg.std_data_dir, "%s.pkl" % self.name), self.frame_interval)

    def _get_tips(self):
        tips = []
        text_list = []
        bottom_frames = [(idx, e) for idx, e in enumerate(self.info_buffer) if e.is_status('bottom')]

        if len(bottom_frames) == 0:
            return tips, text_list

        last_bottom_frame_idx = bottom_frames[-1][0]
        last_bottom_frame = self.info_buffer[last_bottom_frame_idx]

        for tip_idx, correct_tip in enumerate(self.correct_tips):
            tip, text = correct_tip.check(last_bottom_frame)
            tips.append(tip) if tip is not None else None
            text_list.append(text) if text is not None else None
            if len(tips) > 0:
                return tips, text_list

        for praise_tip in self.praise_tips:
            tip, text = praise_tip.check(last_bottom_frame)
            tips.append(tip) if tip is not None else None
            text_list.append(text) if text is not None else None
            if len(tips) > 0:
                return tips, text_list

        return tips, text_list

    def push_new_frame(self, peaks, img):
        std_img, std_mask = self.next_frame()

        if len(self.info_buffer) >= cfg.max_buffer_len:
            del(self.info_buffer[0])
        self.info_buffer.append(Frame(peaks, img))

        # use the right hip to determine the action cycle
        # get the y-coord of right_hip in past frames
        r_hip_y = [e.r_hip.y for e in self.info_buffer]

        # if r_hip_y is the greatest in the neighbourhood with length 50, then it is a bottom frame
        # if r_hip_y is the smallest in the neighbourhood with length 50, then it is a top frame
        key_frame = ""
        if len(r_hip_y) >= 50:
            if r_hip_y[-25] == np.min(r_hip_y[-50:]) and np.where(r_hip_y[-50:-25] == r_hip_y[-25])[0].shape[0] == 0:
                key_frame = "top"
                self.info_buffer[-25].set_status("top")
            if r_hip_y[-25] == np.max(r_hip_y[-50:]) and np.where(r_hip_y[-50:-25] == r_hip_y[-25])[0].shape[0] == 0:
                key_frame = "bottom"
                self.info_buffer[-25].set_status("bottom")

        # judge whether the action is correct and generate the tips
        tips, text_list = self._get_tips()

        # generate the shown image
        img = self._draw_result(img, peaks)
        img_resize = cv2.resize(img, (cfg.output_width, cfg.output_height))

        blend = cv2.addWeighted(img_resize, 0.5, std_img, 0.5, 0)
        blend_fg = cv2.bitwise_and(blend, blend, mask=std_mask)
        mask_inv = cv2.bitwise_not(std_mask)
        img_bg = cv2.bitwise_and(img_resize, img_resize, mask=mask_inv)
        overlap_result_img = blend_fg + img_bg

        result_img = np.zeros((cfg.show_img_h, cfg.show_img_w, 3), dtype=np.uint8)
        result_img[:, :cfg.show_img_w//2] = cv2.resize(img_resize, (cfg.show_img_w//2, cfg.show_img_h))
        result_img[:, cfg.show_img_w//2:] = cv2.resize(std_img, (cfg.show_img_w//2, cfg.show_img_h))

        return tips, key_frame, result_img
