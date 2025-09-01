#!/usr/bin/env python3
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from . import __version__ as version
from .video_fft_calculator import VideoFftCalculator


def main():
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description=f"video-fft v{version}",
    )
    parser.add_argument("input", help="Input video file")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output path for the images, default: same as input video file",
    )
    parser.add_argument(
        "-n", "--num-frames", type=int, help="Number of frames to calculate"
    )
    parser.add_argument(
        "-of",
        "--output-format",
        help="Select output format",
        choices=["json", "csv"],
        default="json",
    )
    parser.add_argument(
        "-r",
        "--first-frame",
        help="Render image for radial profile of the first frame",
        action="store_true",
    )
    parser.add_argument(
        "-a",
        "--all-frames",
        help="Render image for radial profile of all frames",
        action="store_true",
    )
    parser.add_argument(
        "-m",
        "--mean",
        help="Render image for mean/average radial profile of the entire sequence",
        action="store_true",
    )
    parser.add_argument(
        "-s",
        "--scale",
        help="Image scaling, adjust to increase/decrease rendered image size",
        default=1,
        type=float,
    )
    parser.add_argument(
        "-q",
        "--quiet",
        help="Do not show progress bar",
        action="store_true",
    )
    cli_args = parser.parse_args()

    vid_fft = VideoFftCalculator(
        cli_args.input,
        num_frames=cli_args.num_frames,
        output=cli_args.output,
        first_frame=cli_args.first_frame,
        all_frames=cli_args.all_frames,
        mean=cli_args.mean,
        scale=cli_args.scale,
        output_format=cli_args.output_format,
        quiet=cli_args.quiet,
    )
    vid_fft.calc_fft()
    print(vid_fft.get_formatted_stats())


if __name__ == "__main__":
    main()
