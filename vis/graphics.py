import logging
import math
import multiprocessing

import numpy
from PIL import Image

logger = logging.getLogger(__name__)


class Visualizer(multiprocessing.Process):
    """
    Creates images from audio data
    """
    def __init__(self, queue, source, width, height, delay):
        super().__init__(daemon=True)
        self.queue = queue
        self.generator = source.spectrum_generator(delay)
        self.width = width
        self.height = height
        self.color = code_to_rgb256('#C1FF8B')

    def run(self):
        logger.info('visualizer started')
        for spectrum in self.generator:
            # Plot spectrum
            block_size = len(spectrum)
            mtx = numpy.zeros((self.width, self.height, 3),
                              dtype=numpy.uint8)
            for i in range(block_size):
                x = math.floor(i * self.width / block_size)
                y = math.floor(spectrum[i // 2] * (self.height - 1))
                mtx[x, y] = self.color
            image = Image.fromarray(numpy.rot90(mtx), 'RGB')
            self.queue.put(image)


def code_to_rgb256(code):
    r = int(code[1:3], 16)
    g = int(code[3:5], 16)
    b = int(code[5:7], 16)
    return r, g, b
