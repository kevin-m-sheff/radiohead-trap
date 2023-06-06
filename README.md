# radiohead-trap

## Description
This is a personal python project I made for occasionally tricking my Radiohead-disliking partner in to listening to Radiohead. It continuously listens to microphone input and recognizes spoken words using offline voice recognition via the SpeechRecognition Python package and Vosk.  Recognized words are queued until they used, in sliding-window batches of 5, for Radiohead lyrics database queries to see if 5 consecutive words match 5 consecutive lyrics to any A-side Radiohead song from one of their 9 LP releases.  If there is a match, the spotipy package is used to start playing that song on Spotify.  Once a song starts playing, the program exits.

TLDR: If someone says 5 words in a row that match lyrics to any Radiohead song, that Radiohead song starts playing on Spotify. 


## Installation
This project was not really created with the intention for distribution, but if you would like to try to use it:

## Usage

## Notes
