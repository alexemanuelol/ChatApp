# CommandLineChat
A simple command line chat


## TODO

- SERVER: Password for server, a function before clientThread? Set the password for server in the beginning
- SERVER: emoji functions? !smile !wink different...
- CLIENT: Keep log of conversations? on client?
- CLIENT: Make it possible to disconnect and connect, setPort, setIP etc...
- SERVER: encrypt messages
- CLIENT: Set input mic
- CLIENT: Set output speaker


## Setup


## Contributing

### Windows

- Install appropriate .whl file from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
- Run the following command

``` bash
pip3 install pyaudio
```


### Linux

- Run the following commands

``` bash
sudo apt-get install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0
sudo apt-get install ffmpeg libav-tools
sudo pip3 install pyaudio
```


## Known errors

- Only possible to be two current voice chat users at a time, otherwise overflow on the server causing delay in voice data.
