# In development. Not usable at the moment
This goal for this library is to allow people to play back audio and video together with a group of other people across networks or internet.

# Dependencies
I hope to make this mostly OS agnostic. Here are the current dependencies
 - mplayer (http://www.mplayerhq.hu/)
  - Debian: sudo apt-get install mplayer
 - python3
  - Debian: sudo apt-get install python3
 - mplayer.py python library
  - install from https://github.com/Owlz/mplayer.py -- Bugfixes over master branch
 - pyNaCl for crypto
  - pip install pynacl


# Security Considerations
For now, I haven't added much security. This means, if you want to play with it, you'll want to ensure you're restricting who can connect to your port via firewall or routing rules.


