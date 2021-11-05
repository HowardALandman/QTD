#

# Change default password!
passwd

echo Change root password from nothing to equal pi password.
sudo vi /etc/shadow

# Turn on SPI (and maybe I2C). (Needs reboot to take effect.)
sudo raspi-config

# Update the system.
sudo apt update
sudo apt upgrade
sudo apt dist-upgrade -y
sudo apt autoremove
sudo rpi-update

# Install system packages.
sudo apt install gdb
sudo apt install python-dbg python3-dbg python3-debuginfo python3-dev
sudo apt install valgrind

# R language
sudo apt install r-base

# Octave (Matlab clone)
sudo apt install octave

# Allow core dumps.
ulimit -c unlimited

# Create mount for USB data drive.
sudo fdisk -l
sudo ls -l /dev/disk/by-uuid/
sudo mkdir -v /mnt/qtd_data
sudo vi /etc/fstab

# Enable wifi by adding routers.
sudo wpa_cli
sudo vi /etc/wpa_supplicant/wpa_supplicant.conf

# Get required Python libraries.
# for development
sudo python3 -m pip install --upgrade setuptools
sudo python3 -m pip install twine
# for running qtd.py
sudo python3 -m pip install --upgrade spidev>=3.5
sudo python3 -m pip install --upgrade RPi.GPIO
sudo python3 -m pip install paho.mqtt
# (optional) for compiling or debugging
sudo python3 -m pip install guppy3
sudo python3 -m pip install Cython

# Adafruit CircuitPython for driving Si5351 and other I2C peripherals.
#sudo python3 -m pip install --upgrade adafruit-python-shell
#wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
#sudo python3 raspi-blinka.py
sudo apt install -y i2c-tools	# probably unnecessary
sudo python3 -m pip install --upgrade RPi.GPIO	# probably unnecessary
sudo python3 -m pip install --upgrade adafruit-blinka
sudo python3 -m pip install --upgrade adafruit-circuitpython-si5351	# clock generator
sudo python3 -m pip install --upgrade adafruit-circuitpython-ads1x15	# 16-bit ADC

# Make src directory.
mkdir src
cd src

# Configure git.
git config --global user.email "howard@riverrock.org"
git config --global user.name "Howard A. Landman"
vi ~/.gitconfig
# Configure node-red to pretty-print flow file.
# This works better with git and diff.
vi ~/.node-red/settings.js
# Uncomment the "flowFilePretty: true" line.

# Clone the project.
git clone https://github.com/HowardALandman/QTD

# tdc7201 library
# If you won't be developing/altering the library,
# then you can just install from Pypi.
# Just for yourself: python3 -m pip install tdc7201
# For all users: sudo python3 -m pip install tdc7201
# If you are doing development, then
# you may need to uninstall previous versions first.
# Remove /home/pi/.local/lib/python3.7/site-packages/tdc7201*
python3 -m pip uninstall tdc7201
# Remove /usr/local/lib/python3.7/dist-packages/tdc7201*
sudo python3 -m pip uninstall tdc7201
# Install tdc7201 library in development mode.
cd QTD/src/tdc7201/
sudo python3 setup.py develop -b build -e
