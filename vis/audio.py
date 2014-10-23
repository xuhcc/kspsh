import math
import os
import subprocess
import threading
import time

import numpy


def get_spectrum(signal):
    """
    Calculate frequency spectrum
    Accepts:
        signal: numpy array
    """
    size = len(signal)
    # Calculate FFT
    tf = numpy.fft.rfft(signal, n=size)
    # Get magnitude spectrum
    tf = numpy.log(numpy.abs(tf) + 1) / numpy.log(size / 2)
    return tf


class AudioFile(object):

    def __init__(self, audio_data, sample_rate):
        """
        Accepts:
            audio_data: audio data (single channel) as numpy array
            sample_rate: integer
        """
        self._data = audio_data
        self.sample_rate = sample_rate

    def __len__(self):
        return len(self._data)

    @property
    def duration(self):
        seconds = len(self._data) / self.sample_rate
        return seconds

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
            '-ac', '1',  # mono
            '-',  # pipe
        ]
        pipe = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL,
                                bufsize=10**8)
        data = numpy.fromstring(pipe.stdout.read(), dtype="int16")
        pipe.terminate()
        # Normalize
        data = numpy.float32(data) / numpy.abs(data).max()
        return cls(data, sample_rate)

    def spectrum_generator(self, chunk_length):
        """
        Accepts:
            chunk_length: chunk length, seconds
        Yields:
            spectrum: numpy array
        """
        chunk_size = math.ceil(chunk_length * self.sample_rate)
        block_size = 2 ** math.ceil(math.log2(chunk_size))  # FFT size
        for pos in range(0, len(self._data), chunk_size):
            spectrum = get_spectrum(self._data[pos:pos + block_size])
            yield spectrum


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
        proc = subprocess.Popen(['ffplay', '-i', path],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        while proc.poll() is None:
            if self._stop_event.is_set():
                proc.terminate()
                break
            time.sleep(0.1)

    def stop(self):
        self._stop_event.set()
