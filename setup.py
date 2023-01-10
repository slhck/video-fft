#!/usr/bin/env python
import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

# read version string
with open(os.path.join(here, "video_fft", "__init__.py")) as version_file:
    for line in version_file:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"')
            break

# Get the long description from the README file
with open(os.path.join(here, "README.md")) as f:
    long_description = f.read()

# Get the history from the CHANGELOG file
with open(os.path.join(here, "CHANGELOG.md")) as f:
    history = f.read()

setup(
    name="video_fft",
    version=version,
    description="Calculate the magnitude spectrum of a video sequence, via Fast Fourier Transform",
    long_description=long_description + "\n\n" + history,
    long_description_content_type="text/markdown",
    author="Werner Robitza",
    author_email="werner.robitza@gmail.com",
    url="https://github.com/slhck/video-fft",
    packages=["video_fft"],
    include_package_data=True,
    package_data={"video_fft": ["py.typed"]},
    install_requires=[
        "av",
        "tqdm",
        "numpy",
        "matplotlib",
    ],
    license="MIT",
    zip_safe=False,
    keywords="ffmpeg, video",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    entry_points={"console_scripts": ["video-fft = video_fft.__main__:main"]},
)
