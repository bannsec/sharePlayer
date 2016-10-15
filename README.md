# Overview
This goal for this library is to allow people to play back audio and video together with a group of other people across networks or internet.

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


# Security Considerations
This app has been outfitted with authenticating encryption. The other end needs to know the password ahead of time to be able to connect. Choose a strong password if you're concerned about others joining this session.


