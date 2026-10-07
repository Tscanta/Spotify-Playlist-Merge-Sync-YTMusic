import sys
import webbrowser
import re
import spotify_client as spotify_api
from track_matcher import (
    find_best_match,
    rank_candidates,
)


def normalize(text):
    return " ".join(
        text.lower().strip().split()
    )


def find_ytm_playlist(
    ytm_playlists,
    spotify_name,
):
    target = normalize(spotify_name)

    for playlist in ytm_playlists:
        if normalize(
            playlist.get("title", "")
        ) == target:
            return playlist

    return None


def find_spotify_playlist(
    spotify_playlists,
    playlist_id,
):
    for playlist in spotify_playlists:
        if playlist["id"] == playlist_id:
            return playlist

    return None


def progress(current, total):
    width = 30

    ratio = current / total if total else 1

    filled = int(width * ratio)

    bar = (
        "█" * filled
        + "░" * (width - filled)
    )

    percent = int(ratio * 100)

    sys.stdout.write(
        f"\r    [{bar}] "
        f"{percent:3d}% "
        f"({current}/{total})"
    )

    sys.stdout.flush()

    if current == total:
        print()


# ============================================================
# MANUAL MATCH SELECTION
# ============================================================

def ask_user_for_match(spotify_track, candidates):
    print()
    print("=" * 55)
    print("                  UNCERTAIN MATCH")
    print("=" * 55)

    print()
    print("Spotify:")
    print(
        f"    {spotify_track['name']} — "
        f"{', '.join(spotify_track['artists'])}"
    )

    print()
    print("YouTube Music candidates:")
    print()

    for index, candidate in enumerate(candidates[:3], start=1):
        print("-" * 55)

        print(f"[{index}] {candidate.get('name', 'Unknown')}")

        artists = candidate.get("artists", [])
        if artists:
            print(f"    Artist: {', '.join(artists)}")

        album = candidate.get("album")
        if album:
            print(f"    Album: {album}")

        print(f"    Score: {candidate.get('score', 0)}")

        video_id = candidate.get("video_id")

        if video_id:
            print(
                "    Link: "
                f"https://music.youtube.com/watch?v={video_id}"
            )

    print()
    print("[L] Enter YouTube Music link manually")
    print("[S] Skip")

    while True:
        choice = input("\nChoose: ").strip()

        # -------------------------------------------------
        # Select one of the displayed candidates
        # -------------------------------------------------

        if choice.isdigit():
            number = int(choice)

            if 1 <= number <= min(3, len(candidates)):
                return candidates[number - 1]

            print("Invalid candidate number.")
            continue

        # -------------------------------------------------
        # Manual YouTube Music link
        # -------------------------------------------------

        if choice.lower() == "l":

            while True:
                link = input(
                    "\nPaste YouTube Music link: "
                ).strip()

                video_id = extract_youtube_video_id(link)

                if not video_id:
                    print(
                        "Could not extract a YouTube Music "
                        "video ID from that link."
                    )
                    print(
                        "Example:"
                    )
                    print(
                        "https://music.youtube.com/watch?v=XXXXXXXXXXX"
                    )
                    continue

                print()
                print(
                    f"Manual track selected: {video_id}"
                )

                return {
                    "video_id": video_id,
                    "manual": True,
                    "score": 100,
                }

        # -------------------------------------------------
        # Skip
        # -------------------------------------------------

        if choice.lower() == "s":
            return None

        print("Invalid choice. Enter 1, 2, 3, L, or S.")


def extract_youtube_video_id(link):
    """
    Extract a YouTube / YouTube Music video ID.

    Supports:

        https://music.youtube.com/watch?v=XXXXXXXXXXX

        https://www.youtube.com/watch?v=XXXXXXXXXXX

        https://youtu.be/XXXXXXXXXXX
    """

    if not link:
        return None

    link = link.strip()

    patterns = [
        r"[?&]v=([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"youtube\.com/shorts/([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, link)

        if match:
            return match.group(1)

    # Allow the user to paste just the video ID.
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", link):
        return link

    return None


# ============================================================
# SYNC ONE PLAYLIST
# ============================================================

def sync_playlist(
    sp,
    ytm_client,
    spotify_playlist,
    ytm_playlists,
    manual_mode=True,
):
    name = spotify_playlist["name"]

    print(f"\n▶ {name}")

    # ------------------------------------------
    # GET SPOTIFY TRACKS
    # ------------------------------------------

    spotify_tracks = spotify_api.get_tracks(
        sp,
        spotify_playlist["id"],
    )

    print(
        f"  Spotify tracks: "
        f"{len(spotify_tracks)}"
    )

    # ------------------------------------------
    # FIND OR CREATE YT MUSIC PLAYLIST
    # ------------------------------------------

    ytm_playlist = find_ytm_playlist(
        ytm_playlists,
        name,
    )

    if not ytm_playlist:

        print(
            "  ⚠ YT Music playlist "
            "doesn't exist."
        )

        print(
            "  → Creating it..."
        )

        ytm_playlist_id = (
            ytm_client.create_playlist(
                name
            )
        )

        if not isinstance(
            ytm_playlist_id,
            str,
        ):
            print(
                "  ✗ Playlist creation failed."
            )
            return

        print(
            f"  ✓ Created '{name}'"
        )

        ytm_tracks = []

    else:

        ytm_playlist_id = (
            ytm_playlist["playlistId"]
        )

        ytm_tracks = (
            ytm_client.get_playlist_tracks(
                ytm_playlist_id
            )
        )

        print(
            f"  YT Music tracks: "
            f"{len(ytm_tracks)}"
        )

    # ------------------------------------------
    # EXISTING TRACKS
    # ------------------------------------------

    existing = set()

    for track in ytm_tracks:

        existing.add(
            (
                normalize(
                    track.get(
                        "name",
                        "",
                    )
                ),
                tuple(
                    normalize(a)
                    for a in track.get(
                        "artists",
                        [],
                    )
                ),
            )
        )

    tracks_to_add = []
    unmatched = []
    manually_selected = 0
    already_exists = 0
    automatic_matches = 0

    print("\n  Searching tracks...")

    total = len(spotify_tracks)

    # ------------------------------------------
    # MATCH TRACKS
    # ------------------------------------------

    for index, track in enumerate(
        spotify_tracks,
        1,
    ):

        track_name = track.get(
            "name",
            "",
        ).strip()

        track_artists = track.get(
            "artists",
            [],
        )

        # --------------------------------------
        # INVALID / EMPTY SPOTIFY TRACK
        # --------------------------------------

        if not track_name:

            unmatched.append(track)

            progress(
                index,
                total,
            )

            continue

        # --------------------------------------
        # EXISTING TRACK
        # --------------------------------------

        key = (
            normalize(track_name),
            tuple(
                normalize(a)
                for a in track_artists
            ),
        )

        if key in existing:

            already_exists += 1

            progress(
                index,
                total,
            )

            continue

        # --------------------------------------
        # SEARCH YOUTUBE MUSIC
        # --------------------------------------

        results = ytm_client.search_track(
            track_name,
            track_artists,
        )

        candidates = rank_candidates(
            track,
            results,
        )

        # --------------------------------------
        # NO RESULTS
        # --------------------------------------

        if not candidates:

            unmatched.append(track)

            progress(
                index,
                total,
            )

            continue

        best = candidates[0]
        best_score = best["score"]

        # ---------------------------------------------------------
        # Automatic matching
        #
        # 70+ is considered good enough.
        #
        # Candidate #1 is the highest-ranked result, so even if
        # candidate #2 has a similar score, we accept #1.
        # ---------------------------------------------------------

        if best_score >= 70:
            tracks_to_add.append(best["video_id"])
            automatic_matches += 1
            progress(index, total)
            continue

        # --------------------------------------
        # UNCERTAIN / LOW CONFIDENCE
        # --------------------------------------

        if manual_mode:

            selected = ask_user_for_match(
                track,
                candidates,
            )

            if selected:

                tracks_to_add.append(
                    selected["video_id"]
                )

                manually_selected += 1

        else:

            unmatched.append(track)

        progress(
            index,
            total,
        )

    # ------------------------------------------
    # SUMMARY
    # ------------------------------------------

    print(
        f"\n  Already present: "
        f"{already_exists}"
    )

    print(
        f"  Automatic matches: "
        f"{automatic_matches}"
    )

    print(
        f"  Manual matches: "
        f"{manually_selected}"
    )

    print(
        f"  Total to add: "
        f"{len(tracks_to_add)}"
    )

    print(
        f"  Unmatched/skipped: "
        f"{len(unmatched)}"
    )

    # ------------------------------------------
    # ADD TO YOUTUBE MUSIC
    # ------------------------------------------

    if tracks_to_add:

        print(
            "\n  Adding matched tracks..."
        )

        results = ytm_client.add_tracks(
            ytm_playlist_id,
            tracks_to_add,
        )

        added = 0
        failed = 0

        for result in results:

            if result["success"]:
                added += 1
            else:
                failed += 1

                print(
                    f"\n  ✗ Failed to add "
                    f"{result['video_id']}"
                )

                print(
                    f"    Reason: "
                    f"{result['error']}"
                )

        print(
            f"\n  Added successfully: {added}"
        )

        print(
            f"  Failed: {failed}"
        )

    else:

        print(
            "\n  ✓ Nothing new to add."
        )

    # ------------------------------------------
    # UNMATCHED
    # ------------------------------------------

    if unmatched:

        print(
            "\n  Could not match:"
        )

        for track in unmatched:

            track_name = track.get(
                "name",
                "",
            )

            artists = ", ".join(
                track.get(
                    "artists",
                    [],
                )
            )

            if track_name:

                print(
                    f"    ⚠ "
                    f"{track_name}"
                    f" — {artists}"
                )

            else:

                print(
                    "    ⚠ Empty/invalid "
                    "Spotify track"
                )

    print(
        f"\n  ✓ Finished: {name}"
    )


# ============================================================
# SYNC
# ============================================================

def sync(
    spotify_client,
    ytm_client,
    spotify_playlists,
    config,
):
    if not config["playlists"]:

        print(
            "\nNo playlists selected."
        )

        return

    print("\n" + "=" * 55)
    print("                 SYNC PREVIEW")
    print("=" * 55)

    print(
        "\nThis will MODIFY your "
        "YouTube Music account."
    )

    print(
        "Spotify will NOT be modified."
    )

    print("\nPlaylists selected:")

    for playlist in config["playlists"]:

        print(
            f"  • {playlist['name']}"
        )

    print(
        "\nThe current sync can:"
    )

    print(
        "  + Create missing YT Music playlists"
    )

    print(
        "  + Add confidently matched tracks"
    )

    print(
        "  + Let you manually choose "
        "uncertain matches"
    )

    print(
        "  - It will NOT remove "
        "YT Music tracks"
    )

    print(
        "  - It will NOT modify Spotify"
    )

    confirmation = input(
        "\nProceed with sync? [y/N]: "
    ).strip().lower()

    if confirmation != "y":

        print(
            "\nSync cancelled. "
            "Nothing changed."
        )

        return

    # ------------------------------------------
    # MATCHING MODE
    # ------------------------------------------

    print("\nMatching mode:")

    print(
        "  [1] Manual confirmation "
        "(recommended)"
    )

    print(
        "  [2] Automatic"
    )

    while True:

        mode = input(
            "\nChoose [1/2]: "
        ).strip()

        if mode == "1":

            manual_mode = True
            break

        if mode == "2":

            manual_mode = False
            break

        print(
            "  Invalid choice."
        )

    print("\nStarting sync...")

    ytm_playlists = (
        ytm_client.get_playlists()
    )

    for saved in config["playlists"]:

        spotify_playlist = (
            find_spotify_playlist(
                spotify_playlists,
                saved["id"],
            )
        )

        if not spotify_playlist:

            print(
                f"\n▶ {saved['name']}"
            )

            print(
                "  ⚠ Spotify playlist "
                "no longer exists."
            )

            continue

        try:

            sync_playlist(
                spotify_client,
                ytm_client,
                spotify_playlist,
                ytm_playlists,
                manual_mode,
            )

        except Exception as e:

            print(
                f"\n✗ Error syncing "
                f"{saved['name']}:"
            )

            print(
                f"  {type(e).__name__}: {e}"
            )

    print("\n" + "=" * 55)
    print("                 SYNC COMPLETE")
    print("=" * 55)

    print(
        "\nSpotify was not modified."
    )