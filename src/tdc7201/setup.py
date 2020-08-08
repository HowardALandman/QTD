#!/usr/bin/python3

from setuptools import setup, find_packages

from tdc7201 import __version__

with open('README.md') as f:
    long_description = f.read()

setup(name='tdc7201',
      version=__version__,
      description='Raspberry Pi driver for Texas Instruments TDC7201 Time-to-Digital-Converter chip',
      long_description_content_type='text/markdown',
      long_description=long_description,
      install_requires=["RPi.GPIO>=0.5","spidev>=3.5"],
      # also requires "time", "sys", and "random",
      # but those are all built-in.
      classifiers=[
	  "Development Status :: 4 - Beta",
	  "Intended Audience :: Developers",
	  "Intended Audience :: Science/Research",
          "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
          "Natural Language :: English",
	  "Operating System :: POSIX :: Linux",
	  "Programming Language :: Python :: 3",
	  "Programming Language :: Python :: 3 :: Only",
	  "Programming Language :: Python :: 3.6",
	  "Programming Language :: Python :: 3.7",
	  "Topic :: Scientific/Engineering",
	  "Topic :: Scientific/Engineering :: Physics",
	  "Topic :: Software Development :: Libraries :: Python Modules",
	  "Topic :: System :: Hardware",
	  "Topic :: System :: Hardware :: Hardware Drivers"
      ],
      url='https://github.com/HowardALandman/QTD/tree/master/src/tdc7201',
      author='Howard A. Landman',
      author_email='howard@riverrock.org',
      license='GPLv3+',
      #packages=['tdc7201'],
      packages=find_packages(),
      zip_safe=False)
