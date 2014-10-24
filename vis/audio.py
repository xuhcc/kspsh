import logging
import math
import os
import subprocess
import threading
import time

import alsaaudio
import numpy

logger = logging.getLogger(__name__)


def get_spectrum(signal):
    """
    Calculate frequency spectrum
    Accepts:
        signal: numpy array
    """
    size = len(signal)
    # Calculate FFT
    trf = numpy.fft.rfft(signal, n=size)
    # Get magnitude spectrum
    spc = numpy.log(numpy.abs(trf) + 1)
    # Normalize
    spc = numpy.clip(spc / numpy.log(size / 2), 0, 1)
    return spc


class AudioFile(object):

    def __init__(self, audio_data, sample_rate):
        """
        Accepts:
            audio_data: audio data (single channel) as numpy array
            sample_rate: integer
        """
        self._data = audio_data
        self.sample_rate = sample_rate
        logger.info('audio file loaded, {0:.2f}s'.format(self.duration))

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
        data = numpy.float16(data) / 32768
        return cls(data, sample_rate)

    def spectrum_generator(self, chunk_length):
        """
        Accepts:
            chunk_length: chunk length, seconds
        Yields:
            current_time: float
            spectrum: numpy array
        """
        chunk_size = math.ceil(chunk_length * self.sample_rate)
        block_size = 2 ** math.ceil(math.log2(chunk_size))  # FFT size
        current_time = 0
        for pos in range(0, len(self._data), chunk_size):
            spectrum = get_spectrum(self._data[pos:pos + block_size])
            current_time += chunk_length
            yield current_time, spectrum


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
        logger.info('player started')
        while proc.poll() is None:
            if self._stop_event.is_set():
                proc.terminate()
                break
            time.sleep(0.1)
        logger.info('player stopped')

    def stop(self):
        self._stop_event.set()


class Recorder(object):
    """
    Captures audio
    """
    def __init__(self, card="sysdefault:CARD=PCH", sample_rate=44100):
        self._data = numpy.array([], dtype="float16")
        self.sample_rate = sample_rate
        self.source = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,
                                    alsaaudio.PCM_NORMAL,
                                    card)
        self.source.setchannels(1)  # Mono
        self.source.setrate(sample_rate)
        self.source.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        logger.info('recorder initialized')

    def spectrum_generator(self, chunk_length):
        """
        Accepts:
            chunk_length: chunk length, seconds
        Yields:
            current_time: float
            spectrum: numpy array
        """
        chunk_size = math.ceil(chunk_length * self.sample_rate)
        block_size = 2 ** math.ceil(math.log2(chunk_size))  # FFT size
        start_time = time.time()
        pos = 0
        while True:
            # Read audio data from device
            length, raw_data = self.source.read()
            if length <= 0:
                continue
            data = numpy.fromstring(raw_data, dtype="int16")
            data = numpy.float16(data) / 32768
            self._data = numpy.append(self._data, data)
            if len(self._data) >= pos + block_size:
                spectrum = get_spectrum(self._data[pos:pos + block_size])
                pos += block_size
                current_time = time.time() - start_time + chunk_length * 1.5
                yield current_time, spectrum
