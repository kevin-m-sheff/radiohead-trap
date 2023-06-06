#!/usr/bin/env python3
"""Used to start program. Usage: python3 main.py"""
import sys

import speech_recognition as sr

from misc_utils import (
    select_microphone,
    adjust_mic_for_ambient_noise,
    cause_vosk_initialization,
    coordinate_spotify_client_selection,
)
from handler_process_manager import create_handler_process

if __name__ == "__main__":
    try:
        # Init variables checked in finally to None for proper cleanup.
        handler_proc = None
        audio_joinable_queue = None
        parent_conn = None
        child_conn = None
        stop_process_event = None

        speech_recognizer = sr.Recognizer()

        speech_microphone = select_microphone()

        adjust_mic_for_ambient_noise(speech_microphone, speech_recognizer)

        # Start a second process to do everything that isn't listening
        # so this process can be dedicated to listening for voice input.
        (
            handler_proc,
            audio_joinable_queue,
            parent_conn,
            child_conn,
            stop_process_event,
        ) = create_handler_process(speech_recognizer)

        # Have the user specify a spotify client to use
        coordinate_spotify_client_selection(parent_conn)

        # Force vosk to initialize before starting the main listening
        # loop to get it out of the way.
        cause_vosk_initialization(speech_recognizer, audio_joinable_queue)

        # Main listening loop.
        with speech_microphone as source:
            print("\nStarted listening for spoken lyrics!\n")
            while not stop_process_event.is_set():
                # Repeatedly listen for audio input with phrase limit of 5 seconds
                # and put the resulting audio in the audio queue to be recognized.
                try:
                    audio_joinable_queue.put(
                        speech_recognizer.listen(
                            source, timeout=None, phrase_time_limit=5
                        )
                    )
                # Allow Ctrl + C to shut down the program.
                except KeyboardInterrupt:
                    raise KeyboardInterrupt("Keyboard interrupt detected.")

    except (
        AssertionError,
        AttributeError,
        OSError,
        KeyboardInterrupt,
    ) as error_message:
        print(error_message)
        print("Starting termination of program due to error.")

    finally:
        print("[Cleaning up.]")

        if parent_conn:
            parent_conn.close()

        if child_conn:
            child_conn.close()

        if stop_process_event and stop_process_event.is_set():
            # Empty the audio queue from this process since
            # handler process is likely already shut down.
            while not audio_joinable_queue.empty():
                audio_joinable_queue.get()
                audio_joinable_queue.task_done()
            audio_joinable_queue.close()
            audio_joinable_queue.join()
        elif audio_joinable_queue:
            # Put none on the audio queue to signal
            # the handler process to start shutting down.
            audio_joinable_queue.put(None)
            audio_joinable_queue.close()
            audio_joinable_queue.join()

        if handler_proc:
            handler_proc.join()

        print("[Exiting program.]")
        sys.exit(0)
