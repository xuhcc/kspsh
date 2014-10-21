import argparse
import sys
import os.path

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from vis import gui


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=argparse.FileType('r'))
    args = parser.parse_args()
    app = gui.Application(args.input)
    app.start()

if __name__ == "__main__":
    main()
