"""Generate ~1000 synthetic program records for the demo."""
import json
import random
import string
from datetime import datetime, timedelta

random.seed(42)  # Reproducible

RECORD_TYPES = ["Movie", "Show", "Season", "Episode"]
COUNTRIES = ["US", "UK", "CA", "AU", "DE", "FR", "JP", "KR", "IN", "BR"]
LANGUAGES = ["en", "es", "fr", "de", "ja", "ko", "zh", "hi", "pt", "it"]
NETWORKS = ["NBC", "CBS", "ABC", "FOX", "HBO", "Netflix", "Amazon", "Disney+", "Hulu", "BBC", "ITV"]
GENRES = ["Drama", "Comedy", "Action", "Thriller", "Horror", "Romance", "Sci-Fi", "Documentary", "Animation", "Fantasy"]
SUBGENRES = ["Crime", "Legal", "Medical", "Family", "Adventure", "Mystery", "Supernatural", "Historical", "Biographical", "Musical"]

MOVIE_SUBTYPES = ["Feature Film", "Short Film", "TV Movie", "Direct-to-Video", "Documentary"]
SHOW_SUBTYPES = ["Series", "Miniseries", "Special", "News", "Talk Show", "Reality", "Documentary"]

# Some real-ish sounding titles
TITLE_WORDS = [
    "The", "Dark", "Light", "Last", "First", "Hidden", "Silent", "Broken", "Rising",
    "Falling", "Golden", "Silver", "Iron", "Shadow", "Crystal", "Midnight", "Summer",
    "Winter", "Storm", "Fire", "Ice", "Thunder", "Ocean", "Mountain", "River",
    "City", "Crown", "Throne", "Kingdom", "Empire", "Legacy", "Secret", "Promise",
    "Dream", "Night", "Day", "Dawn", "Dusk", "Echo", "Phantom", "Guardian",
]


def random_title(max_words=4):
    num_words = random.randint(1, max_words)
    return " ".join(random.choices(TITLE_WORDS, k=num_words))


def random_date(start_year=2000, end_year=2026):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + timedelta(days=random_days)).strftime("%Y-%m-%d")


def generate_clean_movie(idx):
    return {
        "tmsId": f"MV-DEMO-{idx:04d}",
        "recordType": "Movie",
        "title": random_title(),
        "runtimeMinutes": random.randint(80, 180),
        "subtype": random.choice(MOVIE_SUBTYPES),
        "genre": random.choice(GENRES),
        "subgenre": random.choice(SUBGENRES),
        "releaseYear": random.randint(2000, 2026),
        "countryOfOrigin": random.choice(COUNTRIES),
        "originalAudioLanguage": random.choice(LANGUAGES),
        "market": random.choice(COUNTRIES),
    }


def generate_clean_show(idx):
    return {
        "tmsId": f"SH-DEMO-{idx:04d}",
        "recordType": "Show",
        "title": random_title(),
        "subtype": random.choice(SHOW_SUBTYPES),
        "genre": random.choice(GENRES),
        "subgenre": random.choice(SUBGENRES),
        "releaseYear": random.randint(2000, 2026),
        "countryOfOrigin": random.choice(COUNTRIES),
        "originalAudioLanguage": random.choice(LANGUAGES),
        "originalNetwork": random.choice(NETWORKS),
        "originalAirDate": random_date(),
        "market": random.choice(COUNTRIES),
    }


def generate_clean_season(idx, parent_show_idx):
    return {
        "tmsId": f"SN-DEMO-{idx:04d}",
        "recordType": "Season",
        "title": f"{random_title()} Season {random.randint(1, 10)}",
        "seasonNumber": random.randint(1, 10),
        "parentSeriesId": f"SH-DEMO-{parent_show_idx:04d}",
        "market": random.choice(COUNTRIES),
    }


def generate_clean_episode(idx, parent_season_idx, parent_show_idx):
    return {
        "tmsId": f"EP-DEMO-{idx:04d}",
        "recordType": "Episode",
        "title": random_title(3),
        "runtimeMinutes": random.randint(22, 65),
        "genre": random.choice(GENRES),
        "seasonNumber": random.randint(1, 10),
        "episodeNumber": random.randint(1, 24),
        "parentSeasonId": f"SN-DEMO-{parent_season_idx:04d}",
        "parentSeriesId": f"SH-DEMO-{parent_show_idx:04d}",
        "originalAirDate": random_date(),
        "originalAudioLanguage": random.choice(LANGUAGES),
        "market": random.choice(COUNTRIES),
    }


def inject_title_errors(record):
    """Inject title-related errors."""
    error_type = random.choice(["blank", "too_long", "forbidden_char", "forbidden_term"])
    if error_type == "blank":
        record["title"] = ""
    elif error_type == "too_long":
        record["title"] = "A" * 160  # Exceeds 150 limit
    elif error_type == "forbidden_char":
        record["title"] = record.get("title", "Test") + "\u2122"
    elif error_type == "forbidden_term":
        record["title"] = "TBD"
    return record


def inject_duration_errors(record):
    """Inject duration-related errors."""
    error_type = random.choice(["zero", "negative", "unparseable", "implausible"])
    if error_type == "zero":
        record["runtimeMinutes"] = 0
    elif error_type == "negative":
        record["runtimeMinutes"] = -random.randint(1, 200)
    elif error_type == "unparseable":
        record["runtimeMinutes"] = random.choice(["1h52", "ninety", "N/A", "TBD", "1:30:00"])
    elif error_type == "implausible":
        record["runtimeMinutes"] = random.randint(700, 2000)
    return record


def inject_subtype_errors(record):
    """Inject subtype-related errors."""
    error_type = random.choice(["missing", "invalid"])
    if error_type == "missing":
        record["subtype"] = ""
    elif error_type == "invalid":
        record["subtype"] = random.choice(["Unknown", "Other", "Misc", "General", "Type1"])
    return record


def inject_oad_errors(record):
    """Inject OAD-related errors."""
    error_type = random.choice(["invalid_format", "future_date"])
    if error_type == "invalid_format":
        record["originalAirDate"] = random.choice(["not-a-date", "2026/13/45", "yesterday", "TBD", "32-01-2025"])
    elif error_type == "future_date":
        future = datetime.now() + timedelta(days=random.randint(400, 1000))
        record["originalAirDate"] = future.strftime("%Y-%m-%d")
    return record


def inject_language_errors(record):
    """Inject audio language errors."""
    error_type = random.choice(["unknown", "invalid"])
    if error_type == "unknown":
        record["originalAudioLanguage"] = random.choice(["Unknown", "UNK", "N/A"])
    elif error_type == "invalid":
        record["originalAudioLanguage"] = random.choice(["Klingon", "Elvish", "XYZ", "123", "none"])
    return record


def inject_required_field_errors(record):
    """Remove a required field."""
    field = random.choice(["releaseYear", "countryOfOrigin", "originalNetwork"])
    if field in record:
        record[field] = ""
    else:
        record[field] = None
    return record


def generate_all():
    records = []
    idx = 0

    ERROR_INJECTORS = [
        inject_title_errors,
        inject_duration_errors,
        inject_subtype_errors,
        inject_oad_errors,
        inject_language_errors,
        inject_required_field_errors,
    ]

    # --- Movies: 350 (245 clean + 105 with errors) ---
    for i in range(245):
        idx += 1
        records.append(generate_clean_movie(idx))
    for i in range(105):
        idx += 1
        record = generate_clean_movie(idx)
        # Apply 1-2 random errors
        num_errors = random.randint(1, 2)
        for injector in random.sample(ERROR_INJECTORS, min(num_errors, len(ERROR_INJECTORS))):
            record = injector(record)
        records.append(record)

    # --- Shows: 250 (175 clean + 75 with errors) ---
    show_start = idx + 1
    for i in range(175):
        idx += 1
        records.append(generate_clean_show(idx))
    for i in range(75):
        idx += 1
        record = generate_clean_show(idx)
        num_errors = random.randint(1, 2)
        for injector in random.sample(ERROR_INJECTORS, min(num_errors, len(ERROR_INJECTORS))):
            record = injector(record)
        records.append(record)

    # --- Seasons: 150 (120 clean + 30 with errors) ---
    for i in range(120):
        idx += 1
        records.append(generate_clean_season(idx, random.randint(show_start, show_start + 249)))
    for i in range(30):
        idx += 1
        record = generate_clean_season(idx, random.randint(show_start, show_start + 249))
        record["title"] = ""  # Title error for season
        records.append(record)

    # --- Episodes: 250 (175 clean + 75 with errors) ---
    for i in range(175):
        idx += 1
        records.append(generate_clean_episode(idx, random.randint(1, 150), random.randint(show_start, show_start + 249)))
    for i in range(75):
        idx += 1
        record = generate_clean_episode(idx, random.randint(1, 150), random.randint(show_start, show_start + 249))
        num_errors = random.randint(1, 2)
        for injector in random.sample(ERROR_INJECTORS, min(num_errors, len(ERROR_INJECTORS))):
            record = injector(record)
        records.append(record)

    # Shuffle so errors are spread out
    random.shuffle(records)

    return records


if __name__ == "__main__":
    records = generate_all()
    output_path = "seed_data/records.json"
    with open(output_path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Generated {len(records)} records -> {output_path}")

    # Stats
    by_type = {}
    for r in records:
        t = r["recordType"]
        by_type[t] = by_type.get(t, 0) + 1
    for t, c in sorted(by_type.items()):
        print(f"  {t}: {c}")
