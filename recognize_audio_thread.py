"""Contains recognize audio thread definitions."""
import json

import speech_recognition as sr


def recognize_audio_thread(
    audio_joinable_queue,
    speech_recognizer,
    recognized_words_deque,
    rec_words_deque_thread_cond,
    stop_thread_event,
):
    """Thread that runs in handler process that recognizes
       words from spoken audio captured in the main process and appends
       the recognized words to the recognized words queue to be consumed
       by the database search thread.

    Args:
        audio_joinable_queue: multiprocessing.queue that is consumed by
                              the recognize audio thread in the handler process.

        speech_recognizer: speech_recognition recognizer object.

        recognized_words_deque: recognized words added in the recognize audio thread
                                waiting to be used for query in the database search thread.

        rec_words_deque_thread_cond: threading.condition used to signal enough words have been
                                     added to recognized words deque for processing.

        stop_thread_event: multiprocessing.event to coordinate stop between
                           database search thread and recognize audio thread in
                           handler process on fault or program completion.
    """

    # Loop forever unless the stop event is set by one of the two threads in this process.
    while not stop_thread_event.is_set():
        # Get the next audio processing job.
        new_audio = audio_joinable_queue.get()

        # new_audio is None is the signal to shut down.
        if new_audio is None:
            with rec_words_deque_thread_cond:
                stop_thread_event.set()
                # Empty the queue
                while not audio_joinable_queue.empty():
                    print("Emptying audio queue from audio thread")
                    audio_joinable_queue.get()
                    audio_joinable_queue.task_done()
                # Call task_done one more time to account for the None
                audio_joinable_queue.task_done()
                # Notify the waiting database search thread so it can shut down too.
                recognized_words_deque.appendleft(None)
                rec_words_deque_thread_cond.notify()
                break

        # Use vosk to recognize words spoken.
        try:
            recognized_audio = speech_recognizer.recognize_vosk(new_audio)
        except sr.UnknownValueError:
            print("Vosk could not interpret most recent audio sample.")
            continue

        try:
            recognized_words_json = json.loads(recognized_audio)
        except json.JSONDecodeError:
            print("JSONDecodeError: Vosk returned malformed JSON.")
            continue

        if recognized_words_json.get("text"):
            recognized_words = recognized_words_json.get("text")
            recognized_words_list = recognized_words.split()
            with rec_words_deque_thread_cond:
                # Add newly recognized words to recognized words queue and
                # notify the database search thread that words have been added.
                recognized_words_deque.extend(recognized_words_list)
                print("Recognized: {0}".format(recognized_words))
                rec_words_deque_thread_cond.notify()

        audio_joinable_queue.task_done()

    print("[Exiting recognize audio thread.]")
