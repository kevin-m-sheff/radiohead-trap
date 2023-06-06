"""Contains miscellaneous helper functions."""
import os
from enum import Enum, auto

import speech_recognition as sr


def select_microphone():
    """Prompts the user to select a microphone to use to detect spoken words.

    Raises:
        AttributeError: if PyAudio is not installed.

    Returns:
        speech_microphone: speech_recognition microphone object configured to use
                           selected microphone device.
    """

    # Show the user the microphone device list and have them select a mic
    mic_list = sr.Microphone.list_microphone_names()

    assert (
        len(mic_list) > 0
    ), "No audio devices detected - this program depends on microphone input."

    microphone_index = None

    mics_dict = dict()
    for index, mic_name in enumerate(mic_list):
        mics_dict[index] = mic_name

    while microphone_index is None:
        try:
            print("\nDetected audio devices:")
            for mic_key, mic_device in mics_dict.items():
                print("{0}: {1}".format(mic_key, mic_device))

            user_choice = int(
                input(
                    ("Please type the number corresponding to "
                    "the microphone you would like to use:\n")
                )
            )

            if mics_dict.get(user_choice, None) is None:
                print("\nInvalid selection. Please choose a number from the list.")
            else:
                microphone_index = user_choice

        except ValueError:
            print("\nInvalid input. Please enter a number.")

    # Init speech recognition microphone using selected microphone device.
    try:
        speech_microphone = sr.Microphone(device_index=microphone_index)
    except AttributeError as e:
        raise AttributeError(
            ("AttributeError occurred when setting the chosen microphone: {0} - "
            "Please make sure PyAudio is installed.".format(e))
        )

    return speech_microphone


def adjust_mic_for_ambient_noise(speech_microphone, speech_recognizer):
    """Wrapper for speech_recognition's ambient noise adjustment.

    Args:
        speech_microphone : speech_recognition microphone object.
        speech_recognizer : speech_recognition recognizer object.

    Raises:
        AttributeError: if speech_microphone as source has a .stream of None;
                        indicates microphone is not functioning with speech_recognition
                        properly and may not be a microphone.
    """

    print("\nQUIET! Adjusting for ambient noise.\n")
    try:
        with speech_microphone as source:
            if source.stream is not None:
                # If this if statement is not entered, the except AttributeError block will be entered.
                speech_recognizer.adjust_for_ambient_noise(source, duration=1)
    except AttributeError:
        # If selected device isn't actually a microphone, there will be an
        # AttributeError thrown from speech_recognition library that close
        # cannot be called on NoneType.
        raise AttributeError(
            "Selected audio device is not functioning correctly, please ensure device "
            "is actually a microphone or choose a different device."
        )

    print("\nOk you can stop being quiet.\n")


def cause_vosk_initialization(speech_recognizer, audio_joinable_queue):
    """Forces vosk to initialize before main listening loop to reduce
       voice recognition slowdown on recognition of first set of words
       in the main loop.

    Args:
        speech_recognizer: speech_recognition recognizer object.
        audio_joinable_queue: multiprocessing.queue that is consumed by
                              the recognize audio thread in the handler process.
    """
    print("\nPLEASE WAIT WHILE VOSK INITIALIZES!\n")
    test_audio_file = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "silence.wav"
    )
    if os.path.isfile(test_audio_file):
        with sr.AudioFile(test_audio_file) as source:
            audio_to_recognize = speech_recognizer.record(source)
            audio_joinable_queue.put(audio_to_recognize)
            # Block until recognize audio thread processes the silence audio.
            audio_joinable_queue.join()
    else:
        print(
            "\nCould not complete preemptive Vosk initialization, audio file {0} could "
            "not be found. First batch of word recognition "
            "may be slow.\n".format(test_audio_file)
        )


class SpotifyClientSelectionEnum(Enum):
    """Enum for spotify client selection status for coordination between
    the main process and the database search thread in the handler process
    """

    CLIENT_PROMPT = auto()
    CLIENT_SET = auto()
    CLIENT_ERROR = auto()


def coordinate_spotify_client_selection(parent_conn):
    """Handles the main process side of spotify client selection.
       Prompts for user input and sends choice to database search thread in
       handler process.

    Args:
        parent_conn: main process end of pipe connecting main process and handler process;
                     only used for spotify client selection.
    """

    while True:
        spotify_client_choice_recv = parent_conn.recv()
        if spotify_client_choice_recv == SpotifyClientSelectionEnum.CLIENT_SET:
            # The client was successfully set
            return
        else:
            assert (
                spotify_client_choice_recv != SpotifyClientSelectionEnum.CLIENT_ERROR
            ), "Program depends on an open and working spotify client."
            # Ask user to select a client
            parent_conn.send(input("Specify a spotify client and hit enter: "))
            continue
