import sys
import time

from track_matcher import find_best_match


def normalize(text):
    return " ".join(
        text.lower().strip().split()
    )


def find_ytm_playlist(
    ytm_playlists,
    spotify_name,
):
    target = normalize(
        spotify_name
    )

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


def sync_playlist(
    spotify_client,
    ytm_client,
    spotify_playlist,
    ytm_playlists,
):
    name = spotify_playlist["name"]
    spotify_id = spotify_playlist["id"]

    print(f"\n▶ {name}")

    spotify_tracks = (
        spotify_client.get_tracks(
            spotify_id
        )
    )

    print(
        f"  Spotify tracks: "
        f"{len(spotify_tracks)}"
    )

    # ------------------------------------------
    # FIND OR CREATE PLAYLIST
    # ------------------------------------------

    ytm_playlist = find_ytm_playlist(
        ytm_playlists,
        name,
    )

    if not ytm_playlist:

        print(
            "  ⚠ YT Music playlist doesn't exist."
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
                normalize(track["name"]),
                tuple(
                    normalize(a)
                    for a in track["artists"]
                ),
            )
        )

    tracks_to_add = []
    unmatched = []
    already_exists = 0

    print("\n  Searching tracks...")

    total = len(spotify_tracks)

    for index, track in enumerate(
        spotify_tracks,
        1,
    ):

        key = (
            normalize(track["name"]),
            tuple(
                normalize(a)
                for a in track["artists"]
            ),
        )

        if key in existing:

            already_exists += 1

            progress(index, total)

            continue

        results = ytm_client.search_track(
            track["name"],
            track["artists"],
        )

        match = find_best_match(
            track,
            results,
        )

        if match:

            tracks_to_add.append(
                match["video_id"]
            )

        else:

            unmatched.append(track)

        progress(index, total)

    # ------------------------------------------
    # SUMMARY
    # ------------------------------------------

    print(
        f"\n  Already present: "
        f"{already_exists}"
    )

    print(
        f"  Matches to add: "
        f"{len(tracks_to_add)}"
    )

    print(
        f"  Unmatched: "
        f"{len(unmatched)}"
    )

    # ------------------------------------------
    # ADD
    # ------------------------------------------

    if tracks_to_add:

        print(
            "\n  Adding matched tracks..."
        )

        for start in range(
            0,
            len(tracks_to_add),
            50,
        ):

            batch = tracks_to_add[
                start:start + 50
            ]

            ytm_client.add_tracks(
                ytm_playlist_id,
                batch,
            )

            progress(
                min(
                    start + len(batch),
                    len(tracks_to_add),
                ),
                len(tracks_to_add),
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
            "\n  Could not confidently match:"
        )

        for track in unmatched:

            print(
                f"    ⚠ {track['name']} — "
                f"{', '.join(track['artists'])}"
            )

    print(
        f"\n  ✓ Finished: {name}"
    )


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
        "\nThis will MODIFY your YouTube Music account."
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
        "  - It will NOT remove YT Music tracks"
    )

    print(
        "  - It will NOT modify Spotify"
    )

    confirmation = input(
        "\nProceed with sync? [y/N]: "
    ).strip().lower()

    if confirmation != "y":
        print(
            "\nSync cancelled. Nothing changed."
        )
        return

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