# Overview
This goal for this library is to allow people to play back audio and video together with a group of other people across networks or internet.


# Supported Platforms
The goal is to build this in such a way as to support all the major platforms. That said, for now it is only tested on Linux (Ubuntu). Some initial testing on Windows indicates some things will need to be modified on the script, but it should generally be workable in the future. I do not have a Mac so I have no way of testing that side.

# Supported Players
sharePlayer currently supports using mplayer as well as ChromeCast for shared playback.


# Installation/Quick Start
This is primarily just a python project. Installation boils down to simply `pip install sharePlayer`. Here's a useful one-liner:

`mkvirtualenv --python=$(which python3) -i sharePlayer sharePlayer`

At that point, you are in your virtual environment and sharePlayer has been installed.

# Running
To run sharePlayer, simply run the command `sharePlayer`. It's highly encouraged for you to install this into a python virtual environment, so if you did that you would want to make sure that your virtual environment is open prior to running that command.

# Caveats
This app is based on client/server configuration. The server in this case is you or your co-video watcher. You need to be able to set up your network in such a way that the client can get to the server. I have not implemented any UPnP type functionality yet.

This app has been developed with the concept of having viewing parties. However, for the moment it is only tested for having one server and one client (two people total). It will likely not work as expected or at all if you attempt to connect more. This is temporary, but for now it's a 2 person viewing system.

# Dependencies
I hope to make this mostly OS agnostic. Here are the current dependencies
 - mplayer (http://www.mplayerhq.hu/)
  - Debian: sudo apt-get install mplayer
 - python3
  - Debian: sudo apt-get install python3 python3-dev
 - mplayer.py python library
  - install from https://github.com/Owlz/mplayer.py -- Bugfixes over master branch
 - pyNaCl for crypto
  - pip install pynacl
 - dill
  - pip install dill
 - progressbar2
  - pip install progressbar2

# Configuration
Right now sharePlayer supports a configuration file. This file is in ini format and can be manually edited. It also has a menu option to edit this file through the app itself. The location of this file will differ based on your OS (using appdirs in the backend). For instance, on Linux, it will be under ~/.config/sharePlayer.


# Security Considerations
This app has been outfitted with authenticating encryption. The other end needs to know the password ahead of time to be able to connect. Choose a strong password if you're concerned about others joining this session.


