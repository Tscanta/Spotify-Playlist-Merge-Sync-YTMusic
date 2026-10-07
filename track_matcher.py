import re


BAD_WORDS = {
    "live",
    "cover",
    "karaoke",
    "instrumental",
    "sped up",
    "slowed",
    "nightcore",
    "8d",
    "remix",
    "acoustic",
    "demo",
}


def normalize(text):
    text = text.lower().strip()

    text = text.replace("&", "and")

    text = re.sub(r"[^\w\s]", " ", text)

    return " ".join(text.split())


def normalize_artist(text):
    return normalize(text)


def title_score(spotify_title, ytm_title):
    spotify = normalize(spotify_title)
    ytm = normalize(ytm_title)

    if spotify == ytm:
        return 40

    # Remove common YouTube labels
    cleaned = ytm

    removable = [
        "official audio",
        "official video",
        "official music video",
        "lyrics",
        "lyric video",
        "audio",
    ]

    for suffix in removable:
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-len(suffix)].strip()

    if cleaned == spotify:
        return 38

    if spotify in cleaned:
        return 30

    return 0


def artist_score(
    spotify_artists,
    ytm_artists,
):
    spotify = [
        normalize_artist(a)
        for a in spotify_artists
    ]

    ytm = [
        normalize_artist(a)
        for a in ytm_artists
    ]

    if not spotify or not ytm:
        return 0

    score = 0

    # Primary artist
    if spotify[0] in ytm:
        score += 35

    elif any(
        spotify[0] in artist
        or artist in spotify[0]
        for artist in ytm
    ):
        score += 25

    # Additional artists
    for artist in spotify[1:]:
        if artist in ytm:
            score += 10

    return min(score, 45)


def duration_score(
    spotify_duration,
    ytm_duration,
):
    if not spotify_duration or not ytm_duration:
        return 0

    difference = abs(
        spotify_duration - ytm_duration
    )

    if difference <= 2:
        return 10

    if difference <= 5:
        return 7

    if difference <= 10:
        return 4

    return 0


def bad_word_penalty(title):
    normalized = normalize(title)

    penalty = 0

    for word in BAD_WORDS:
        if word in normalized:
            penalty += 20

    return penalty


def calculate_score(
    spotify_track,
    candidate,
):
    score = 0

    score += title_score(
        spotify_track["name"],
        candidate.get("title", ""),
    )

    score += artist_score(
        spotify_track["artists"],
        [
            artist.get("name", "")
            for artist in candidate.get(
                "artists",
                [],
            )
        ],
    )

    score += duration_score(
        spotify_track.get(
            "duration_seconds"
        ),
        candidate.get(
            "duration_seconds"
        ),
    )

    score -= bad_word_penalty(
        candidate.get("title", "")
    )

    # Small bonus for an actual YT Music song result
    if candidate.get("resultType") == "song":
        score += 5

    return score


def find_best_match(
    spotify_track,
    search_results,
):
    candidates = []

    for result in search_results:

        if result.get("resultType") != "song":
            continue

        if not result.get("videoId"):
            continue

        score = calculate_score(
            spotify_track,
            result,
        )

        candidates.append(
            (score, result)
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    best_score, best = candidates[0]

    # Don't blindly add weak matches.
    if best_score < 70:
        return None

    return {
        "score": best_score,
        "video_id": best["videoId"],
        "name": best.get("title", ""),
        "artists": [
            artist.get("name", "")
            for artist in best.get(
                "artists",
                [],
            )
        ],
        "duration_seconds": best.get(
            "duration_seconds"
        ),
    }