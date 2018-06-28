import socket
import os
import threading
import numpy as np
import struct
import cv2
import ctypes
from enum import Enum
import sys
from queue import Queue
from threading import Thread
from threading import Lock
from threading import Event

# from detect import DetectThread
# from capture import CaptureThread
# from visualize import VisualizeGUI
from audio import AudioThread

import pickle
import time
import tkinter as tk
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import askquestion
# from fitness import Extractor
from PIL import Image
from PIL import ImageTk
import uuid
import pdb
from GUI.widgets import *

from cfgs.config import cfg

from actions import *

class Client_Accept:
    def __init__(self, host='192.168.1.124', port=8117, video_file=None):
        self.host = host
        self.port= port
        self.bufsize = 1024
        self.result_queue = Queue(maxsize=cfg.max_queue_len)
        self.video_file = video_file
        self.s_addr_port = (self.host, self.port)
        # self.init()
        self.img_dic = {}
        self.audio_thread = AudioThread()
        self.audio_thread.start()
        self.action = BackSquat()
        self.socket_client((self.s_addr_port))
        # self.__init_gui() 

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
        self.window.resizable(False, False)
        
    def _start(self):

        client_thread = threading.Thread(target=self.send_to_server)
        
        print("11") 
        # result_thread = threading.Thread(target=self.show_result)
        # print("22")
        client_thread.start()
        # result_thread.start()


    def init(self):
        pass
        # capture_thread = CaptureThread(capture_queue, enable_capture)
        # capture_thread.start()
        # visualize_gui = VisualizeGUI(result_queue, audio_thread, enable_predict, back_squat, output_path=output_path)

    def socket_client(self, s_addr_port):
        print(s_addr_port)
        try:
            self.server =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        except Exception as e:
            print("Error create socket")
            # sys.exit()
            # quit()

        try:
            # socket.setdefaulttimeout(5)
            self.server.connect(s_addr_port)
        except socket.error as e:
            print("Error connecting to server: %s" % e )
            sys.exit()
        except socket.timeout:
            print("connecting to server timeout")
            sys.exit()
        print("client connected the server %s, %d" % (self.host, self.port))

        self.__init_gui()

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()
    def on_closing(self):
        self.server.close()
        self.window.destroy()
        # sys.exit()
        quit()

    def capture_run(self, cap, from_camera):
        frame_idx = 0
        save_frame_idx = 0
        while (True if from_camera == True else cap.isOpened()):
           
            ret, frame = cap.read()
            
            frame_idx = (frame_idx + 1) % 1e5

            if frame_idx % int(30 / cfg.fps) == 0:
                continue
            scale = 0.8

            y_start = int((480 - 480 * scale) / 2)
            y_end = int((480 - 480 * scale) / 2 + 480 * scale)

            x_start = int(640 - 640 * scale)

            frame = frame[y_start:y_end, x_start:]

            if from_camera:
                frame = cv2.transpose(frame)
                frame = cv2.flip(frame, 1)
            if ret == False or (cfg.capture_frame_num > 0 and save_frame_idx >= cfg.capture_frame_num):
                # self.capture_queue.put(np.zeros((0,0)))
                print("video over")
                break

            save_frame_idx += 1
            # self.capture_queue.put(frame)
            return frame
    ##20180512.mp4
    def send_to_server(self, video_file=None):
        print("pid",os.getpid())
        # print(video_file)
        from_camera = video_file == None
        print(cfg.cam_idx)
        cap = cv2.VideoCapture(cfg.cam_idx) if from_camera else cv2.VideoCapture(video_file)
        # frame = self.capture_run(cap, from_camera)
        frame_idx = 0
        if not cap.isOpened():
            print("open video failed")
            return

        while (True if from_camera == True else cap.isOpened()):
            print("pid",os.getpid())
            ret, frame = cap.read()
            
            if not ret:
                print("over")
                self.server.send(struct.pack("l99434s", int(-1), b''))
                break
  
            scale = 0.8

            y_start = int((480 - 480 * scale) / 2)
            y_end = int((480 - 480 * scale) / 2 + 480 * scale)

            x_start = int(640 - 640 * scale)
           
            # frame = frame[y_start:y_end, x_start:]

            if from_camera:
                frame = cv2.transpose(frame)
                frame = cv2.flip(frame, 1)
        
            self.img_dic[frame_idx] = frame
            img_encode = cv2.imencode('.jpg', frame)[1]
            img_code = np.array(img_encode)
            str_encode = img_code.tostring()
            # print(str_encode)
            print("size", str(len(str_encode)))
            
            # self.server.send(pickle.dumps((frame_idx, str_encode)))
            self.server.send(struct.pack("l99434s", int(frame_idx), str_encode))
            print("%s frame send over!" % (frame_idx))
            # time.sleep(2)
            frame_idx +=1
            # result_peak = self.server.recv(self.bufsize)
            buf = b""
            while 1:
                tem_buf = self.server.recv(self.bufsize)
                if len(tem_buf) != self.bufsize :
                    buf += tem_buf
                    break
                buf += tem_buf
            if len(tem_buf) == 0:
                break
            img_id, result_peak = pickle.loads(buf)
            print("============recevied from server=================")
            print(img_id)
            print(result_peak[0])
            # self.result_queue.put(img_id,result_peak[0])  

            # if len(ret) == 0:
            #     break
            print(frame_idx-1)
            if frame_idx == -1:
                break

            # for i in result_peak[0]:
                # cv2.circle(self.img_dic[img_id], i[0:2], 4, (255,255,0), thickness=-1)
            # cv2.imwrite(str(uuid.uuid4())+".jpg", self.img_dic[img_id])
            tips, text, result_img = self.action.push_new_frame(result_peak[0], cv2.resize(self.img_dic[img_id], (0, 0), fx=0.25, fy=0.25, interpolation=cv2.INTER_CUBIC))

            if self.audio_thread.qsize() == 0 and self.audio_thread.is_playing == False:
                for tip in tips:
                    self.audio_thread.put(tip)

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

        self.server.close()
        # cv2.destroyAllWindows()
   
    def show_result(self):
        while True:
            print("rrr")
            frame_id, peak = self.result_queue.get()
            print("1111")
            # if len(ret) == 0:
            #     break
            print(frame_idx)
            if frame_id == -1:
                break
            tips, text, result_img = self.action.push_new_frame(peak, self.img_dic[frame_id])

            if self.audio_thread.qsize() == 0 and self.audio_thread.is_playing == False:
                for tip in tips:
                    self.audio_thread.put(tip)

            # if self.output_path != None and cfg.capture_frame_num != -1:
            #     videoWrite.write(result_img)
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
        


if __name__ == '__main__':
    client_accept = Client_Accept()
    
    # client_accept.send_data()