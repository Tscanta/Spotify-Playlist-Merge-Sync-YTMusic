# SpotifyPlaylistMerger

A command-line Python project with **two independent features**:

1. **Spotify Playlist Merger** — merge multiple Spotify playlists into one Spotify playlist.
2. **Spotify → YouTube Music Sync** — transfer and update selected Spotify playlists on YouTube Music.

The two features are separate. You can use the merger without using the YouTube Music sync, and you can use the sync without merging playlists first.

---

## Features

### 1. Spotify Playlist Merger

The original feature of the project.

It lets you:

- Fetch your Spotify playlists
- Select multiple playlists
- Merge them into one Spotify playlist
- Remove duplicate tracks
- Work directly through the Spotify Web API
- Keep the workflow entirely in the terminal

**Run it with:**

```bash
python spotifyplaylistmerger.py
```

This feature is completely independent from the YouTube Music synchronization system.

---

### 2. Spotify → YouTube Music Sync

A separate tool for transferring and updating Spotify playlists on YouTube Music.

It lets you:

- Select multiple Spotify playlists for synchronization
- Save playlists for future syncs
- Add and remove saved playlists
- Automatically create missing YouTube Music playlists
- Detect tracks already present on YouTube Music
- Search YouTube Music for missing tracks
- Match tracks using title, artist, album, duration, and version information
- Automatically accept high-confidence matches
- Manually choose uncertain matches
- Skip tracks when no reliable match is available
- Run the sync whenever you want from the terminal

**Run it with:**

```bash
python spotify_to_ytm.py
```

Spotify is **read-only** during synchronization.

---

# Spotify Playlist Merger

## What It Does

Suppose you have:

```text
Rock
Metal
Anime
Favorites
```

You can select several playlists and combine them into one Spotify playlist:

```text
Rock
   \
Metal
    \
Anime  →  Combined Playlist
    /
Favorites
```

Duplicate songs are removed during the merge.

### Example

```bash
python spotifyplaylistmerger.py
```

Then select the Spotify playlists you want to combine and provide the name of the destination playlist.

The result is one Spotify playlist containing the tracks from the selected playlists.

### When to Use This

Use the merger when your goal is:

> "I have multiple Spotify playlists and I want one combined Spotify playlist."

You do **not** need YouTube Music for this feature.

---

# Spotify → YouTube Music Sync

## What It Does

The synchronization system works independently from the merger.

It uses:

```text
Spotify
   ↓
Read playlists and tracks
   ↓
Track matching engine
   ↓
Search YouTube Music
   ↓
Match tracks
   ↓
YouTube Music
```

Spotify acts as the source of truth.

The tool can create the corresponding YouTube Music playlist and add missing tracks.

### Example

Spotify:

```text
My Playlist
├── Song A
├── Song B
├── Song C
└── Song D
```

YouTube Music:

```text
My Playlist
├── Song A
└── Song B
```

After synchronization:

```text
My Playlist
├── Song A
├── Song B
├── Song C
└── Song D
```

The current sync is **additive**.

It does not currently remove extra YouTube Music tracks or reorder the playlist.

---

## Running the Sync

Run:

```bash
python spotify_to_ytm.py
```

The CLI provides:

```text
1. Sync playlists
2. Add playlists
3. Remove playlists
4. Show saved playlists
5. Exit
```

### First-Time Setup

Use:

```text
2. Add playlists
```

Select the Spotify playlists you want the sync tool to remember.

You can later view them with:

```text
4. Show saved playlists
```

Remove saved playlists with:

```text
3. Remove playlists
```

Then use:

```text
1. Sync playlists
```

to synchronize the saved playlists.

---

## Sync Matching Modes

Before synchronization, the tool asks for a matching mode:

```text
[1] Manual confirmation (recommended)
[2] Automatic
```

### Manual Mode

Recommended when using a playlist for the first time.

High-confidence matches are selected automatically.

Uncertain matches are shown to you:

```text
[1] Candidate A
    Score: 89
    Artist: Example Artist
    Album: Example Album
    YouTube Music link

[2] Candidate B
    Score: 84
    Artist: Example Artist
    Album: Another Album
    YouTube Music link

[3] Candidate C
    Score: 76

[S] Skip
```

You can choose the correct version or skip the track.

### Automatic Mode

High-confidence matches are added automatically.

The matcher considers multiple signals instead of relying only on the song title.

---

## Track Matching

The synchronization system considers:

- Song title
- Artist
- Album
- Track duration
- Song version
- YouTube Music result type
- Popularity as a small tie-breaker

It also recognizes versions such as:

```text
Live
Acoustic
Remix
Nightcore
Slowed
Sped Up
8D
Cover
Karaoke
Instrumental
Demo
Extended
Radio Edit
```

YouTube labels such as:

```text
Official Audio
Official Video
Lyrics
Visualizer
```

are treated separately from the actual song title.

The goal is not to add the maximum number of songs.

The goal is to add the **correct** songs.

---

## Sync Safety

Before making changes, the tool shows a preview and asks for confirmation:

```text
This will MODIFY your YouTube Music account.
Spotify will NOT be modified.

Proceed with sync? [y/N]:
```

If you do not confirm, the synchronization is cancelled.

The current synchronization:

- Creates missing YouTube Music playlists
- Adds matched tracks
- Does not delete YouTube Music tracks
- Does not reorder YouTube Music tracks
- Does not modify Spotify playlists

---

# Installation

## Requirements

- Python 3.x
- Spotify Developer application
- Spotify account
- YouTube Music account for synchronization

## Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/SpotifyPlaylistMerger.git
cd SpotifyPlaylistMerger
```

## Create a Virtual Environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Spotify API Setup

Create an application in the Spotify Developer Dashboard and obtain:

- Client ID
- Client Secret
- Redirect URI

Create a `.env` file in the project directory:

```env
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

The Spotify authentication cache is created locally when required.

---

# YouTube Music Setup

The synchronization feature uses `ytmusicapi`.

YouTube Music authentication is configured separately using the local browser authentication file:

```text
browser.json
```

This file contains authentication information and must **never** be:

- uploaded to GitHub
- committed to the repository
- posted online
- shared with anyone

The same applies to:

```text
.env
.spotify_cache
```

and any other file containing credentials or authentication data.

---

# Project Structure

```text
SpotifyPlaylistMerger/
│
├── spotifyplaylistmerger.py    # Spotify playlist merging feature
│
├── spotify_to_ytm.py            # Spotify → YouTube Music CLI
├── spotify_client.py            # Spotify API wrapper
├── ytm_client.py                # YouTube Music API wrapper
├── track_matcher.py              # Track matching and scoring
├── sync_engine.py                # Synchronization logic
├── sync_config.json              # Local saved sync playlists
│
├── .env                          # Spotify credentials
├── browser.json                  # YouTube Music authentication
├── .spotify_cache                # Spotify auth cache
├── .gitignore
├── requirements.txt
└── README.md
```

The merger and synchronization systems share Spotify access code where appropriate, but they remain separate user-facing features.

---

# Which Command Should I Use?

## I want to merge Spotify playlists

Use:

```bash
python spotifyplaylistmerger.py
```

Example goal:

```text
Playlist A
Playlist B
Playlist C
      ↓
One combined Spotify playlist
```

---

## I want to transfer/sync Spotify playlists to YouTube Music

Use:

```bash
python spotify_to_ytm.py
```

Example goal:

```text
Spotify Playlist
      ↓
YouTube Music Playlist
```

---

## I want to do both

You can use both independently.

For example:

```bash
python spotifyplaylistmerger.py
```

to create a combined Spotify playlist.

Then:

```bash
python spotify_to_ytm.py
```

to synchronize selected Spotify playlists to YouTube Music.

You do **not** have to merge playlists before using the sync feature.

---

# Current Limitations

The YouTube Music synchronization currently uses an additive model.

It can:

```text
Spotify:
A B C

YouTube Music:
A B

        ↓ Sync

YouTube Music:
A B C
```

But if YouTube Music contains an extra track:

```text
Spotify:
A B C

YouTube Music:
A B C D
```

the current version keeps `D`.

Playlist ordering is also not synchronized yet.

---

## Future

- Additional music platforms
- Cross-platform playlist migration
- Reverse synchronization
- More advanced CLI commands

---

# Design Philosophy

The project deliberately keeps the two features independent.

```text
                 SpotifyPlaylistMerger
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
       Playlist Merger       Spotify → YT Music
              │                     │
              ▼                     ▼
      Combined Spotify       YouTube Music
         Playlist              Playlist
```

The merger solves:

> **"How do I combine my Spotify playlists?"**

The synchronization tool solves:

> **"How do I keep selected Spotify playlists available on YouTube Music?"**

They are different problems, so they have different commands and workflows.

---

# License

This project is for personal and educational use.
