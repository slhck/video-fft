#!/usr/bin/env python3

import sys
import os
from video_fft.video_fft_calculator import VideoFftCalculator
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import video_fft.__main__ as video_fft  # noqa E402

this_dir = os.path.abspath(os.path.dirname(__file__))
input_file = os.path.join(this_dir, "test.mp4")

ground_truth = {
    "average_fft": 14310,
    "max_fft": 14313,
    "min_fft": 14307,
    "median_fft": 14310,
    "pct_05": 14308,
    "pct_95": 14313,
}


def test_images():
    fft = VideoFftCalculator(input_file, all_frames=True, mean=True)
    fft.calc_fft()

    files = [f"test_frame-{i}.png" for i in range(5)]
    files.append("test-mean.png")

    for f in files:
        fpath = os.path.join(this_dir, f)
        assert os.path.isfile(fpath)
        try:
            os.unlink(fpath)
        except Exception as e:
            print(e)
            pass

def test_stats():
    fft = VideoFftCalculator(input_file)
    fft.calc_fft()
    ret = fft.get_stats()

    del ret["input_file"]

    assert ret == ground_truth
