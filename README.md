# CommandLineChat
A simple command line chat


## TODO

- Password for server, a function before clientThread? Set the password for server in the beginning
- emoji functions? !smile !wink different...
- Keep log of conversations? on client?
- Make it possible to disconnect and connect, setPort, setIP etc...
- encrypt messages
- Set input mic
- Set output speaker
- Add V M H to infobox with either color green or red depending on if it's on or off. V = voice, M = mic, H = headset



## Setup

TODO





## Contribute

### PyAudio setup

#### Windows

- Install appropriate .whl file from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
- Run the following command

``` bash
pip3 install <path to .whl file>
pip3 install pyaudio
```


#### Linux

- Run the following commands

``` bash
sudo apt-get install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0
sudo apt-get install ffmpeg libav-tools
sudo pip3 install pyaudio
```

#### Mac OS

TODO





## Known errors

- Only possible to be two current voice chat users at a time, otherwise overflow on the server causing delay in voice data.
