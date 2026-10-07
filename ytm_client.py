from ytmusicapi import YTMusic


class YouTubeMusicClient:
    def __init__(self, auth_file="browser.json"):
        self.ytmusic = YTMusic(auth_file)

    def get_playlists(self):
        return self.ytmusic.get_library_playlists(limit=None)

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

            album = item.get("album")

            if isinstance(album, dict):
                album = album.get("name")

            tracks.append({
                "video_id": video_id,
                "name": item.get("title", "").strip(),
                "artists": artists,
                "album": album,
                "duration_seconds": item.get("duration_seconds"),
            })

        return tracks

    def create_playlist(self, name):
        return self.ytmusic.create_playlist(
            title=name,
            description=f"Synced from Spotify: {name}",
            privacy_status="PRIVATE",
        )

    def _normalize_search_result(self, result):
        """
        Convert a ytmusicapi search result into the format
        expected by track_matcher.py.
        """

        video_id = result.get("videoId")

        if not video_id:
            return None

        artists = []

        for artist in result.get("artists", []):
            if isinstance(artist, dict):
                name = artist.get("name")
            else:
                name = str(artist)

            if name:
                artists.append(name)

        album = result.get("album")

        if isinstance(album, dict):
            album = album.get("name")

        return {
            "video_id": video_id,
            "name": result.get("title", "").strip(),
            "artists": artists,
            "album": album,
            "duration_seconds": result.get("duration_seconds"),
            "result_type": result.get("resultType"),
            "category": result.get("category"),
            "views": result.get("views"),
            "raw": result,
        }

    def search_track(self, name, artists):
        """
        Search aggressively for a Spotify track.

        Multiple queries are used because YouTube Music's
        search ranking can miss valid songs when the exact
        Spotify title/artist combination is unusual.
        """

        artist_text = " ".join(artists)

        # Build several different searches.
        queries = [
            f"{name} {artist_text}",
            name,
            f"{artist_text} {name}",
        ]

        # Remove duplicate/empty queries.
        unique_queries = []

        for query in queries:
            query = query.strip()

            if query and query not in unique_queries:
                unique_queries.append(query)

        candidates = []
        seen_video_ids = set()

        for query in unique_queries:

            # -------------------------------------------------
            # Search 1: Songs with normal spelling correction
            # -------------------------------------------------

            try:
                results = self.ytmusic.search(
                    query,
                    filter="songs",
                    limit=20,
                    ignore_spelling=False,
                )

                for result in results:
                    candidate = self._normalize_search_result(result)

                    if not candidate:
                        continue

                    video_id = candidate["video_id"]

                    if video_id in seen_video_ids:
                        continue

                    seen_video_ids.add(video_id)
                    candidates.append(candidate)

            except Exception:
                pass

            # -------------------------------------------------
            # Search 2: Songs WITHOUT spelling correction
            # -------------------------------------------------

            try:
                results = self.ytmusic.search(
                    query,
                    filter="songs",
                    limit=20,
                    ignore_spelling=True,
                )

                for result in results:
                    candidate = self._normalize_search_result(result)

                    if not candidate:
                        continue

                    video_id = candidate["video_id"]

                    if video_id in seen_video_ids:
                        continue

                    seen_video_ids.add(video_id)
                    candidates.append(candidate)

            except Exception:
                pass

            # -------------------------------------------------
            # Search 3: Unfiltered search
            #
            # This can expose results that don't appear in
            # the "songs" filter.
            # -------------------------------------------------

            try:
                results = self.ytmusic.search(
                    query,
                    limit=20,
                    ignore_spelling=False,
                )

                for result in results:
                    candidate = self._normalize_search_result(result)

                    if not candidate:
                        continue

                    video_id = candidate["video_id"]

                    if video_id in seen_video_ids:
                        continue

                    seen_video_ids.add(video_id)
                    candidates.append(candidate)

            except Exception:
                pass

            # -------------------------------------------------
            # Search 4: Unfiltered + ignore spelling
            # -------------------------------------------------

            try:
                results = self.ytmusic.search(
                    query,
                    limit=20,
                    ignore_spelling=True,
                )

                for result in results:
                    candidate = self._normalize_search_result(result)

                    if not candidate:
                        continue

                    video_id = candidate["video_id"]

                    if video_id in seen_video_ids:
                        continue

                    seen_video_ids.add(video_id)
                    candidates.append(candidate)

            except Exception:
                pass

        return candidates

    def add_tracks(self, playlist_id, video_ids):
        if not video_ids:
            return []

        results = []

        for video_id in video_ids:
            try:
                result = self.ytmusic.add_playlist_items(
                    playlist_id,
                    videoIds=[video_id],
                    duplicates=False,
                )

                results.append({
                    "video_id": video_id,
                    "success": True,
                    "response": result,
                })

            except Exception as e:
                results.append({
                    "video_id": video_id,
                    "success": False,
                    "error": str(e),
                })

        return results