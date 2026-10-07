import json
import os

from dotenv import load_dotenv

import spotify_client
from ytm_client import YouTubeMusicClient
import sync_engine


load_dotenv()


CONFIG_FILE = "sync_config.json"
YT_AUTH_FILE = "browser.json"


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"playlists": []}

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


# --------------------------------------------------
# PLAYLIST MANAGEMENT
# --------------------------------------------------

def add_playlists(
    spotify_playlists,
    config,
):
    print("\n" + "=" * 50)
    print("             ADD PLAYLISTS")
    print("=" * 50)

    existing = {
        playlist["id"]
        for playlist in config["playlists"]
    }

    available = [
        playlist
        for playlist in spotify_playlists
        if playlist["id"] not in existing
    ]

    if not available:
        print("\nAll playlists are already selected.")
        return

    for i, playlist in enumerate(
        available,
        1,
    ):
        print(
            f"{i}. {playlist['name']} "
            f"({playlist['tracks']['total']} tracks)"
        )

    print("\nExample: 1,3,5")
    print("Or type 'all'.")

    while True:
        choice = input(
            "\nSelect playlists: "
        ).strip().lower()

        if choice == "all":
            selected = available
            break

        try:
            numbers = [
                int(x.strip())
                for x in choice.split(",")
            ]

            if not numbers:
                raise ValueError

            selected = []

            for number in numbers:
                if not 1 <= number <= len(available):
                    raise ValueError

                playlist = available[number - 1]

                if playlist not in selected:
                    selected.append(playlist)

            break

        except ValueError:
            print("Invalid selection.")

    for playlist in selected:

        config["playlists"].append({
            "id": playlist["id"],
            "name": playlist["name"],
        })

        print(
            f"✓ Added: {playlist['name']}"
        )

    save_config(config)


def remove_playlists(config):

    if not config["playlists"]:
        print("\nNo playlists selected.")
        return

    print("\n" + "=" * 50)
    print("           REMOVE PLAYLISTS")
    print("=" * 50)

    for i, playlist in enumerate(
        config["playlists"],
        1,
    ):
        print(
            f"{i}. {playlist['name']}"
        )

    choice = input(
        "\nRemove: "
    ).strip()

    try:
        numbers = [
            int(x.strip())
            for x in choice.split(",")
        ]

        if any(
            number < 1
            or number > len(config["playlists"])
            for number in numbers
        ):
            raise ValueError

    except ValueError:
        print("Invalid selection.")
        return

    for number in sorted(
        set(numbers),
        reverse=True,
    ):
        playlist = config["playlists"].pop(
            number - 1
        )

        print(
            f"✓ Removed: {playlist['name']}"
        )

    save_config(config)


def show_saved_playlists(config):

    print("\n" + "=" * 50)
    print("           SAVED SYNC PLAYLISTS")
    print("=" * 50)

    if not config["playlists"]:
        print("\nNo playlists selected.")
        return

    for i, playlist in enumerate(
        config["playlists"],
        1,
    ):
        print(
            f"{i}. {playlist['name']}"
        )


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    print("=" * 50)
    print("       SPOTIFY → YOUTUBE MUSIC SYNC")
    print("=" * 50)

    if not os.path.exists(YT_AUTH_FILE):
        print(
            "\nERROR: browser.json was not found."
        )
        return

    print("\nConnecting to Spotify...")

    sp = spotify_client.login()

    print("Connecting to YouTube Music...")

    ytm = YouTubeMusicClient(
        YT_AUTH_FILE
    )

    print("Connected successfully.")

    spotify_playlists = (
        spotify_client.get_playlists(sp)
    )

    config = load_config()

    while True:

        print("\n" + "=" * 50)
        print("                    MENU")
        print("=" * 50)

        print("\n1. Sync playlists")
        print("2. Add playlists")
        print("3. Remove playlists")
        print("4. Show saved playlists")
        print("5. Exit")

        choice = input(
            "\nChoose: "
        ).strip()

        if choice == "1":

            sync_engine.sync(
                sp,
                ytm,
                spotify_playlists,
                config,
            )

        elif choice == "2":

            add_playlists(
                spotify_playlists,
                config,
            )

            config = load_config()

        elif choice == "3":

            remove_playlists(config)

            config = load_config()

        elif choice == "4":

            show_saved_playlists(config)

        elif choice == "5":

            print("\nGoodbye.")
            break

        else:

            print(
                "\nInvalid choice."
            )


if __name__ == "__main__":
    main()