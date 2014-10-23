import multiprocessing
import queue
import time
import tkinter as tk

from PIL import ImageTk

from vis.audio import AudioFile, Player
from vis.graphics import Visualizer


class Application(object):

    def __init__(self, input_file, width=800, height=600, fps=25):
        # Prepare window and elements
        self.root = tk.Tk()
        self.root.geometry("{w}x{h}+{ox}+{oy}".format(
            w=width + 2,
            h=height + 2 + 20,
            ox=200,
            oy=100))
        # Create canvas
        self.canvas = tk.Canvas(
            self.root,
            width=width,
            height=height,
            bd=0,
            bg="#000")
        self.canvas.bind("<Button-1>", lambda e: self.quit())
        self.canvas.pack()
        # The application must keep a reference to the image object
        self.image = None
        # Set up workers
        self.delay = 1 / fps
        self.queue = multiprocessing.Queue(maxsize=16)
        if input_file:
            self.player = Player(input_file)
            self.visualizer = Visualizer(
                self.queue,
                AudioFile.read(input_file),
                width,
                height,
                self.delay)

    def draw_image(self):
        """
        Display one image per call
        """
        start_time = time.time()
        try:
            image = self.queue.get_nowait()
        except queue.Empty:
            pass
        else:
            # Draw image
            self.image = ImageTk.PhotoImage(image=image)
            self.canvas.create_image(0, 0, image=self.image, anchor=tk.NW)
        if self.visualizer.is_alive() or not self.queue.empty():
            # Repeat
            delay = max(self.delay - (time.time() - start_time), 0)
            self.root.after(int(delay * 1000), self.draw_image)

    def start(self):
        self.visualizer.start()
        self.player.start()
        self.draw_image()
        self.root.mainloop()

    def stop(self):
        self.player.stop()

    def quit(self):
        self.stop()
        self.root.destroy()
