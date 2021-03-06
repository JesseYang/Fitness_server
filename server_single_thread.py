import socket
import threading
import sys
import time
import struct
import cv2
import numpy as np
import uuid
from enum import Enum
import os
from queue import Queue
from threading import Thread
from threading import Lock
from threading import Event

from detect import DetectThread
from capture import CaptureThread
from visualize import VisualizeGUI
from audio import AudioThread

from cfgs.config import cfg
import pdb
from actions import *
import json
import pickle


class Server_Accept:
    def __init__(self, host='192.168.1.124', port=8117):
        print(os.getpid())
        self.host = host
        self.port= port
        self.thread_flage=0
        self.bufsize = 1024*3

        self.capture_queue = Queue(maxsize=cfg.max_queue_len)
        self.result_queue = Queue(maxsize=cfg.max_queue_len)
        # self.enable_capture = Event()
        # self.enable_predict = Event()

        # self.capture_thread = CaptureThread(self.capture_queue, self.enable_capture)
        # capture_thread.start()

        self.detect_thread = DetectThread(self.capture_queue, self.result_queue)
        self.detect_thread.start()

        # self.audio_thread = AudioThread()
        # self.audio_thread.start()

        self.output_path = "output_%s.mp4" % str(uuid.uuid4())
        self.deep_squat = DeepSquat()
        self.back_squat = BackSquat()
        
        # self.capture_thread = CaptureThread(self.capture_queue, self.enable_capture)
        # capture_thread.start()
        self.socket_server()
        
        # visualize_gui = VisualizeGUI(result_queue, audio_thread, enable_predict, back_squat, output_path=output_path)

    def del_data(self, conn, addr):
        print(os.getpid())
        # .from_camera = video_file == None
       
        while 1:
            print(os.getpid())
            buf = b""
            data_len = -1
            while True:
                tem_buf = conn.recv(self.bufsize)
                buf += tem_buf
                if data_len != -1 and data_len == len(buf):
                    break
                if len(buf) > 4 and data_len == -1:  
                    img_size = struct.unpack('i', buf[:4])
                    data_len = img_size[0] + 16
            img_info = struct.unpack("iid%ds" % (data_len - 16), buf)

            print("received ori time ", str(img_info[2]))
            img_id = img_info[1]
            # self.img_time[img_id] = img_info[2]
            if img_id == -1:
                
                self.capture_queue.put([addr, -1, 0])
                conn.close()
                break
            else:
                data = np.fromstring(img_info[3], dtype='uint8')
                img = cv2.imdecode(data, 1)
                print("======received from client ======",addr, img_id, img.shape, str(time.time()-img_info[2]))
                print("size ", self.capture_queue.qsize())
                self.capture_queue.put([addr, img_id, img])

          
         
                client_addr, ids, peak = self.result_queue.get()
                result = pickle.dumps((ids, peak, time.time()))
                print("server send to client")
               
                conn.send(result)
                print("peak send over")
                # break
 
        print("Client connection interrupted: {0}".format(addr))
        # conn.close()
        # self.s.close()
        print("{0} closed! ".format(addr))


    def socket_server(self):
        
        self.s =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        try:
            self.s.bind((self.host,self.port))
        except socket.error as e:
            print("Bind failed")
            print(e)
            sys.exit()
        self.s.listen(5)
        print("waiting for connection...")

    def receive_data(self):
        # while True:
        conn, addr = self.s.accept()
        print("accept new connection from {0}".format(addr))
        # t = threading.Thread(target=self.del_data, args=(conn, addr))
        # t.start()
        # self.wait_for_result()
        self.del_data(conn, addr)
        conn.close()
        self.s.close()

    def wait_for_result(self):
        while True:
            if self.thread_flage:
                self.receive_data()

if __name__ == '__main__':

    server_accept = Server_Accept()
    server_accept.receive_data()
