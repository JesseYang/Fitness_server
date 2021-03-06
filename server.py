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
# from visualize import VisualizeGUI
# from audio import AudioThread

from cfgs.config import cfg
import pdb
from actions import *
import json
import pickle


class ServerAccept:
    def __init__(self, host='192.168.1.124', port=8117):
        print(os.getpid())
        self.host = host
        self.port= port
        self.bufsize = 1024*3

        self.capture_queue = Queue(maxsize=cfg.max_queue_len)
        self.result_queue = Queue(maxsize=cfg.max_queue_len)

        self.detect_thread = DetectThread(self.capture_queue, self.result_queue)
        self.detect_thread.start()


        self.output_path = "output_%s.mp4" % str(uuid.uuid4())
        self.deep_squat = DeepSquat()
        self.back_squat = BackSquat()
        
        self.socket_server()

    def receive_data(self, conn, addr):
        print(os.getpid())
        while True:
            print(os.getpid())
            receive_time = time.time()
            buf = b""
            data_len = -1
           
            # receive one image
            while True:
                tem_buf = conn.recv(self.bufsize)
                buf += tem_buf
                if data_len != -1 and data_len == len(buf):
                    break
                if len(buf) > 4 and data_len == -1:  
                    img_size = struct.unpack('i', buf[:4])
                    data_len = img_size[0] + 8

            img_info = struct.unpack("i%ds" % (data_len - 8), buf[4:])
            print("receive time ", str(time.time() - receive_time))
            img_id = img_info[0]
            if img_id == -1:
                self.capture_queue.put([addr, -1, 0])
                conn.close()
                break
            else:
                data = np.fromstring(img_info[1], dtype='uint8')
                img = cv2.imdecode(data, 1)
                print("======received from client ======",addr, img_id, img.shape)

                self.capture_queue.put([addr, img_id, img])

        print("Client connection interrupted: {0}".format(addr))
        conn.close()
        self.s.close()
        print("{0} closed! ".format(addr))

    def send_result(self, addr, port):
        try:
            send_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception as e:
            print("Error create socket")
        print("111")
        try:
            # socket.setdefaulttimeout(5)
            print("server to client(addr:port)", addr)
            send_client.connect((addr,8121))
        except socket.error as e:
            print("Error connecting to client: %s" % e )
            sys.exit()
        while True:
            client_addr, ids, peak = self.result_queue.get()

            if ids == -1:
                send_client.close()
                break
            result = pickle.dumps((ids, peak))
            # print("server send to client", addr, client_addr)
            # print(ids, peak)
            send_client.send(result)
            print("%d peak send over, pid %d" % ( ids, os.getpid()))
            

    def socket_server(self):
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        try:
            self.s.bind((self.host,self.port))
        except socket.error as e:
            print("Bind failed")
            print(e)
            sys.exit()
        self.s.listen(5)
        print("waiting for connection...")
        print(os.getpid())

    def deal_data(self):
        while True:
            conn, addr = self.s.accept()
            print("accept new connection from {0}".format(addr))
            t = threading.Thread(target=self.receive_data, args=(conn, addr))
            t.start()
            # self.wait_for_result()
            # self.receive_data(conn, addr)
            
            t1 = threading.Thread(target=self.send_result, args=(addr))
            t1.start()


    def wait_for_result(self):
        while True:
            if self.thread_flage:
                self.receive_data()

if __name__ == '__main__':

    server_accept = ServerAccept()
    server_accept.deal_data()
