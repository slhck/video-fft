"""
FFT-based video analysis to detect actual video resolution.

This module provides tools for analyzing video content using Fast Fourier Transform
(FFT) to identify upscaled content by examining high-frequency components. Upscaled
videos typically show reduced high-frequency energy compared to native resolution
content, which can be detected through radial profile analysis of the FFT magnitude
spectrum.
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
from typing import Generator, Literal, TypedDict, cast

import av
import numpy as np
from matplotlib import pyplot as plt
from tqdm import tqdm


class VideoFftData(TypedDict):
    input_file: str
    average_fft: int
    max_fft: int
    min_fft: int
    median_fft: int
    pct_05: int
    pct_95: int


class VideoFftCalculator:
    def __init__(
        self,
        input_file: str,
        num_frames: int | None = None,
        output: str | None = None,
        first_frame: bool = False,
        all_frames: bool = False,
        mean: bool = False,
        scale: float = 1,
        output_format: Literal["csv", "json"] = "json",
        quiet: bool = False,
    ):
        """


        Args:
            input_file (str): input video file
            num_frames (int | None, optional): maximum number of frames to process
            output (str | None, optional): output path for images
            first_frame (bool, optional): render image for radial profile of the first frame
            all_frames (bool, optional): render image for radial profile of all frames
            mean (bool, optional): render image for mean/average radial profile of the entire sequence
            scale (float, optional): image scaling, adjust to increase/decrease rendered image size
            output_format (str, optional): select output format, must be 'json' or 'csv'
            quiet (bool, optional): do not show progress bar

        Raises:
            RuntimeError: Wrong output format, must be 'json' or 'csv'
        """
        self.input_file = str(input_file)
        self.output = (
            str(output) if output is not None else os.path.dirname(self.input_file)
        )
        self.num_frames = int(num_frames) if num_frames is not None else None
        self.first_frame = bool(first_frame)
        self.all_frames = bool(all_frames)
        self.mean = bool(mean)
        self.scale = float(scale)

        self.output_format = str(output_format)
        if self.output_format not in ["json", "csv"]:
            raise RuntimeError("Wrong output format, must be 'json' or 'csv'")

        self.quiet = bool(quiet)

        self.frame_height: int | None = None
        self.frame_width: int | None = None

        # Create output directory if it doesn't exist
        if self.output:
            os.makedirs(self.output, exist_ok=True)

        self.fig_prefix: str = os.path.join(
            self.output, os.path.splitext(os.path.basename(self.input_file))[0]
        )

        self.data: VideoFftData | None = None
        self.last_magnitude_spectrum: np.ndarray | None = None  # for later
        self.avg_magnitude_spectrum = None  # for later

    @staticmethod
    def radial_profile(data: np.ndarray, center: tuple[int, int]) -> np.ndarray:
        """
        Calculate the radial profile of a 2D array.

        Args:
            data (np.ndarray): 2D array
            center (tuple[int, int]): center of the radial profile

        Returns:
            np.ndarray: radial profile

        Source: https://stackoverflow.com/a/21242776/435093
        """
        y, x = np.indices((data.shape))
        r = np.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2)
        r = r.astype(int)

        tbin = np.bincount(r.ravel(), data.ravel())
        nr = np.bincount(r.ravel())
        radialprofile = tbin / nr
        return radialprofile

    def get_stats(self) -> VideoFftData:
        """
        Return the calculated statistics.

        Raises:
            RuntimeError: when the data hasn't been generated yet

        Returns:
            VideoFftData: calculated statistics
        """
        if not self.data:
            raise RuntimeError(
                "Data has not been generated yet, call calc_fft() first!"
            )

        return self.data

    def get_formatted_stats(self) -> str:
        """
        Return the stats in the chosen output format.

        Returns:
            str: stats in the chosen output format
        """
        if not self.data:
            raise RuntimeError(
                "Data has not been generated yet, call calc_fft() first!"
            )

        if self.output_format == "json":
            return json.dumps(self.data, indent=4)
        elif self.output_format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(self.data.keys())
            writer.writerow(self.data.values())
            return output.getvalue()
        else:
            raise RuntimeError("Wrong output format, must be 'json' or 'csv'")

    def get_num_frames(self) -> int:
        container = av.open(self.input_file)
        num_frames = container.streams.video[0].frames
        return num_frames

    def _read_input_file(self) -> Generator[np.ndarray, None, None]:
        """
        Read the input and yield the individual frames

        Returns:
            Generator[np.ndarray, None, None]: generator of frames
        """
        container = av.open(self.input_file)

        if not len(container.streams.video):
            raise RuntimeError("No video streams found!")

        for frame in container.decode(video=0):
            frame_data = (
                frame.to_ndarray(format="gray")
                .reshape(frame.height, frame.width)
                .astype("float32")
            )
            yield frame_data

    def _plot_magnitude_spectrum(self, what: str, frame_index=None):
        if what not in ["last", "mean"]:
            raise RuntimeError("'what' must be 'last' or 'mean'")

        data = (
            self.last_magnitude_spectrum
            if what == "last"
            else self.avg_magnitude_spectrum
        )

        if data is None:
            raise RuntimeError("No data to plot!")

        if self.frame_width is None or self.frame_height is None:
            raise RuntimeError("No frame width/height calculated")

        plt.figure(
            figsize=(
                (self.frame_width / 100) * self.scale,
                (self.frame_height / 100) * self.scale,
            ),
            dpi=72,
        )
        plt.imshow(data, cmap="gray")

        if what == "last":
            if frame_index is None:
                raise RuntimeError("Pass a frame index!")
            file_path = f"{self.fig_prefix}_frame-{frame_index}.png"
        else:
            file_path = f"{self.fig_prefix}-mean.png"

        plt.savefig(file_path, bbox_inches="tight")

        print(f"File written to {file_path}", file=sys.stderr)

    def calc_fft(self) -> None:
        """
        Calculate FFT-based metrics for the input video.

        Processes each frame by computing its 2D FFT, then extracts the azimuthally
        averaged 1D power spectrum (radial profile) from the magnitude spectrum.
        The sum of high-frequency components is used as a metric to detect upscaled
        content - native resolution videos have higher values than upscaled ones.

        Results are stored in self.data as a VideoFftData dict containing:
        - input_file: absolute path to input
        - average_fft: mean of high-frequency sums across all frames
        - max_fft, min_fft, median_fft: distribution statistics
        - pct_05, pct_95: 5th and 95th percentile values

        If first_frame, all_frames, or mean options are set, corresponding
        magnitude spectrum images are saved to the output directory.

        Raises:
            RuntimeError: If no video streams found or no FFT values calculated.
        """
        # Generate empty list fft sum values
        fft_values: list[int] = []

        if self.num_frames is not None:
            num_frames = min(self.get_num_frames(), self.num_frames)
        else:
            num_frames = self.get_num_frames()

        t = tqdm(total=num_frames, disable=self.quiet, file=sys.stderr)

        current_frame = 0
        for frame_data in self._read_input_file():
            fshift = np.fft.fftshift(np.fft.fft2(frame_data))
            self.last_magnitude_spectrum = 20 * np.log(np.abs(fshift))

            if self.avg_magnitude_spectrum is None:
                self.avg_magnitude_spectrum = self.last_magnitude_spectrum  # type: ignore
            else:
                self.avg_magnitude_spectrum = np.mean(
                    np.array(
                        [self.avg_magnitude_spectrum, self.last_magnitude_spectrum]
                    ),
                    axis=0,
                )

            if not (self.frame_height or self.frame_width):
                self.frame_height, self.frame_width = self.last_magnitude_spectrum.shape  # type: ignore

            if self.frame_height is None or self.frame_width is None:
                raise RuntimeError("Could not determine frame width/height")

            if (self.first_frame and current_frame == 0) or self.all_frames:
                self._plot_magnitude_spectrum("last", current_frame)

            center = (int(self.frame_width / 2), int(self.frame_height / 2))

            # Calculate the azimuthally averaged 1D power spectrum
            psf_1d = VideoFftCalculator.radial_profile(
                cast(np.ndarray, self.last_magnitude_spectrum), center
            )
            # Get the sum of the high frequencies
            low_freq_ind = int((len(psf_1d) / 2))
            fft_values.append(sum(psf_1d[low_freq_ind:]))

            current_frame += 1
            t.update()
            if num_frames is not None and current_frame >= num_frames:
                break

        t.close()

        if self.mean:
            self._plot_magnitude_spectrum("mean")

        if not fft_values:
            raise RuntimeError("No FFT values were calculated!")

        self.data = {
            "input_file": os.path.abspath(self.input_file),
            "average_fft": int(np.mean(fft_values)),
            "max_fft": int(max(fft_values)),
            "min_fft": int(min(fft_values)),
            "median_fft": int(np.median(fft_values)),
            "pct_05": int(np.percentile(fft_values, 5, method="midpoint")),
            "pct_95": int(np.percentile(fft_values, 95, method="midpoint")),
        }
