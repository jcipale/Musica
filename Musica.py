#!/usr/bin/env python3
"""
Musica v3.26
Discogs Collection Exporter — Clean and Normalized Edition

Exports user's entire Discogs collection as a CSV:
Artist;Title;Year;Genre;Format;Label;Label_Number;Recording_Mode;DBX_Encoded

Author: Musica Project
"""

import os
import sys
import json
import requests
from time import sleep

# -------------------------------------------------------------
# Progress bar
# -------------------------------------------------------------
def progress_bar(current, total, width=40):
    if total <= 0:
        return
    ratio = current / total
    filled = int(width * ratio)
    bar = "=" * filled + "-" * (width - filled)
    sys.stdout.write(f"\r[{bar}] {ratio * 100:5.1f}%")
    sys.stdout.flush()
    if current == total:
        print()


# -------------------------------------------------------------
# Artist normalization
# -------------------------------------------------------------
def normalize_artist(name):
    if not name:
        return "Unknown"
    name = name.strip()
    if "(" in name and ")" in name:
        name = name.split("(")[0].strip()
    parts = name.split()
    if len(parts) == 1:
        return name
    if name.lower().startswith("the "):
        return f"{name[4:]}, The"
    if "," in name:
        return name
    return f"{parts[-1]}, {' '.join(parts[:-1])}"


# -------------------------------------------------------------
# Title normalization
# -------------------------------------------------------------
def normalize_title(title):
    if not title:
        return "Unknown"
    title = title.strip()
    if title.lower().startswith("the "):
        return f"{title[4:]}, The"
    return title


# -------------------------------------------------------------
# Format normalization
# -------------------------------------------------------------
def normalize_format(fmt_list):
    if not fmt_list:
        return "Unknown"
    fmt_text = " ".join(fmt_list).lower()
    if "vinyl" in fmt_text:
        return "LP"
    if "cd" in fmt_text:
        return "CD"
    if "cassette" in fmt_text:
        return "Cass"
    if "reel" in fmt_text:
        return "RtR"
    if "8-track" in fmt_text or "8 track" in fmt_text:
        return "8T"
    return fmt_text.title()


# -------------------------------------------------------------
# Recording mode (Mono/Stereo)
# -------------------------------------------------------------
def detect_recording_mode(fmt_list):
    if not fmt_list:
        return "U"
    text = " ".join(fmt_list).lower()
    if "mono" in text:
        return "M"
    if "stereo" in text:
        return "S"
    return "U"


# -------------------------------------------------------------
# DBX encoded detection
# -------------------------------------------------------------
def detect_dbx(fmt_list, notes):
    combined = " ".join(fmt_list + [notes]).lower()
    if "dbx" in combined:
        return "Yes"
    return "No"


# -------------------------------------------------------------
# Load user JSON config
# -------------------------------------------------------------
def load_config():
    files = [f for f in os.listdir(".") if f.lower().endswith(".json") and "jcipale" in f.lower()]
    if not files:
        print("No user config JSON found.")
        sys.exit(1)

    if len(files) == 1:
        filename = files[0]
    else:
        print("Available user config files:")
        for i, f in enumerate(files, 1):
            print(f"  {i}. {f}")
        choice = input("Select config file [1]: ").strip()
        idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(files) else 0
        filename = files[idx]

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Using config file: {filename}")
    return data


# -------------------------------------------------------------
# Fetch collection from Discogs
# -------------------------------------------------------------
def fetch_discogs_collection(username, token):
    base_url = f"https://api.discogs.com/users/{username}/collection/folders/0/releases"
    headers = {"User-Agent": "Musica_v3.26/1.0"}
    params = {"token": token, "per_page": 100, "page": 1}
    releases = []
    total_items = None

    print("\nFetching all releases from Discogs...")
    while True:
        r = requests.get(base_url, headers=headers, params=params)
        if r.status_code != 200:
            print(f"\nError fetching data: HTTP {r.status_code}")
            break
        data = r.json()
        if total_items is None:
            total_items = data.get("pagination", {}).get("items", 0)
        releases.extend(data.get("releases", []))
        progress_bar(len(releases), total_items)
        if not data.get("pagination", {}).get("urls", {}).get("next"):
            break
        params["page"] += 1
        sleep(0.2)
    print(f"\nDownload complete: {len(releases)} items.\n")
    return releases


# -------------------------------------------------------------
# Main export logic
# -------------------------------------------------------------
def main():
    cfg = load_config()
    username = cfg.get("username")
    token = cfg.get("token")

    releases = fetch_discogs_collection(username, token)
    csv_filename = f"Musica_Export_v3.26.csv"

    with open(csv_filename, "w", encoding="utf-8") as f:
        f.write("Artist;Title;Year;Genre;Format;Label;Label_Number;Recording_Mode;DBX_Encoded\n")

        for i, rel in enumerate(releases, start=1):
            info = rel.get("basic_information", {})
            artists = info.get("artists", [])
            artist_name = normalize_artist(artists[0]["name"]) if artists else "Unknown"

            title = normalize_title(info.get("title"))
            year = str(info.get("year") or "Unknown")
            genre = ", ".join(info.get("genres", [])) or "Unknown"
            formats = [f.get("name", "") for f in info.get("formats", [])]
            fmt = normalize_format(formats)

            labels = info.get("labels", [])
            label = labels[0].get("name", "Unknown") if labels else "Unknown"
            label_num = labels[0].get("catno", "") if labels else ""

            recording_mode = detect_recording_mode(formats)
            notes = info.get("notes", "")
            dbx_flag = detect_dbx(formats, notes)

            f.write(f"{artist_name};{title};{year};{genre};{fmt};{label};{label_num};{recording_mode};{dbx_flag}\n")

            if i % 20 == 0 or i == len(releases):
                progress_bar(i, len(releases))

    print(f"\nExport complete: {csv_filename}\n")


# -------------------------------------------------------------
# Run safely
# -------------------------------------------------------------
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")

