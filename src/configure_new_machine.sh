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

# Make src directory.
mkdir src
cd src

# Configure git.
git config --global user.email "howard@riverrock.org"
git config --global user.name "Howard A. Landman"
vi ~/.gitconfig

# Clone the project.
git clone https://github.com/HowardALandman/QTD

# Install tdc7201 library in development mode.
cd QTD/src/tdc7201/
sudo python3 setup.py develop -b build -e
