from api import get
from config import config
from utils import require_login
from downloader import download_track
from converter import convert_audio
from tagger import tag_audio
from cover import download_cover_image
import os

def find_album_by_title(title: str):
    if not require_login(config):
        return []

    results = get("/search", params={"q": title, "type": "album"})
    if not results:
        print("API returned no result.")
        return []

    return results.get("albums", [])

def download_album(album_id: str):
    if not require_login(config):
        return

    album_data = get(f"/albums/{album_id}")
    if not album_data or "album" not in album_data:
        print("Could not fetch album details.")
        return

    album = album_data["album"]
    tracks = album.get("tracks", [])

    if not tracks:
        print("Album has no tracks or failed to load.")
        return

    title = album.get("title", f"album_{album_id}")
    output_format = config.output_format
    quality = "27" if output_format == "flac" else "5"

    album_folder = os.path.join(config.output_directory, f"{title} [{output_format.upper()}]")
    os.makedirs(album_folder, exist_ok=True)

    print(f"Downloading Album: {title} ({len(tracks)} tracks)")

    for idx, track in enumerate(tracks, 1):
        print(f"[{idx}/{len(tracks)}] {track['title']} — {track['artist']}")

        raw_path = download_track(
            track_id=track["id"],
            quality=quality,
            directory=album_folder,
            index=idx,
            track_meta=track
        )
        if not raw_path:
            print("Skipping: download failed.")
            continue

        converted_path = convert_audio(raw_path, output_format)
        if not converted_path:
            print("Skipping: conversion failed.")
            continue

        metadata = {
            "title": track.get("title", ""),
            "artist": track.get("artist", ""),
            "album": album.get("title", ""),
            "genre": album.get("genre", ""),
            "date": album.get("releaseDate", "")[:4]
        }

        cover_url = album.get("cover")
        cover_path = None
        if cover_url:
            cover_path = download_cover_image(
                cover_url, os.path.join(album_folder, f"cover_{track['id']}.jpg")
            )

        tag_audio(converted_path, metadata, cover_path=cover_path)

        if cover_path and os.path.exists(cover_path) and not config.keep_cover_file:
            try:
                os.remove(cover_path)
            except Exception:
                pass

        if config.delete_raw_files and raw_path != converted_path:
            try:
                os.remove(raw_path)
            except Exception:
                pass