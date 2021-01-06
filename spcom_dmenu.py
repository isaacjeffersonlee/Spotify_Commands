#!/usr/bin/env python

# Imports
import spcom_config
from notify import notification
import dmenu
import os
import argparse
from argparse import RawTextHelpFormatter
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth

scope = '''user-modify-playback-state user-top-read
user-library-modify user-follow-modify playlist-read-private
playlist-modify-public playlist-modify-private user-read-playback-state
user-read-currently-playing user-read-private user-follow-read
playlist-read-collaborative user-library-read'''

# Client Credentials
username = spcom_config.username
client_secret = spcom_config.client_secret
client_id = spcom_config.client_id
redirect_uri = spcom_config.redirect_uri

# Where to look for .cache
cache_path = os.path.dirname(__file__) + '/.cache'

auth_manager = spotipy.oauth2.SpotifyOAuth(client_id=client_id,
                                           client_secret=client_secret,
                                           redirect_uri=redirect_uri,
                                           cache_path=cache_path)

sp = spotipy.Spotify(auth_manager=auth_manager)


# My json dumps function
def jprint(data):
    print(json.dumps(data, indent=5, sort_keys=False))


def get_currently_playing():
    """Return currently playing song name and artist."""
    currently_playing = {}
    currently_playing_json = sp.current_user_playing_track()
    if currently_playing_json is None:
        currently_playing['song'] = '>>>'
        currently_playing['artist'] = '<<<'
        return currently_playing
    else:
        currently_playing['song'] = currently_playing_json['item']['name']
        currently_playing['artist'] = currently_playing_json['item']['artists'][0]['name']
        return currently_playing


def get_devices():
    """Return device information for currently active spotify devices."""
    devices_info = sp.devices()['devices']
    devices = []
    for device in devices_info:
        device_dict = {}
        device_dict['id'] = device['id']
        device_dict['name'] = device['name']
        device_dict['is_active'] = device['is_active']
        devices.append(device_dict)

    return devices


def get_track_uri(search_query):
    """Return the track uri of the first search result"""
    search_result = sp.search(search_query, limit=1, offset=0, type='track',
                              market=None)
    if search_result['tracks']['total'] == 0:
        print("Unable to find any matching songs!")
        return False
    else:
        track_uri = search_result['tracks']['items'][0]['uri']
        return track_uri


def playback_from_search(search_query):
    """
    Start playback from given search query by using
    the search method to get the query song uri and
    then plays the uri using the start_playback method.
    """
    track_uri = get_track_uri(search_query)
    if track_uri:
        if is_active():
            sp.start_playback(uris=[track_uri])
        else:
            print("No active device found!")
    else:
        return False


def get_user_playlists():
    """Returns dict of user playlists with corresponding uris."""
    playlists_info = sp.current_user_playlists(limit=50, offset=0)['items']
    playlists = []
    for playlist in playlists_info:
        playlist_dict = {}
        playlist_dict['uri'] = playlist['uri']
        playlist_dict['name'] = playlist['name']
        playlists.append(playlist_dict)
    return playlists
        

def get_playlist_uri(playlist_query):
    """Returns the playlist uri corresponding to the playlist_query."""
    playlist_uri = []
    user_playlists = get_user_playlists()
    for playlist in user_playlists:
        if playlist['name'] == playlist_query:
            playlist_uri.append(playlist['uri'])
    # Note that items to add needs to be in a list.
    if not playlist_uri:
        print(f'Playlist {playlist_query} not found!')
        return False
    else:
        return playlist_uri[0]


def add_track_to_playlist(playlist_query, track_uri):
    """
    Adds the track corresponding to given track_uri
    to the given user playlist.
    Note: playlist is the name of the playlist as a
    string, so if incorrect spelling will not add.
    """
    playlist_uri = get_playlist_uri(playlist_query)
    if not playlist_uri:
        return False
    else:
        sp.playlist_add_items(playlist_uri, [track_uri])

    
def queue_query(search_query):
    """
    Get the uri of the search query and add the
    corresponding track to the queue."""
    track_uri = get_track_uri(search_query)
    if track_uri:
        sp.add_to_queue(track_uri)
    else:
        return False


def skip_time(seek_time):
    """
    Fastforward or rewind currently playing song by
    seek_time milliseconds.
    """
    current_position = int(sp.current_user_playing_track()['progress_ms'])
    sp.seek_track(current_position + int(seek_time))


def is_active():
    currently_playing = sp.current_user_playing_track()
    if currently_playing is None:
        return False
    else:
        return True

    
def switch_playback():
    """Switch playback to next active device."""
    if is_active():
        devices = get_devices()
        inactive_devices = []
        for device in devices:
            if not device['is_active']:
                inactive_devices.append(device['id'])

        if not inactive_devices:
            print("Only one active device!")
        else:
            device_id = inactive_devices[0]
            sp.transfer_playback(device_id, force_play=True)
    else:
        print('No active devices found!')


def toggle_shuffle():
    """Get current playback shuffle state and toggle."""
    current_playback_info = sp.current_playback()
    shuffle_state = current_playback_info['shuffle_state'] 
    sp.shuffle(not shuffle_state)


def get_artist_uri(artist_query):
    search_result = sp.search(artist_query, limit=1, offset=0,
                              type='artist', market=None)
    if not search_result['artists']['items']: # if no artist are found 
        print(f"No artist by the name of {artist_query} found!")
        return False
    else:
        artist_uri = search_result['artists']['items'][0]['uri']
        return artist_uri


def get_last_tracks_uri(playlist_query, track_num):
    """Returns a list of the uris of the last track_num tracks from a playlist."""
    playlist_uri = get_playlist_uri(playlist_query)
    if not playlist_uri:
        return False
    else:
        # playlist_tracks = sp.user_playlist_tracks(playlist_id=playlist_uri, limit=5, offset=0)
        playlist_len = sp.playlist_items(playlist_uri, fields='total', limit=1)['total']
        offset = int(playlist_len) - int(track_num)
        tracks = sp.playlist_tracks(playlist_uri, offset=offset, fields='items')['items']
        track_uris = [track['track']['uri'] for track in tracks]
        return track_uris


def queue_recommended(playlist_query, num_tracks):
    """
    Find and queue num_tracks recommended songs,
    based on the last 5 songs from the given playlist.
    """
    seed_track_uris = get_last_tracks_uri(playlist_query, 5)
    if not seed_track_uris:
        return False
    else:
        recommended_tracks = sp.recommendations(seed_tracks=seed_track_uris,
                                                limit=int(num_tracks))
    
        recommended_uris = [track['uri'] for track in recommended_tracks['tracks']] 
        for track_uri in recommended_uris:
            sp.add_to_queue(track_uri)


def toggle_play_pause():
    """Toggle play or pause."""
    if is_active():
        is_playing = sp.current_user_playing_track()['is_playing']
        if is_playing:
            sp.pause_playback()
        else:
            sp.start_playback()
    else:
        pass

def queue_last_n_songs(playlist, n):
    """Queue the last n songs from a playlist."""
    track_uris = get_last_tracks_uri(playlist, n)
    if not track_uris:
        return False
    else:
        for uri in track_uris:
            sp.add_to_queue(uri)
            

def main():
    parser = argparse.ArgumentParser(description='Control Spotify Playback',
                                     formatter_class=RawTextHelpFormatter)

    parser.add_argument('action', help='''[action] options:
    
    [toggle] : toggle play/pause depending on current state,

    [play] : resume/start current playback,

    [pause] : pause current playback,

    [next] : skip current track,

    [prev] : previous track,

    [skip] : skip the current song by -t time, in ms,

    [search] : prompt for a song with dmenu and play,

    [queue] : prompt for a song with dmenu and add to queue,

    [recommend] : prompt for a playlist to base recommendations
    off with dmenu, using the last 5 songs from the
    playlist to find and queue 5 recommended songs.

    [switch] : switch playback to next available device,

    [transfer] : prompt for a device with dmenu and switch to it,

    [devices] : list currently active devices,

    [current] : get currently playing song,

    [add] : dmenu prompt for a playlist to add the currently playing song to, 

    [last] : dmenu prompt to queue the last n songs from a playlist,

    [playlists] : list current users playlists.''')

    parser.add_argument('-t', '--time', help='Time flag, used with skip action.')

    args = parser.parse_args()

    if args.action == 'toggle':
        toggle_play_pause()

    if args.action == 'play':
        if is_active():
            sp.start_playback()
        else:
            print('No active devices!')

    elif args.action == 'pause':
        if is_active():
            sp.pause_playback()
        else:
            print('No active devices!')

    elif args.action == 'skip':
        if args.time is None:
            print("Please specify a time to skip in ms with the -t flag.")
        else:
            skip_time(args.time)

    elif args.action == 'search':
        song = dmenu.show(["<"],
                          prompt="Song to play:",
                          background_selected='#1DB954',
                          foreground_selected='#000000')
        if song is None:
            pass
        else:
            playback_from_search(song)
            search_result = get_currently_playing()
            song_and_artist = search_result['song'] + \
                ' - ' + search_result['artist']
            notification(f'Now playing {song_and_artist}.',
                         title='Spcom')
            
    elif args.action == 'queue':
        song = dmenu.show(["<"],
                          prompt="Song to queue:",
                          background_selected='#1DB954',
                          foreground_selected='#000000')
        if song is None:
            pass
        else:
            try:
                if not queue_query(song):
                    notification(f'{song} not found!.', title='Error!')
                else:
                    queue_query(song)
                    notification(f'{song} added to queue.', title='Spcom')

            except spotipy.exceptions.SpotifyException:
                notification('No active device found!', title='Error!')

    elif args.action == 'recommend':
        playlists = get_user_playlists()
        playlist_names = [playlist['name'] for playlist in playlists]
        playlist = dmenu.show(playlist_names, lines=len(playlist_names),
                              prompt="Playlists:",
                              background_selected='#1DB954',
                              foreground_selected='#000000')
        if playlist is None:
            notification("No playlist given!", title='Error!')
        else:
            queue_recommended(playlist, 5)
            notification(f"Added 5 recommended songs based on {playlist}",
                         title="Spcom")

    elif args.action == 'current':
        current = get_currently_playing()
        print(current['song'] + ' - ' + current['artist'])

    elif args.action == 'add':
        if not is_active():
            notification('No song currently playing!', title='Error!')
        else:
            playlists = get_user_playlists()
            playlist_names = [playlist['name'] for playlist in playlists]
            playlist = dmenu.show(playlist_names,
                                  lines=len(playlist_names),
                                  prompt="Playlists:",
                                  background_selected='#1DB954',
                                  foreground_selected='#000000')

            if playlist is None:
                pass
            else:
                song = get_currently_playing()['song']
                track_uri = get_track_uri(song)
                add_track_to_playlist(playlist, track_uri)
                notification(f'Added {song} to {playlist}')

    elif args.action == 'playlists':
        playlists = get_user_playlists()
        playlist_names = [playlist['name'] for playlist in playlists]
        dmenu.show(playlist_names, lines=len(playlist_names),
                   prompt="Playlists:",
                   background_selected='#1DB954',
                   foreground_selected='#000000')

    elif args.action == 'devices':
        devices = get_devices()
        # for device in devices:
            # print('Device name: {}, id: {}'.format(device['name'], device['id']))
        device_list = [device['name'] for device in devices]
        dmenu.show(device_list, prompt="Active Devices: ",
                   lines=len(device_list),
                   background_selected='#1DB954',
                   foreground_selected='#000000')

    elif args.action == 'transfer':
        if not is_active():
            notification('No active devices!', title='Error!')
        else:
            all_devices = get_devices()
            devices = [device['name'] for device in all_devices]
            device_name = dmenu.show(devices, lines=len(devices),
                                     prompt="Switch device to:",
                                     background_selected='#1DB954',
                                     foreground_selected='#000000')
            for device in all_devices:
                if device_name == device['name']:
                    chosen_device_id = device['id']

            sp.transfer_playback(device_id=chosen_device_id,
                                 force_play=True)
            notification('Now playing from {}'.format(device_name))

    elif args.action == 'switch':
        switch_playback()

    elif args.action == 'next':
        sp.next_track()
        current = get_currently_playing()
        song_and_artist = current['song'] + ' - ' + current['artist']
        notification(f"Now playing {song_and_artist}", title="Spcom")

    elif args.action == 'prev':
        sp.previous_track()
        current = get_currently_playing()
        song_and_artist = current['song'] + ' - ' + current['artist']
        notification(f"Now playing {song_and_artist}", title="Spcom")

    elif args.action == 'last':
        if not is_active():
            notification('No active devices!', title='Error!')
        else:
            playlists = get_user_playlists()
            playlist_names = [playlist['name'] for playlist in playlists]
            playlist = dmenu.show(playlist_names, lines=len(playlist_names),
                                  prompt="Playlists:",
                                  background_selected='#1DB954',
                                  foreground_selected='#000000')
            num_songs = dmenu.show(["<"], prompt="Num. songs to queue:",
                                   background_selected='#1DB954',
                                   foreground_selected='#000000')
            queue_last_n_songs(playlist, num_songs)
            notification(f"Queued last {num_songs} from {playlist}")
            
    elif args.action == 'shuffle':
        if not is_active():
            notification('No active devices!', title='Error!')
        else:
            toggle_shuffle()
            current_playback_info = sp.current_playback()
            shuffle_state = current_playback_info['shuffle_state'] 
            notification(f'Shuffle mode {shuffle_state}', title='Spcom')

    else:
        print(f'{args.action} is not a valid argument! See -h for available actions.')


if __name__ == '__main__':
    main()

    
