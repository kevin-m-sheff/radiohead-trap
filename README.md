# radiohead-trap

## Description
This is a personal python project I made for occasionally tricking my Radiohead-disliking partner in to listening to Radiohead. 

It continuously listens to microphone input and recognizes spoken words using offline voice recognition via the SpeechRecognition Python package and Vosk.  Recognized words are queued until they used, in sliding-window batches of 5, for Radiohead lyrics database queries to see if 5 consecutive words match 5 consecutive lyrics to any A-side Radiohead song from one of their 9 LP releases.  If there is a match, the spotipy package is used to start playing that song on Spotify.  Once a song starts playing, the program exits.

TLDR: If someone says 5 words in a row that match lyrics to any Radiohead song, that Radiohead song starts playing on Spotify. 


## Installation
### This project was not really created with the intention for distribution, but if you would like to try to use it:

### Step Zero: Have spotify premium.  This will not work with a free account.

### Step One
A: Clone the repository somewhere.

### Step Two
A: Install the python packages listed in requirements.txt.  I would recommend installing inside a virtual environment.

B: Check here for PyAudio installation instructions if you're having trouble: https://pypi.org/project/PyAudio/

### Step Three
A: Download a vosk language model from https://alphacephei.com/vosk/models - I recommend https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip

B: Extract the zip file and place the contents in the "model" directory.

### Step Four
A: Create a spotify developer account using the same log in method you use for spotify premium: https://developer.spotify.com

B: Go through the getting started instructions here (takes 3 minutes): https://developer.spotify.com/documentation/web-api

C: Go to Dashboard -> your app name -> Settings -> Basic Information | Record the Client ID and Client secret.
  
D: Create a .env file in the root of the project directory with the contents:
SPOTIPY_CLIENT_ID=your_client_id
  
SPOTIPY_CLIENT_SECRET=your_client_secret
  
SPOTIPY_REDIRECT_URI=http://localhost:3000

## Usage
Before running the program, make sure you have a working microphone device connected to the computer you're using and that you are logged in to an open spotify client on the device you want the song audio to come from.

In a terminal of some type, enter the root of the directory where you cloned the project and type "python3 main.py" and hit enter.

You will be prompted to select a microphone device and spotify client.  After waiting for vosk to initialize, you'll be informed that the program is listening and you should see the things you say printed out in the terminal stdout.

To end the program, ctrl+C.


## Notes
-I have only tested this on a 2021 M1 MacBook Pro and it works fine.  I did not test it anywhere else because I can only use this program a limited number of times before the novelty of tricking my partner wears off and she tries to search-and-destroy my devices.

-If you're going to use this yourself, a Spotify developer account is needed because I did not think it was worth the effort to go through the Spotify application review process for a practical joke I'll use 5 times.  See installation section for how to set this up.



