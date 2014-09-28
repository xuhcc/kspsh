import math
import multiprocessing

import numpy
from PIL import Image

from audio import Audio


class Visualizer(multiprocessing.Process):
    """
    Creates images from audio data
    """
    def __init__(self, queue, audio_file, width, height, delay):
        super().__init__(daemon=True)
        self.queue = queue
        self.audio = Audio.read(audio_file)
        self.width = width
        self.height = height
        self.chunk_size = self.audio.get_chunk_size(delay)
        self.block_size = 2 ** math.ceil(math.log2(self.chunk_size))
        self.color = code_to_rgb256('#5F00FF')

    def run(self):
        for pos in range(0, len(self.audio), self.chunk_size):
            spectrum = self.audio.get_spectrum(pos, pos + self.block_size)
            mtx = numpy.zeros((self.width, self.height, 3),
                              dtype=numpy.uint8)
            for i in range(self.block_size):
                x = math.floor(i * self.width / self.block_size)
                y = math.floor(spectrum[i // 2] * (self.height - 1))
                mtx[x, y] = self.color
            image = Image.fromarray(numpy.rot90(mtx), 'RGB')
            self.queue.put(image)


def code_to_rgb256(code):
    r = int(code[1:3], 16)
    g = int(code[3:5], 16)
    b = int(code[5:7], 16)
    return r, g, b
