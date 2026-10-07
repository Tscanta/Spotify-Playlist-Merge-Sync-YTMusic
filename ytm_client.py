from ytmusicapi import YTMusic


class YouTubeMusicClient:

    def __init__(self, auth_file="browser.json"):
        self.ytmusic = YTMusic(auth_file)

    def get_playlists(self):
        return self.ytmusic.get_library_playlists(
            limit=None
        )

    def get_playlist_tracks(self, playlist_id):
        result = self.ytmusic.get_playlist(
            playlist_id,
            limit=None,
        )

        tracks = []

        for item in result.get("tracks", []):
            video_id = item.get("videoId")

            if not video_id:
                continue

            artists = []

            for artist in item.get("artists", []):
                name = artist.get("name")

                if name:
                    artists.append(name)

            tracks.append({
                "video_id": video_id,
                "name": item.get("title", "").strip(),
                "artists": artists,
                "duration_seconds": item.get(
                    "duration_seconds"
                ),
            })

        return tracks

    def create_playlist(self, name):
        return self.ytmusic.create_playlist(
            title=name,
            description=f"Synced from Spotify: {name}",
            privacy_status="PRIVATE",
        )

    def search_track(self, name, artists):
        query = f"{name} {' '.join(artists)}"

        results = self.ytmusic.search(
            query,
            filter="songs",
            limit=10,
        )

        return results

    def add_tracks(self, playlist_id, video_ids):
        if not video_ids:
            return None

        return self.ytmusic.add_playlist_items(
            playlist_id,
            videoIds=video_ids,
            duplicates=False,
        )