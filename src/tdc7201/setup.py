#!/usr/bin/python3

from setuptools import setup, find_packages

setup(name='tdc7201',
      version='0.1a1',
      description='Driver for T.I. TDC7201 chip',
      long_description='Raspberry Pi driver for Texas Instruments TDC7201 Time-to-Digital-Converter chip',
      install_requires=["RPi.GPIO>=0.5","spidev>=3.4"],
      # also requires "time", "sys", "random", and maybe "optparse",
      # but those are all built-in.
      classifiers=[
          "License :: OSI Approved :: Python Software Foundation License",
	  "Development Status :: 3 - Alpha",
	  "Intended Audience :: Science/Research",
	  "Operating System :: POSIX :: Linux",
	  "Programming Language :: Python :: 3",
	  "Topic :: Scientific/Engineering",
	  "Topic :: System :: Hardware :: Hardware Drivers"
      ],
      url='https://github.com/HowardALandman/QTD/src/tdc7201',
      author='Howard A. Landman',
      author_email='howard@riverrock.org',
      license='MIT',
      #packages=['tdc7201'],
      packages=find_packages(),
      zip_safe=False)
