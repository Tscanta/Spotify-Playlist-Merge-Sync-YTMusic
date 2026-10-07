import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth


def login():
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
            scope="playlist-read-private playlist-read-collaborative",
            cache_path=".spotify_cache",
        )
    )


def get_playlists(sp):
    playlists = []
    results = sp.current_user_playlists(limit=50)

    while results:
        playlists.extend(results["items"])

        if results["next"]:
            results = sp.next(results)
        else:
            break

    return playlists


def get_tracks(sp, playlist_id):
    tracks = []

    results = sp.playlist_items(
        playlist_id,
        limit=100,
        fields="items(track(id,name,duration_ms,artists(name),is_local)),next",
    )

    while results:
        for item in results["items"]:
            track = item.get("track")

            if not track or track.get("is_local"):
                continue

            tracks.append({
                "id": track["id"],
                "name": track["name"],
                "artists": [
                    artist["name"]
                    for artist in track["artists"]
                ],
                "duration_seconds": (
                    track["duration_ms"] / 1000
                ),
            })

        if results["next"]:
            results = sp.next(results)
        else:
            break

    return tracks