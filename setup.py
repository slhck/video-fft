#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# read version string
with open(path.join(here, "video_fft", "__init__.py")) as version_file:
    version = eval(version_file.read().split(" = ")[1].strip())

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Get the history from the CHANGELOG file
with open(path.join(here, "CHANGELOG.md"), encoding="utf-8") as f:
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
    install_requires=[
        "av>=8.0.3",
        "tqdm>=4.60.0",
        "numpy>=1.20.2",
        "matplotlib>=3.4.2",
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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.6",
    entry_points={"console_scripts": ["video-fft = video_fft.__main__:main"]},
)
