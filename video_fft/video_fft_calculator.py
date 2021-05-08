import numpy as np
from matplotlib import pyplot as plt
import json
import os
from tqdm import tqdm
from typing import Generator
import av
import sys


class VideoFftCalculator:
    def __init__(
        self,
        input_file,
        num_frames=None,
        output=None,
        first_frame=False,
        all_frames=False,
        mean=False,
        scale=1,
        output_format="json",
        quiet=False,
    ):
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
        self.quiet = bool(quiet)

        self.frame_height = None
        self.frame_width = None
        self.fig_prefix = os.path.join(
            self.output, os.path.splitext(os.path.basename(self.input_file))[0]
        )

        self.data = {}
        self.last_magnitude_spectrum = None  # for later
        self.avg_magnitude_spectrum = None  # for later

        if self.output_format not in ["json", "csv"]:
            raise RuntimeError("Wrong output format, must be 'json' or 'csv'")

    @staticmethod
    def radial_profile(data, center):
        """
        Source: https://stackoverflow.com/a/21242776/435093
        """
        y, x = np.indices((data.shape))
        r = np.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2)
        r = r.astype(int)

        tbin = np.bincount(r.ravel(), data.ravel())
        nr = np.bincount(r.ravel())
        radialprofile = tbin / nr
        return radialprofile

    def get_stats(self):
        if not self.data:
            raise RuntimeError(
                "Data has not been generated yet, call calc_fft() first!"
            )

        return self.data

    def print_stats(self) -> None:
        if not self.data:
            raise RuntimeError(
                "Data has not been generated yet, call calc_fft() first!"
            )

        if self.output_format == "json":
            print(json.dumps(self.data, indent=4))
        elif self.output_format == "csv":
            import csv

            writer = csv.writer(sys.stdout)
            writer.writerow(self.data.keys())
            writer.writerow(self.data.values())
        else:
            # shouldn't happen
            pass

    def get_num_frames(self) -> int:
        container = av.open(self.input_file)
        num_frames = container.streams.video[0].frames
        return num_frames

    def read_input_file(self) -> Generator[np.ndarray, None, None]:
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

    def plot_magnitude_spectrum(self, what: str, frame_index=None):
        if what not in ["last", "mean"]:
            raise RuntimeError("'what' must be 'last' or 'mean'")

        data = (
            self.last_magnitude_spectrum
            if what == "last"
            else self.avg_magnitude_spectrum
        )

        if data is None:
            raise RuntimeError("No data to plot!")

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

    def calc_fft(self):
        # Generate empty list fft sum values
        fft_values = []

        if self.num_frames is not None:
            num_frames = min(self.get_num_frames(), self.num_frames)
        else:
            num_frames = self.get_num_frames()

        t = tqdm(total=num_frames, disable=self.quiet, file=sys.stderr)

        current_frame = 0
        for frame_data in self.read_input_file():
            fshift = np.fft.fftshift(np.fft.fft2(frame_data))
            self.last_magnitude_spectrum = 20 * np.log(np.abs(fshift))

            if self.avg_magnitude_spectrum is None:
                self.avg_magnitude_spectrum = self.last_magnitude_spectrum
            else:
                self.avg_magnitude_spectrum = np.mean(
                    np.array(
                        [self.avg_magnitude_spectrum, self.last_magnitude_spectrum]
                    ),
                    axis=0,
                )

            if not (self.frame_height or self.frame_width):
                self.frame_height, self.frame_width = self.last_magnitude_spectrum.shape

            if (self.first_frame and current_frame == 0) or self.all_frames:
                self.plot_magnitude_spectrum("last", current_frame)

            center = (self.frame_width / 2, self.frame_height / 2)

            # Calculate the azimuthally averaged 1D power spectrum
            psf_1d = VideoFftCalculator.radial_profile(
                self.last_magnitude_spectrum, center
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
            self.plot_magnitude_spectrum("mean")

        if not fft_values:
            raise RuntimeError("No FFT values were calculated!")

        self.data = {
            "input_file": os.path.abspath(self.input_file),
            "average_fft": int(np.mean(fft_values)),
            "max_fft": int(max(fft_values)),
            "min_fft": int(min(fft_values)),
            "median_fft": int(np.median(fft_values)),
            "pct_05": int(np.percentile(fft_values, 5, interpolation="midpoint")),
            "pct_95": int(np.percentile(fft_values, 95, interpolation="midpoint")),
        }
