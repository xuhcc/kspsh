import wave
import struct
import math


def create_wave(filename, synth, duration, nchannels=2, sampwidth=2, framerate=44100):
    """
    Accepts:
        filename
        synth: synthesizer function, accepts frame number,
            returning amplitude (value in range +-1)
        duration: duration in seconds
        nchannels: number of audio channels (1 for mono, 2 for stereo)
        sampwidth: sample width in bytes
        framerate: sampling frequency
    """
    # Create file
    wv = wave.open(filename, "wb")
    wv.setnchannels(nchannels)
    wv.setsampwidth(sampwidth)
    wv.setframerate(framerate)
    # https://ccrma.stanford.edu/courses/422/projects/WaveFormat/
    # 8-bit samples are stored as unsigned bytes, ranging from 0 to 255.
    # 16-bit samples are stored as 2's-complement signed integers,
    # ranging from -32768 to 32767.
    if sampwidth == 1:
        fmt = "{0:d}B".format(nchannels)
        con = lambda val: int((val + 1) * 255)
    elif sampwidth == 2:
        fmt = "{0:d}h".format(nchannels)
        con = lambda val: math.floor(val * 32767.5)
    else:
        raise ValueError
    nframes = int(duration * framerate * nchannels / sampwidth)
    for i in range(0, nframes):
        values = [con(synth(i, c)) for c in range(1, nchannels + 1)]
        bts = struct.pack(fmt, *values)
        wv.writeframes(bts)


def test(frame_no, channel_no):
    amp = math.sin(frame_no / 64 + math.sqrt(frame_no)) 
    return amp


if __name__ == "__main__":
    create_wave("sound.wav", test, 3)
