import re


# ============================================================
# VERSION DEFINITIONS
# ============================================================

# These indicate that the candidate may be a different
# recording / edit / transformation of the song.
VERSION_PATTERNS = {
    # Live
    "live",
    "live at",
    "live from",
    "live session",
    "live version",
    "concert",
    "unplugged",
    "rehearsal",

    # Acoustic
    "acoustic",
    "acoustic version",
    "stripped",
    "stripped version",

    # Remixes / mixes
    "remix",
    "remixed",
    "mix",
    "club mix",
    "extended mix",
    "radio mix",
    "radio edit",
    "dance mix",
    "dub mix",
    "vip",
    "vip mix",
    "bootleg",

    # Tempo / sound transformations
    "sped up",
    "sped up version",
    "slowed",
    "slowed down",
    "slowed + reverb",
    "slowed and reverb",
    "nightcore",
    "bass boosted",
    "lofi",
    "lo fi",
    "8d",
    "8d audio",

    # Alternate versions
    "cover",
    "karaoke",
    "instrumental",
    "demo",
    "edit",
    "extended",
    "re recorded",
    "re-recorded",
    "remastered",
    "remaster",
    "alternate version",
    "alt version",
    "orchestral",
    "piano version",
}


# ============================================================
# YOUTUBE UPLOAD LABELS
# ============================================================

# These usually describe the YouTube upload rather than
# representing a different version of the actual song.

YOUTUBE_LABELS = {
    # Official
    "official audio",
    "official video",
    "official music video",
    "official lyric video",
    "official visualizer",
    "official performance",

    # Video / lyrics
    "music video",
    "video clip",
    "lyric video",
    "lyrics video",
    "lyrics",
    "lyric",
    "with lyrics",

    # Media labels
    "audio",
    "visualizer",
    "track",
    "song",
    "full track",

    # Quality
    "hq",
    "hd",
    "4k",
    "1080p",
    "stereo",
    "high quality",

    # Promotional labels
    "premiere",
    "exclusive",
    "teaser",
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(text):
    """
    Normalize text so two titles can be compared.

    Example:

        "Numb - Official Audio!"

    becomes:

        "numb official audio"
    """

    if not text:
        return ""

    text = str(text).lower().strip()

    # Treat "&" and "and" as equivalent.
    text = text.replace("&", "and")

    # Normalize apostrophes.
    text = text.replace("’", "'")

    # Remove punctuation.
    text = re.sub(r"[^\w\s]", " ", text)

    # Collapse repeated whitespace.
    text = " ".join(text.split())

    return text


# ============================================================
# TITLE CLEANING
# ============================================================

def clean_title(title):
    """
    Remove YouTube upload labels while keeping actual
    song-version information.

    Examples:

        Numb - Official Audio
            -> numb

        Numb (Nightcore) - Official Audio
            -> numb nightcore

        Numb [Live] - Official Video
            -> numb live
    """

    title = normalize(title)

    if not title:
        return ""

    words = title.split()

    changed = True

    while changed:
        changed = False

        for label in sorted(
            YOUTUBE_LABELS,
            key=len,
            reverse=True,
        ):
            label_words = label.split()

            if len(words) < len(label_words):
                continue

            if words[-len(label_words):] == label_words:
                words = words[:-len(label_words)]
                changed = True
                break

    return " ".join(words).strip()


# ============================================================
# VERSION DETECTION
# ============================================================

def _contains_phrase(text, phrase):
    """
    Check whether a phrase exists as complete words.

    This is much safer than:

        phrase in text

    because substring matching can create false positives.
    """

    pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"

    return re.search(pattern, text) is not None


def extract_versions(title):
    """
    Extract version information from a title.

    Returns a set of detected version labels.

    Examples:

        Numb (Nightcore)
            -> {"nightcore"}

        Numb - Slowed + Reverb
            -> {"slowed + reverb"}

        Numb (Live at Wembley)
            -> {"live at"}

        Numb
            -> set()
    """

    normalized = normalize(title)

    if not normalized:
        return set()

    found = set()

    # Longest phrases first.
    patterns = sorted(
        VERSION_PATTERNS,
        key=len,
        reverse=True,
    )

    for version in patterns:
        if _contains_phrase(normalized, version):
            found.add(version)

    # --------------------------------------------------------
    # Special handling for "live at X"
    # --------------------------------------------------------

    if re.search(r"\blive\s+at\b", normalized):
        found.add("live at")

    # --------------------------------------------------------
    # Special handling for "live from X"
    # --------------------------------------------------------

    if re.search(r"\blive\s+from\b", normalized):
        found.add("live from")

    return found


# Backwards-compatible name.
def extract_version_words(title):
    return extract_versions(title)


# ============================================================
# VERSION CATEGORY
# ============================================================

def version_category(versions):
    """
    Convert individual version labels into broader categories.

    This helps us understand that:

        nightcore
        slowed
        sped up

    are all transformations.

    While:

        live
        cover
        acoustic

    represent different recording types.
    """

    categories = set()

    for version in versions:

        # Live
        if (
            version == "live"
            or version.startswith("live ")
            or version == "concert"
            or version == "unplugged"
            or version == "rehearsal"
        ):
            categories.add("live")

        # Acoustic
        elif (
            "acoustic" in version
            or "stripped" in version
        ):
            categories.add("acoustic")

        # Remix / mix
        elif (
            "remix" in version
            or "mix" in version
            or version in {"bootleg", "vip", "vip mix"}
        ):
            categories.add("remix")

        # Tempo transformations
        elif version in {
            "nightcore",
            "sped up",
            "sped up version",
            "slowed",
            "slowed down",
            "slowed + reverb",
            "slowed and reverb",
            "8d",
            "8d audio",
            "bass boosted",
        }:
            categories.add("tempo")

        # Cover
        elif version == "cover":
            categories.add("cover")

        # Karaoke
        elif version == "karaoke":
            categories.add("karaoke")

        # Instrumental
        elif version == "instrumental":
            categories.add("instrumental")

        # Demo
        elif version == "demo":
            categories.add("demo")

        # Edit / alternate
        elif version in {
            "edit",
            "extended",
            "extended mix",
            "radio edit",
            "alternate version",
            "alt version",
        }:
            categories.add("edit")

        # Remaster
        elif version in {
            "remaster",
            "remastered",
            "re recorded",
            "re-recorded",
        }:
            categories.add("remaster")

        # Other
        else:
            categories.add(version)

    return categories


# ============================================================
# TITLE SCORE
# ============================================================

def title_score(spotify_title, ytm_title):
    """
    Compare the actual song titles.

    Version labels are NOT used as the primary title signal.
    They are handled separately by version_score().
    """

    spotify = clean_title(spotify_title)
    ytm = clean_title(ytm_title)

    if not spotify or not ytm:
        return 0

    # Remove version information for the base-title comparison.
    spotify_versions = extract_versions(spotify)
    ytm_versions = extract_versions(ytm)

    spotify_base = spotify
    ytm_base = ytm

    for version in sorted(
        spotify_versions,
        key=len,
        reverse=True,
    ):
        spotify_base = re.sub(
            r"(?<!\w)" + re.escape(version) + r"(?!\w)",
            " ",
            spotify_base,
        )

    for version in sorted(
        ytm_versions,
        key=len,
        reverse=True,
    ):
        ytm_base = re.sub(
            r"(?<!\w)" + re.escape(version) + r"(?!\w)",
            " ",
            ytm_base,
        )

    spotify_base = " ".join(spotify_base.split())
    ytm_base = " ".join(ytm_base.split())

    # --------------------------------------------------------
    # Exact title
    # --------------------------------------------------------

    if spotify_base == ytm_base:
        return 40

    # --------------------------------------------------------
    # One title contains the other
    # --------------------------------------------------------

    if (
        spotify_base in ytm_base
        or ytm_base in spotify_base
    ):
        return 30

    # --------------------------------------------------------
    # Word overlap
    # --------------------------------------------------------

    spotify_words = set(spotify_base.split())
    ytm_words = set(ytm_base.split())

    if not spotify_words or not ytm_words:
        return 0

    overlap = len(
        spotify_words & ytm_words
    ) / max(
        len(spotify_words),
        len(ytm_words),
    )

    if overlap >= 0.8:
        return 25

    if overlap >= 0.5:
        return 15

    return 0


# ============================================================
# ARTIST SCORE
# ============================================================

def artist_score(spotify_artists, ytm_artists):
    """
    Compare Spotify and YouTube Music artists.
    """

    spotify = [
        normalize(a)
        for a in spotify_artists
        if a
    ]

    ytm = [
        normalize(a)
        for a in ytm_artists
        if a
    ]

    if not spotify or not ytm:
        return 0

    score = 0

    main_artist = spotify[0]

    # Exact primary artist.
    if main_artist == ytm[0]:
        score += 35

    # Primary artist exists somewhere in YT artists.
    elif main_artist in ytm:
        score += 30

    # Partial artist match.
    elif any(
        main_artist in artist
        or artist in main_artist
        for artist in ytm
    ):
        score += 25

    else:
        return 0

    # Additional Spotify artists.
    for artist in spotify[1:]:
        if artist in ytm:
            score += 5

    return min(score, 40)


# ============================================================
# ALBUM SCORE
# ============================================================

def album_score(spotify_album, ytm_album):
    """
    Album matching is a supporting signal.

    Missing album information does NOT cause rejection.
    """

    if not spotify_album or not ytm_album:
        return 0

    spotify = normalize(spotify_album)
    ytm = normalize(ytm_album)

    if spotify == ytm:
        return 10

    return 0


# ============================================================
# DURATION SCORE
# ============================================================

def duration_score(
    spotify_duration,
    ytm_duration,
):
    """
    Compare track lengths.

    Small differences are normal because of metadata differences.
    Large differences are suspicious.
    """

    if (
        spotify_duration is None
        or ytm_duration is None
    ):
        return 0

    try:
        difference = abs(
            float(spotify_duration)
            - float(ytm_duration)
        )
    except (TypeError, ValueError):
        return 0

    # Almost identical recording.
    if difference <= 2:
        return 12

    # Very close.
    if difference <= 5:
        return 9

    # Probably close enough.
    if difference <= 10:
        return 5

    # Very different recording.
    if difference >= 30:
        return -10

    return 0


# ============================================================
# VERSION SCORE
# ============================================================

def version_score(
    spotify_title,
    ytm_title,
):
    """
    Compare song versions.

    Examples:

        Spotify: Numb (Nightcore)
        YT:      Numb (Nightcore)
            -> strong match

        Spotify: Numb (Nightcore)
        YT:      Numb
            -> penalty

        Spotify: Numb
        YT:      Numb (Live)
            -> penalty

        Spotify: Numb (Live)
        YT:      Numb (Nightcore)
            -> heavy penalty
    """

    spotify_versions = extract_versions(
        spotify_title
    )

    ytm_versions = extract_versions(
        ytm_title
    )

    # Both have no version.
    if not spotify_versions and not ytm_versions:
        return 0

    # Exact same version labels.
    if spotify_versions == ytm_versions:
        return 20

    spotify_categories = version_category(
        spotify_versions
    )

    ytm_categories = version_category(
        ytm_versions
    )

    # --------------------------------------------------------
    # Spotify has a version, YT doesn't.
    # --------------------------------------------------------

    if spotify_versions and not ytm_versions:
        return -25

    # --------------------------------------------------------
    # YT has a version, Spotify doesn't.
    # --------------------------------------------------------

    if ytm_versions and not spotify_versions:
        return -25

    # --------------------------------------------------------
    # Same broad category but different exact version.
    #
    # Example:
    # Spotify: Slowed
    # YT:      Slowed + Reverb
    # --------------------------------------------------------

    if spotify_categories == ytm_categories:
        return -5

    # Completely different versions.
    return -30


# ============================================================
# POPULARITY SCORE
# ============================================================

def popularity_score(candidate):
    """
    Popularity is ONLY a tiny tie-breaker.

    It can never overpower title, artist,
    duration, or version matching.
    """

    views = candidate.get("views")

    if not views:
        return 0

    try:
        views = int(
            str(views).replace(",", "")
        )
    except (ValueError, TypeError):
        return 0

    if views >= 100_000_000:
        return 3

    if views >= 10_000_000:
        return 2

    if views >= 1_000_000:
        return 1

    return 0


# ============================================================
# COMPLETE SCORE
# ============================================================

def calculate_score(
    spotify_track,
    candidate,
):
    """
    Calculate the total confidence score.
    """

    score = 0

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    score += title_score(
        spotify_track.get("name", ""),
        candidate.get("title", ""),
    )

    # --------------------------------------------------------
    # ARTISTS
    # --------------------------------------------------------

    candidate_artists = [
        artist.get("name", "")
        for artist in candidate.get(
            "artists",
            [],
        )
        if artist.get("name")
    ]

    score += artist_score(
        spotify_track.get("artists", []),
        candidate_artists,
    )

    # --------------------------------------------------------
    # ALBUM
    # --------------------------------------------------------

    score += album_score(
        spotify_track.get("album"),
        candidate.get("album"),
    )

    # --------------------------------------------------------
    # DURATION
    # --------------------------------------------------------

    score += duration_score(
        spotify_track.get(
            "duration_seconds"
        ),
        candidate.get(
            "duration_seconds"
        ),
    )

    # --------------------------------------------------------
    # VERSION
    # --------------------------------------------------------

    score += version_score(
        spotify_track.get("name", ""),
        candidate.get("title", ""),
    )

    # --------------------------------------------------------
    # RESULT TYPE
    # --------------------------------------------------------

    if candidate.get("resultType") == "song":
        score += 5

    # --------------------------------------------------------
    # POPULARITY
    # --------------------------------------------------------

    score += popularity_score(candidate)

    return score


# ============================================================
# MATCH CANDIDATES
# ============================================================

def rank_candidates(
    spotify_track,
    search_results,
):
    """
    Score and rank all valid YouTube Music song results.

    This is separate from find_best_match() so the sync engine
    can later display multiple candidates to the user when
    confidence is low.
    """

    candidates = []

    for result in search_results:

        # Only actual songs.
        if result.get("resultType") != "song":
            continue

        # Must have a playable YouTube Music video ID.
        if not result.get("videoId"):
            continue

        score = calculate_score(
            spotify_track,
            result,
        )

        candidates.append(
            {
                "score": score,
                "video_id": result.get(
                    "videoId"
                ),
                "name": result.get(
                    "title",
                    "",
                ),
                "artists": [
                    artist.get("name", "")
                    for artist in result.get(
                        "artists",
                        [],
                    )
                ],
                "album": result.get(
                    "album"
                ),
                "duration_seconds": result.get(
                    "duration_seconds"
                ),
                "versions": list(
                    extract_versions(
                        result.get(
                            "title",
                            "",
                        )
                    )
                ),
                "raw": result,
            }
        )

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return candidates


# ============================================================
# BEST MATCH
# ============================================================

def find_best_match(
    spotify_track,
    search_results,
):
    """
    Find the safest automatic match.

    Returns None if:
        - confidence is too low
        - two candidates are too close
    """

    candidates = rank_candidates(
        spotify_track,
        search_results,
    )

    if not candidates:
        return None

    best = candidates[0]

    best_score = best["score"]

    second_score = (
        candidates[1]["score"]
        if len(candidates) > 1
        else 0
    )

    # --------------------------------------------------------
    # Minimum confidence
    # --------------------------------------------------------

    if best_score < 70:
        return None

    # --------------------------------------------------------
    # Ambiguous match
    # --------------------------------------------------------

    if (
        len(candidates) > 1
        and best_score - second_score < 8
    ):
        return None

    return {
        "score": best_score,
        "second_score": second_score,
        "video_id": best["video_id"],
        "name": best["name"],
        "artists": best["artists"],
        "album": best["album"],
        "duration_seconds": best[
            "duration_seconds"
        ],
        "versions": best["versions"],
    }