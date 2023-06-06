"""Contains database search thread definitions."""
import sqlite3
import string
from collections import deque

import spotipy

from spotipy_helper import init_spotipy_helper_wrapper


def search_db(words_to_search_deque):
    """Uses sqlite3 to query radiohead_songs.db to see if
       spoken words match lyrics for a radiohead song.

    Args:
        words_to_search_deque: set of spoken words used for lyrics database query.

    Returns:
        result: results of the query, regardless of success in finding a song match.
    """

    database_path = "radiohead_songs.db"
    search_string = " ".join(words_to_search_deque)

    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    query = "SELECT name FROM songs WHERE lyrics LIKE ?"
    cursor.execute(query, ("%" + search_string + "%",))

    result = cursor.fetchall()
    conn.close()
    return result


def database_search_thread(
    recognized_words_deque, rec_words_deque_thread_cond, stop_thread_event, child_conn
):
    """Thread that runs in handler process and initiates
       query of database every time there are enough spoken words
       in the queue and attempts to start spotify playback
       when there is a database query match.

    Args:
        recognized_words_deque: recognized words added in the recognize
                                audio thread waiting to be used for query
                                in the database search thread.

        rec_words_deque_thread_cond: threading.condition used to signal
                                     enough words have been added to recognized
                                     words deque for processing.

        stop_thread_event: multiprocessing.event to coordinate stop between
                           database search thread and recognize audio thread in
                           handler process on fault or program completion.

        child_conn: handler process end of pipe connecting main
                    process and handler process; only used for spotify
                    client selection.
    """

    # Set the number of words for each database search.
    num_words_to_search = 5

    # Init deque that will hold the words to search in the lyrics database.
    words_to_search_deque = deque()

    try:
        # Init spotipy helper.
        spotipy_helper = init_spotipy_helper_wrapper(child_conn)

        # Loop forever unless the stop event is set by one of the two threads in this process.
        while not stop_thread_event.is_set():
            with rec_words_deque_thread_cond:
                while (
                    len(words_to_search_deque) + len(recognized_words_deque)
                    < num_words_to_search
                ):
                    # Wait until there is another word added to the recognized_words_deque.
                    rec_words_deque_thread_cond.wait()

                    # At least one word added, check to see if the thread should be stopped.
                    if recognized_words_deque[0] is None:
                        # stop thread event already set in recognize audio thread in this scenario
                        break

                # If there are enough words now, start processing.
                if (
                    not stop_thread_event.is_set()
                    and len(words_to_search_deque) + len(recognized_words_deque)
                    >= num_words_to_search
                ):
                    # Process in this while loop while there are enough total words
                    # to process between the two deques.
                    while (
                        not stop_thread_event.is_set()
                        and len(words_to_search_deque) + len(recognized_words_deque)
                        >= num_words_to_search
                    ):
                        # Move items from recognized_words_deque words_to_search_deque
                        # until the latter is appropriately sized.
                        while (
                            not stop_thread_event.is_set()
                            and len(words_to_search_deque) < num_words_to_search
                        ):
                            popped_word = recognized_words_deque.popleft()
                            # Ensure lowercase and no punctuation in word
                            # before adding to words_to_search_deque.
                            popped_word_sanitized = popped_word.lower().translate(
                                str.maketrans("", "", string.punctuation)
                            )
                            words_to_search_deque.append(popped_word_sanitized)

                        # Perform the search against the words.
                        if not stop_thread_event.is_set():
                            result = search_db(words_to_search_deque)

                            # If there is not a database match, pop the oldest
                            # word in the words_to_search_deque.
                            if result == []:
                                words_to_search_deque.popleft()
                            else:
                                # Just take the first result in case there are
                                # multiple matches.
                                song_name = result[0][0]
                                print(
                                    "\n!!! SPOKEN WORDS '{0}' MATCH LYRICS FOR SONG '{1}' !!!\n".format(
                                        " ".join(words_to_search_deque), song_name
                                    )
                                )

                                if spotipy_helper.play_song_wrapper(
                                    song_name, stop_thread_event
                                ):
                                    stop_thread_event.set()
                                    print(
                                        "\nSong is playing successfully, shutting down this program!\n"
                                    )

                                if stop_thread_event.is_set():
                                    # Stop execution
                                    break
                                else:
                                    # Continue execution after popping the oldest word
                                    # in the words_to_search_deque
                                    words_to_search_deque.popleft()
                                    pass

    except (
        AssertionError,
        KeyError,
        spotipy.SpotifyException,
        spotipy.oauth2.SpotifyOauthError,
    ) as error_message:
        print(error_message)
        stop_thread_event.set()

    finally:
        print("[Exiting database search thread.]")
