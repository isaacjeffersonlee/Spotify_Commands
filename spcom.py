#!/usr/bin/env python

# Imports
import os
import argparse
from argparse import RawTextHelpFormatter
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
# import spotipy.util as util

### TODO ###
# 
# Integrate with dmenu for searching querys
# Client Credentials with an encrypted file
# Restructure with __main__ stuff and proper imports
# Make executable with pyinstaller

# Parsing Arguments


# Setting Environment Variables, could make this as command line inputs that get saved at a later date.
os.environ['SPOTIPY_CLIENT_ID'] = 'abb90ec72eab412c97d01276fc4ff11f'
os.environ['SPOTIPY_CLIENT_SECRET'] = 'dcd2dcd92b864340952306e0f674dda8'
os.environ['SPOTIPY_REDIRECT_URI'] = 'https://www.google.com/'

# Client Credentials
username = 'isaacjeffersonlee?si=IDXT-pNdRqaqGCdB4oOOHA'
scope = '''user-modify-playback-state user-top-read
user-library-modify user-follow-modify playlist-read-private
playlist-modify-public playlist-modify-private user-read-playback-state
user-read-currently-playing user-read-private user-follow-read
playlist-read-collaborative user-library-read'''

# token = util.prompt_for_user_token(username,
#                                    scope,
#                                    client_id='abb90ec72eab412c97d01276fc4ff11f',
#                                    client_secret='dcd2dcd92b864340952306e0f674dda8',
#                                    redirect_uri='https://www.google.com/')

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

# Spotipy Object
# sp = spotipy.Spotify(auth=token)


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
        offset = playlist_len - track_num
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


def main():
    parser = argparse.ArgumentParser(description='Control Spotify Playback',
                                     formatter_class=RawTextHelpFormatter)

    parser.add_argument('action', help='''[action] options:
    [play] : resume/start current playback,
    [pause] : pause current playback,
    [next] : skip current track,
    [prev] : previous track,
    [skip] : skip the current song by -t time, in ms,
    [search] : search and play a song, using -s flag,
    [queue] : search and queue a song, using -s flag,
    [recommend] : queue -n recommended songs, based on the last 5 songs from -p playlist,
    [switch] : switch/transfer playback to next available device,
    [devices] : list currently active devices,
    [current] : get currently playing song,
    [add] : add currently playing song to playlist, specified by -p playlist flag,
    [playlists] : list current users playlists.''')

    parser.add_argument('-s', '--song', help='Song flag, used with search action.')
    parser.add_argument('-p', '--playlist', help='Playlist flag, used with add action.')
    parser.add_argument('-t', '--time', help='Time flag, used with skip action.')
    parser.add_argument('-n', '--number', help='Number of songs flag, used with queue_recommended')
    args = parser.parse_args()

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
        if args.song is None:
            print("No song to search!")
            print("Please enter a song to search with -s flag.")
        else:
            playback_from_search(args.song)
            
    elif args.action == 'queue':
        if args.song is None:
            print("No song to queue!")
            print("Please enter a song to queue with -s flag.")
        else:
            queue_query(args.song)

    elif args.action == 'recommend':
        if args.playlist is None:
            print("No playlist specified!")
            print("Please enter a playlist to base recommendations off with -p flag.")
        elif args.number is None:
            print("No number specified!")
            print("Please specify the number of recommended songs to add to queue with -n flag.")
        else:
            queue_recommended(args.playlist, args.number)

    elif args.action == 'current':
        current = get_currently_playing()
        print(current['song'] + ' - ' + current['artist'])

    elif args.action == 'add':
        if args.playlist is None:
            print("No playlist given!")
            print("Please enter a playlist to search with -s flag.")
        else:
            song = get_currently_playing()['song']
            track_uri = get_track_uri(song)
            add_track_to_playlist(args.playlist, track_uri)

    elif args.action == 'playlists':
        playlists = get_user_playlists()
        print("User playlists: ")
        for playlist in playlists:
            print(playlist['name'] + ' - ' + playlist['uri'])

    elif args.action == 'devices':
        devices = get_devices()
        for device in devices:
            print('Device name: {}, id: {}'.format(device['name'], device['id']))

    elif args.action == 'switch':
        switch_playback()

    elif args.action == 'next':
        sp.next_track()

    elif args.action == 'prev':
        sp.previous_track()

    elif args.action == 'shuffle':
        toggle_shuffle()

    else:
        print(f'{args.action} is not a valid argument! See -h for available actions.')


if __name__ == '__main__':
    main()

    
