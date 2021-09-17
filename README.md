# Spotify_Commands

## Summary
Python command line tool to control Spotify playback from command line.
Uses the Spotipy python Spotify API

## Options
 Option  | Info
 --------|-----------------------------------
 [toggle] | toggle play/pause depending on current state,
 [play] | resume/start current playback,
 [pause] | pause current playback,
 [next] | skip current track,
 [prev] | previous track,
 [skip] | skip the current song by -t time, in ms,
 [search] | prompt for a song with dmenu and play,
 [queue] | prompt for a song with dmenu and add to queue,
 [recommend] | prompt for a playlist to recommend from, uses the last 5 songs from the playlist to find and queue 5 recommended songs.
 [switch] | switch playback to next available device,
 [transfer] | prompt for a device with dmenu and switch to it,
 [devices] | list currently active devices,
 [current] | get currently playing song,
 [add] | dmenu prompt for a playlist to add the currently playing song to, 
 [last] | dmenu prompt to queue the last n songs from a playlist,
 [playlists] | list current users playlists.

## Dependencies
```
pip install spotipy
pip install dmenu
pip install py-notifier
```
