"""Contains SpotipyHelper class and functionality to 
   assist with spotify authentication, search, and playback.
"""
import os
import time

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from misc_utils import SpotifyClientSelectionEnum


def init_spotipy_helper_wrapper(child_conn):
    """Wrapper for initializing the spotipy helper class
       used for authentication, song search, and playback.

    Args:
        child_conn: handler process end of pipe connecting main process and handler process;
                    only used for spotify client selection.

    Raises:
        KeyError: if SpotifyHelper __init__ fails.
        AssertionError: if selecting spotify client fails.

    Returns:
        spotipy_helper: initialized SpotipyHelper instance.
    """

    spotipy_helper = None
    try:
        spotipy_helper = SpotipyHelper()
    except KeyError as e:
        raise KeyError(
            "Failed to create SpotipyHelper: {0} - Please check "
            "to ensure your .env file is correct and try again.".format(e)
        )

    # Try to set the spotify device id.
    set_spotify_id_status = spotipy_helper.set_spotify_device_id(child_conn)
    assert (
        set_spotify_id_status
    ), ("Failed to set spotify client, please make sure you are "
    "logged in to an open spotify client before running this program.")

    return spotipy_helper


class SpotipyHelper:
    """Class to handle spotify authentication, song search, and playback."""

    def __init__(self):
        """Initializes SpotifyHelper instance if authentication is successful.

        Raises:
            KeyError: if authentication is unsuccessful.
        """
        # Set device_id to None and configure with set_spotify_device_id
        # method after SpotipyHelper init.
        self._device_id = None

        # Load .env variables for client id/secret and redirect uri.
        load_dotenv()

        try:
            self._spotify_instance = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    client_id=os.environ["SPOTIPY_CLIENT_ID"],
                    client_secret=os.environ["SPOTIPY_CLIENT_SECRET"],
                    redirect_uri=os.environ["SPOTIPY_REDIRECT_URI"],
                    scope="app-remote-control,user-modify-playback-state,"
                    "user-read-currently-playing,user-read-playback-state",
                )
            )

        except KeyError as e:
            raise KeyError(
                "Spotify authentication failed. Environment variable(s) "
                "possibly not set properly: {0}".format(e)
            )

    def set_spotify_device_id(self, child_conn):
        """Sets spotipy helper's _device_id with selected spotify client id.

        Args:
            child_conn: handler process end of pipe connecting main process and handler process;
                                 only used for spotify client selection.

        Raises:
            spotipy.SpotifyException: if setting device id fails.
            spotipy.oauth2.SpotifyOauthError: if spotify authentication issue arises.
        Returns:
            True or False: True if device id is set properly; False otherwise.
        """

        try:
            devices = self._spotify_instance.devices()
        except spotipy.SpotifyException as e:
            raise spotipy.SpotifyException(
                "An error has occurred while setting spotify device id: {0}".format(e)
            )
        except spotipy.oauth2.SpotifyOauthError as e:
            raise spotipy.oauth2.SpotifyOauthError(
                "A spotify authentication issue has occurred. You need to restart "
                "the program to reauthenticate: {0}".format(e)
            )

        device_list = devices["devices"]

        if not device_list:
            print("No available spotify clients.")
            child_conn.send(SpotifyClientSelectionEnum.CLIENT_ERROR)
            return False

        selected_device = None
        while selected_device is None:
            try:
                print("\nAvailable spotify clients:")
                for i, device in enumerate(device_list):
                    print("{0}: {1} ({2})".format(i, device["name"], device["type"]))

                child_conn.send(SpotifyClientSelectionEnum.CLIENT_PROMPT)
                user_choice = int(child_conn.recv())

                if 0 <= user_choice <= len(device_list) - 1:
                    selected_device = device_list[user_choice]["id"]
                else:
                    print("Invalid selection. Please choose a number from the list.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        self._device_id = selected_device
        child_conn.send(SpotifyClientSelectionEnum.CLIENT_SET)
        return True

    def search_for_song(self, song_name, stop_thread_event):
        """Searches for target song_name on spotify.

        Args:
            song_name: song name as listed in radiohead_songs.db
            stop_thread_event: multiprocessing.event to coordinate stop between
                               database search thread and recognize audio thread in
                               handler process on fault or program completion.

        Returns:
            track_id, track_name: spotify_track_id, spotify_track_name; or
                                  None, None if no results found.
        """

        track_id = None
        track_name = None

        query = "track:{0} artist:Radiohead".format(song_name)

        print("Searching spotify for {0}".format(song_name))
        results = None
        try:
            results = self._spotify_instance.search(q=query, type="track", limit=1)
        except spotipy.SpotifyException as e:
            print(
                "An error has occurred while searching Spotify, but "
                "program execution will continue: {0}".format(e)
            )
            return track_id, track_name
        except spotipy.oauth2.SpotifyOauthError as e:
            print(
                "A spotify authentication issue has occurred. You need "
                "to restart the program to reauthenticate: {0}".format(e)
            )
            stop_thread_event.set()
            return track_id, track_name

        if results and results.get("tracks") and results["tracks"].get("items"):
            track_id = results["tracks"]["items"][0]["id"]
            track_name = results["tracks"]["items"][0]["name"]
        else:
            print("No results found for {0} when searching Spotify".format(song_name))

        return track_id, track_name

    def start_playback(self, track_id, track_name, stop_thread_event):
        """Attempts to start playback for track_id/track_name on Spotify.

        Args:
            track_id: spotify track id
            track_name: spotify track name
            stop_thread_event: multiprocessing.event to coordinate stop between
                               database search thread and recognize audio thread in
                               handler process on fault or program completion.

        Returns:
            True or False: True if start playback command issued, False otherwise.
        """

        print("Attempting to play: '{0}'".format(track_name))
        try:
            self._spotify_instance.start_playback(
                device_id=self._device_id, uris=["spotify:track:{0}".format(track_id)]
            )
        except spotipy.SpotifyException as e:
            print(
                "An error has occurred while starting playback on Spotify, "
                "but program execution will continue: {0}".format(e)
            )
            return False
        except spotipy.oauth2.SpotifyOauthError as e:
            print(
                "A spotify authentication issue has occurred. You need to "
                "restart the program to reauthenticate: {0}".format(e)
            )
            stop_thread_event.set()
            return False
        return True

    def check_song_is_playing(self, track_id, track_name, stop_thread_event):
        """Checks that song is actually playing on spotify after start play request.

        Args:
            track_id: spotify track id
            track_name: spotify track name
            stop_thread_event: multiprocessing.event to coordinate stop between
                               database search thread and recognize audio thread in
                               handler process on fault or program completion.

        Returns:
            True or False: True if song is verified to be playing, False otherwise.
        """

        current_playback = None
        try:
            current_playback = self._spotify_instance.current_playback()
        except spotipy.SpotifyException as e:
            print(
                "An error has occurred while checking playback on Spotify, "
                "but program execution will continue: {0}".format(e)
            )
            return False
        except spotipy.oauth2.SpotifyOauthError as e:
            print(
                "A spotify authentication issue has occurred. You need to "
                "restart the program to reauthenticate: {0}".format(e)
            )
            stop_thread_event.set()
            return False

        if current_playback and current_playback.get("is_playing"):
            current_track_name = current_playback["item"]["name"]
            current_track_id = current_playback["item"]["id"]
            if current_track_name == track_name and current_track_id == track_id:
                print("'{0}' is verified to be playing.".format(track_name))
                return True

        print(
            "Unable to verify {0} is playing, so program execution will continue.".format(
                track_name
            )
        )
        return False

    def play_song_wrapper(self, song_name, stop_thread_event):
        """Wrapper for spotify search, start playback, and check playback functionality.

        Args:
            song_name: song name as listed in radiohead_songs.db
            stop_thread_event: multiprocessing.event to coordinate stop between
                               database search thread and recognize audio thread in
                               handler process on fault or program completion.

        Returns:
            True or False: True if song was found and is successfully playing, False otherwise.
        """

        # Search for song
        track_id, track_name = self.search_for_song(song_name, stop_thread_event)

        # Attempt to start playback if valid results found
        start_playback_requested = False
        if not stop_thread_event.is_set() and track_id and track_name:
            start_playback_requested = self.start_playback(
                track_id, track_name, stop_thread_event
            )

        # Check that song is actually playing
        song_is_playing = False
        if not stop_thread_event.is_set() and start_playback_requested:
            # Give the song a few seconds to start playing before checking
            time.sleep(2)
            song_is_playing = self.check_song_is_playing(
                track_id, track_name, stop_thread_event
            )

        return song_is_playing
