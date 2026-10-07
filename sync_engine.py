import sys
import webbrowser

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

def ask_user_for_match(
    spotify_track,
    candidates,
):
    """
    Show the best YouTube Music candidates and let the user
    manually select one.

    Returns:
        candidate dict
        None if skipped
    """

    print("\n")
    print("=" * 60)
    print("              UNCERTAIN MATCH")
    print("=" * 60)

    spotify_name = spotify_track.get(
        "name",
        "",
    )

    spotify_artists = ", ".join(
        spotify_track.get(
            "artists",
            [],
        )
    )

    print("\nSpotify:")
    print(
        f"  {spotify_name} — "
        f"{spotify_artists}"
    )

    print("\nYouTube Music candidates:")

    # Only show the top 3.
    shown_candidates = candidates[:3]

    for index, candidate in enumerate(
        shown_candidates,
        1,
    ):
        print("\n" + "-" * 55)

        print(
            f"[{index}] "
            f"{candidate['name']}"
        )

        artists = ", ".join(
            candidate.get(
                "artists",
                [],
            )
        )

        if artists:
            print(
                f"    Artist: {artists}"
            )

        if candidate.get("album"):
            print(
                f"    Album: "
                f"{candidate['album']}"
            )

        print(
            f"    Score: "
            f"{candidate['score']}"
        )

        versions = candidate.get(
            "versions",
            [],
        )

        if versions:
            print(
                f"    Version: "
                f"{', '.join(versions)}"
            )

        video_id = candidate.get(
            "video_id"
        )

        if video_id:
            url = (
                "https://music.youtube.com/"
                f"watch?v={video_id}"
            )

            print(
                f"    Link: {url}"
            )

    print("\n" + "-" * 55)

    print("[S] Skip this song")

    while True:

        choice = input(
            "\nChoose a match "
            "[1-3/S]: "
        ).strip().lower()

        if choice == "s":
            print(
                "  → Skipped."
            )
            return None

        if choice.isdigit():

            number = int(choice)

            if 1 <= number <= len(
                shown_candidates
            ):
                selected = shown_candidates[
                    number - 1
                ]

                print(
                    f"  ✓ Selected: "
                    f"{selected['name']}"
                )

                return selected

        print(
            "  Invalid choice. "
            "Enter 1, 2, 3, or S."
        )


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

        # --------------------------------------
        # BEST CANDIDATE
        # --------------------------------------

        best = candidates[0]

        second_score = (
            candidates[1]["score"]
            if len(candidates) > 1
            else 0
        )

        best_score = best["score"]

        gap = (
            best_score - second_score
            if len(candidates) > 1
            else best_score
        )

    # ------------------------------------------------------
    # VERY HIGH CONFIDENCE
    # ------------------------------------------------------
    # If the best candidate is 90+, trust it even if
    # another candidate is also above 90.

        if best_score >= 90:
            tracks_to_add.append(best["video_id"])
            automatic_matches += 1
            progress(index,total)
            continue

    # ------------------------------------------------------
    # NORMAL HIGH CONFIDENCE
    # ------------------------------------------------------
    # Below 90, require a clear gap between candidates.

        if ( best_score >= 70 and gap >= 8 ):
            tracks_to_add.append(best["video_id"])
            automatic_matches += 1
            progress(index,total)
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