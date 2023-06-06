"""Contains functionality to start and manage handler 
   process containing database search thread and recognize audio thread.
"""
import multiprocessing as mp
import threading
from collections import deque

from database_search_thread import database_search_thread
from recognize_audio_thread import recognize_audio_thread


def create_handler_process(speech_recognizer):
    """Creates and starts second process to handler database
       search thread and recognize audio thread.

    Args:
        speech_recognizer: speech_recognition recognizer object.

    Raises:
        OSError: if process fails to start due to lack of system resources.
        AssertionError: if process fails to start due to the
                        process having already been started.

    Returns:
        handler_proc, audio_joinable_queue, parent_conn, child_conn, stop_process_event

        handler_proc: handler process instance.

        audio_joinable_queue: multiprocessing.queue that is consumed by
                              the recognize audio thread in the handler process.

        parent_conn: main process end of pipe connecting main process and handler process;
                     only used for spotify client selection.

        child_conn: handler process end of pipe connecting main process and handler process;
                    only used for spotify client selection.

        stop_process_event: multiprocessing event used by the handler process to signal the
                            main process to stop.
    """

    mp.set_start_method("spawn")

    # Create a mp event so handler process can signal to main process to stop when needed.
    stop_process_event = mp.Event()

    # Create pipe to be used for user selection of spotify client.
    parent_conn, child_conn = mp.Pipe()

    audio_joinable_queue = mp.JoinableQueue()

    handler_proc = mp.Process(
        target=handler_process,
        args=(audio_joinable_queue, speech_recognizer, child_conn, stop_process_event),
    )

    try:
        handler_proc.start()
    except OSError as e:
        raise OSError(
            "OSError when trying to start handler process, possibly "
            "due to lack of system resources: {0}".format(e)
        )
    except AssertionError as e:
        raise AssertionError(
            "Assertion Error when trying to start handler process, process "
            "may have already been started: {0}".format(e)
        )

    return (
        handler_proc,
        audio_joinable_queue,
        parent_conn,
        child_conn,
        stop_process_event,
    )


def handler_process(
    audio_joinable_queue, speech_recognizer, child_conn, stop_process_event
):
    """Handler process that creates and manages database search
       thread and recognize audio thread.
    

    Args:
        audio_joinable_queue: multiprocessing.queue that is consumed by
                              the recognize audio thread in the handler process.

        speech_recognizer: speech_recognition recognizer object.

        child_conn: handler process end of pipe connecting main process and handler process;
                    only used for spotify client selection.
                    
        stop_process_event: multiprocessing event used by the handler process to signal the
                            main process to stop.
    """

    # Create list to store thread objects.
    threads = []

    # Create deque for recognized words.
    # Words are *only appended* in the recognize audio thread
    # and *only popped* in the database search thread.
    recognized_words_deque = deque()

    # Create threading condition to communicate when words have been appended
    # to the recognized words deque.
    rec_words_deque_thread_cond = threading.Condition()

    # Create threading event to coordinate stopping the threads.
    stop_thread_event = threading.Event()

    # Set up and start database search thread.
    db_search_thread = threading.Thread(
        target=database_search_thread,
        args=(
            recognized_words_deque,
            rec_words_deque_thread_cond,
            stop_thread_event,
            child_conn,
        ),
    )
    db_search_thread.start()
    threads.append(db_search_thread)

    # Set up and start recognize audio thread.
    rec_thread = threading.Thread(
        target=recognize_audio_thread,
        args=(
            audio_joinable_queue,
            speech_recognizer,
            recognized_words_deque,
            rec_words_deque_thread_cond,
            stop_thread_event,
        ),
    )
    rec_thread.start()
    threads.append(rec_thread)

    # Don't exit this process until both threads have stopped.
    for thread in threads:
        thread.join()

    child_conn.close()
    audio_joinable_queue.close()

    # Signal that the main process should stop.
    stop_process_event.set()

    print("[Exiting handler process.]")
