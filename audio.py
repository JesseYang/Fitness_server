from queue import Queue
from threading import Thread
from threading import Lock
from threading import Event

import os

class AudioThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self._audio_queue = Queue(maxsize=10)
        self.is_playing = False

    def put(self, audio):
        self._audio_queue.put(audio)

    def qsize(self):
        return self._audio_queue.qsize()

    def run(self):
        while True:
            audio = self._audio_queue.get()
            self.is_playing = True
            os.system('aplay %s' % audio)
            self.is_playing = False
