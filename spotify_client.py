import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth


def login():
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
            scope="playlist-read-private playlist-read-collaborative user-library-read",
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

    # Add Spotify Liked Songs as a special "playlist"
    liked_count = sp.current_user_saved_tracks(limit=1)["total"]

    playlists.append({
        "id": "liked_songs",
        "name": "❤️ Liked Songs",
        "tracks": {
            "total": liked_count
        },
        "is_liked_songs": True,
    })

    return playlists


def get_tracks(sp, playlist_id):
    # Special case: Spotify Liked Songs
    if playlist_id == "liked_songs":
        return get_liked_tracks(sp)

    tracks = []

    results = sp.playlist_items(
        playlist_id,
        limit=100,
        fields="items(track(id,name,duration_ms,album(name),artists(name),is_local)),next",
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
                "album": track["album"]["name"],
                "duration_seconds": track["duration_ms"] / 1000,
            })

        if results["next"]:
            results = sp.next(results)
        else:
            break

    return tracks


def get_liked_tracks(sp):
    tracks = []

    results = sp.current_user_saved_tracks(limit=50)

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
                "album": track["album"]["name"],
                "duration_seconds": track["duration_ms"] / 1000,
            })

        if results["next"]:
            results = sp.next(results)
        else:
            break

    return tracks