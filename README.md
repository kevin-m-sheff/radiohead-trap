# radiohead-trap

## Description
This is a personal python project I made for occasionally tricking my Radiohead-disliking partner in to listening to Radiohead. 

It continuously listens to microphone input and recognizes spoken words using offline voice recognition via the SpeechRecognition Python package and Vosk.  Recognized words are queued until they used, in sliding-window batches of 5, for Radiohead lyrics database queries to see if 5 consecutive words match 5 consecutive lyrics to any A-side Radiohead song from one of their 9 LP releases.  If there is a match, the spotipy package is used to start playing that song on Spotify.  Once a song starts playing, the program exits.

TLDR: If someone says 5 words in a row that match lyrics to any Radiohead song, that Radiohead song starts playing on Spotify. 


## Installation
This project was not really created with the intention for distribution, but if you would like to try to use it:
1: Clone the repository somewhere.
2: Install the python packages listed in requirements.txt.  I would recommend installing inside a virtual environment. 
2.a: (Check here for PyAudio installation instructions if you're having trouble: https://pypi.org/project/PyAudio/)
3: Download a vosk language model 

## Usage

## Notes
I have only tested this on a 2021 M1 MacBook Pro and it works fine.  I did not test it anywhere else because I can only use this program a limited number of times before the novelty of tricking my partner wears off. 

