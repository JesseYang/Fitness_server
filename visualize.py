import pickle
import cv2
import numpy as np
from enum import Enum
from queue import Queue

from queue import Queue
from threading import Thread
from threading import Lock
from threading import Event

from cfgs.config import cfg


import tkinter as tk
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import askquestion
# from fitness import Extractor
from PIL import Image
from PIL import ImageTk
import os
import time
import uuid
import pdb
from GUI.widgets import *

class Mode(Enum):
    OVERLAP = 1
    SIDE_BY_SIDE = 2
    BOTH = 3

class VisualizeGUI():
    def __init_gui(self):

        self.window = tk.Tk()
        self.window.wm_title('VideoText')
        self.window.config(background = '#FFFFFF')

        self.canvas = ICanvas(self.window, width = cfg.output_width * 2, height = cfg.output_height)
        self.canvas.grid(row = 0, column = 0)

        self.fm_control = tk.Frame(self.window, width=cfg.output_width*2, height=20, background = 'white')
        self.fm_control.grid(row = 1, column=0, sticky=tk.W, padx=2, pady=5)

        self.lb_status = tk.Text(self.fm_control, height=18,  background = 'white')
        self.lb_status.grid(row = 0, column=2, padx=10, pady=5)
        # self.lb_status.insert(1.0,"因为你在我心中是那么的具体") 
        
        self.fm_status = tk.Frame(self.window, width = 100, height = 100, background = '#FFFFFF')
        self.fm_status.grid(row = 0, column=1, padx=0, pady=2)
  
        self.btn_prev_frame1 = tk.Button(self.fm_status, text='Start', command = self._start)
        self.btn_prev_frame1.grid(row = 0, column=0, padx=10, pady=2)
        
        self.btn_next_frame3 = tk.Button(self.fm_status, text='New', command = None)
        self.btn_next_frame3.grid(row = 1, column=0, padx=10, pady=20)
        
    def __init__(self, result_queue, audio_thread, enable_predict, action, output_path=None):

        self.result_queue = result_queue
        self.enable_predict = enable_predict
        self.action = action
        self.audio_thread = audio_thread

        self.img_queue = []


        self.output_path = output_path

        self.mode = Mode.BOTH
        # self.mode = Mode.SIDE_BY_SIDE
        # self.mode = Mode.OVERLAP

        self.init_frame_num = 10
        self.frame_idx = 0
        # self.__init_gui()
        # self.window.mainloop()


    def run(self):
        self.init_peaks = []
        self.enable_predict.set()

        if self.output_path != None and cfg.capture_frame_num != -1:
            if self.mode == Mode.SIDE_BY_SIDE or self.mode == Mode.BOTH:
                videoWrite = cv2.VideoWriter(self.output_path, cv2.VideoWriter_fourcc(*'mp4v'), 20, (2 * cfg.output_width, cfg.output_height))
            else:   # The OVERLAP mode
                videoWrite = cv2.VideoWriter(self.output_path, cv2.VideoWriter_fourcc(*'mp4v'), 20, (cfg.output_width, cfg.output_height))

      
        while True:
            frame_id, peak = self.result_queue.get()
            # if len(ret) == 0:
            #     break
            if frame_id == 0:
            	break
            peak, img = ret

            tips, text, result_img = self.action.push_new_frame(peak, img)

            if self.audio_thread.qsize() == 0 and self.audio_thread.is_playing == False:
                for tip in tips:
                    self.audio_thread.put(tip)

            if self.output_path != None and cfg.capture_frame_num != -1:
                videoWrite.write(result_img)
            # cv2.imshow('frame', result_img)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break

            result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
            # print(result_img.shape)
            self.canvas.add(result_img)
            if text != "" and text != None:
                self.lb_status.insert(1.0, '\n')
                self.lb_status.insert(1.0, text)
                self.lb_status.update_idletasks()
            # print(text)
            self.window.update_idletasks()  #快速重画屏幕  
            self.window.update()

        if self.output_path != None and cfg.capture_frame_num != -1:
            videoWrite.release()
        cv2.destroyAllWindows()

        # f = open('temp.pkl', 'wb')
        # pickle.dump(temp_data, f)

        print("done")

    def _start(self):
        time.sleep(3)
        self.run()

