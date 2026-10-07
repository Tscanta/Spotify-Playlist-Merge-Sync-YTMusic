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
            Tiered YouTube Music search.

            Starts with the most precise query and only performs
            broader searches when the previous search does not
            produce enough useful candidates.

            This reduces API requests for normal tracks while
            still giving difficult tracks additional chances.
            """

            artist_text = " ".join(artists).strip()

            queries = [
                # Tier 1 — precise
                f"{name} {artist_text}".strip(),

                # Tier 2 — title only
                name.strip(),

                # Tier 3 — artist + title
                f"{artist_text} {name}".strip(),
            ]

            # Remove duplicate queries
            unique_queries = []

            for query in queries:
                if query and query not in unique_queries:
                    unique_queries.append(query)

            candidates = []
            seen_video_ids = set()

            def collect(results):
                new_count = 0

                for result in results:
                    candidate = self._normalize_search_result(result)

                    if not candidate:
                        continue

                    video_id = candidate["video_id"]

                    if video_id in seen_video_ids:
                        continue

                    seen_video_ids.add(video_id)
                    candidates.append(candidate)
                    new_count += 1

                return new_count

            # =========================================================
            # TIER 1 — Exact title + artist
            # =========================================================

            try:
                results = self.ytmusic.search(
                    unique_queries[0],
                    filter="songs",
                    limit=10,
                    ignore_spelling=False,
                )

                collect(results)

            except Exception:
                pass

            # If we already have useful results, stop here.
            if len(candidates) >= 5:
                return candidates

            # =========================================================
            # TIER 2 — Title only
            # =========================================================

            if len(unique_queries) >= 2:

                try:
                    results = self.ytmusic.search(
                        unique_queries[1],
                        filter="songs",
                        limit=10,
                        ignore_spelling=False,
                    )

                    collect(results)

                except Exception:
                    pass

            # If we now have enough candidates, stop.
            if len(candidates) >= 5:
                return candidates

            # =========================================================
            # TIER 3 — Artist + title
            # =========================================================

            if len(unique_queries) >= 3:

                try:
                    results = self.ytmusic.search(
                        unique_queries[2],
                        filter="songs",
                        limit=10,
                        ignore_spelling=True,
                    )

                    collect(results)

                except Exception:
                    pass

            # =========================================================
            # TIER 4 — Broad/unfiltered search
            #
            # Only used when the previous searches produced
            # very little.
            # =========================================================

            if len(candidates) < 3:

                try:
                    results = self.ytmusic.search(
                        unique_queries[0],
                        limit=10,
                        ignore_spelling=True,
                    )

                    collect(results)

                except Exception:
                    pass

            return candidates

    def search_track_tier(self, name, artists, tier):
            artist_text = " ".join(artists).strip()

            if tier == 1:
                queries = [f"{name} {artist_text}".strip()]
                options = {
                    "filter": "songs",
                    "limit": 10,
                    "ignore_spelling": False,
                }

            elif tier == 2:
                queries = [name.strip()]
                options = {
                    "filter": "songs",
                    "limit": 10,
                    "ignore_spelling": False,
                }

            elif tier == 3:
                queries = [f"{artist_text} {name}".strip()]
                options = {
                    "filter": "songs",
                    "limit": 10,
                    "ignore_spelling": True,
                }

            else:
                queries = [f"{name} {artist_text}".strip()]
                options = {
                    "limit": 10,
                    "ignore_spelling": True,
                }

            candidates = []
            seen = set()

            for query in queries:
                try:
                    results = self.ytmusic.search(query, **options)

                    for result in results:
                        candidate = self._normalize_search_result(result)

                        if not candidate:
                            continue

                        video_id = candidate["video_id"]

                        if video_id in seen:
                            continue

                        seen.add(video_id)
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