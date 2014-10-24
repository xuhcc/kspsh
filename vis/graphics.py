import colorsys
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

    def run(self):
        logger.info('visualizer started')
        for current_time, spectrum in self.generator:
            # Plot spectrum
            mtx = numpy.zeros((self.width, self.height, 3),
                              dtype=numpy.uint8)
            for x, y, color in self.plot_polar(current_time, spectrum):
                mtx[x, y] = color
            image = Image.fromarray(numpy.rot90(mtx), 'RGB')
            self.queue.put((current_time, image))

    def plot_simple(self, current_time, spectrum):
        spec_size = len(spectrum)
        for idx in range(spec_size):
            x = math.floor(idx * self.width / spec_size)
            y = math.floor(spectrum[idx] * (self.height - 1))
            c = value_to_rgb256(current_time + idx / spec_size)
            yield x, y, c

    def plot_polar(self, current_time, spectrum):
        spec_size = len(spectrum)
        for idx in range(spec_size):
            r = spectrum[idx] * self.height / 2
            a = math.pi * (2 * idx / spec_size - 0.5)
            x = math.floor(r * math.cos(a) + self.width / 2)
            y = math.floor(r * math.sin(a) + self.height / 2)
            c = value_to_rgb256(current_time + idx / spec_size)
            yield x, y, c
            x = self.width - x
            y =  self.height - y
            yield x, y, c


def code_to_rgb256(code):
    r = int(code[1:3], 16)
    g = int(code[3:5], 16)
    b = int(code[5:7], 16)
    return r, g, b


def rgb_to_rgb256(r, g, b):
    r_ = math.floor(r * 255)
    g_ = math.floor(g * 255)
    b_ = math.floor(b * 255)
    return r_, g_, b_


def value_to_rgb256(value):
    """
    Translate arbitrary value to color
    Accepts:
        value: float
    Returns:
        (r, g, b) tuple
    """
    hsv = 0.8 + 0.2 * math.sin(value), 0.5, 1
    rgb = colorsys.hsv_to_rgb(*hsv)
    return rgb_to_rgb256(*rgb)
