import math
import os
import subprocess
import threading
import time

import numpy


class Audio(object):

    def __init__(self, audio_data, sample_rate):
        self._data = audio_data
        self.sample_rate = sample_rate

    def __len__(self):
        return len(self._data)

    @property
    def duration(self):
        seconds = len(self._data) / self.sample_rate
        return seconds

    def get_chunk_size(self, length):
        """
        Accepts:
            length: chunk length, seconds
        """
        return math.ceil(length * self.sample_rate)

    @classmethod
    def read(cls, audio_file, sample_rate=44100):
        """
        Read audio data from file
        Accepts:
            audio_file: file object
            sample_rate
        """
        path = os.path.abspath(audio_file.name)
        command = [
            'ffmpeg',
            '-i', path,
            '-f', 's16le',  # raw 16-bit
            '-acodec', 'pcm_s16le',
            '-ar', str(sample_rate),
            '-ac', '2',  # stereo
            '-',  # pipe
        ]
        pipe = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10**8)
        data = numpy.fromstring(pipe.stdout.read(), dtype="int16")
        pipe.terminate()
        # Split channels
        data = data.reshape((len(data) / 2, 2))
        return cls(data, sample_rate)

    def get_spectrum(self, p1, p2):
        """
        Calculate frequency spectrum
        Accepts:
            p1: starting position
            p2: ending position
        """
        size = p2 - p1
        sound = numpy.zeros(size, dtype=float)
        # Combine channels
        for i, sample in enumerate(self._data[p1:p2]):
            l = int(sample[0])
            r = int(sample[1])
            sound[i] = (l + r) / 2
        # Calculate FFT
        tf = numpy.abs(numpy.fft.fft(sound))[:size // 2]
        # Normalize
        tf = tf / (tf.max() or 1)
        return tf


class Player(threading.Thread):
    """
    Plays audio file
    """
    def __init__(self, audio_file):
        super().__init__()
        self.audio_file = audio_file
        self._stop_event = threading.Event()

    def run(self):
        path = os.path.abspath(self.audio_file.name)
        proc = subprocess.Popen(['ffplay', '-i', path])
        while proc.poll() is None:
            if self._stop_event.is_set():
                proc.terminate()
                break
            time.sleep(0.1)

    def stop(self):
        self._stop_event.set()
