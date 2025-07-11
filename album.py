import os
from downloader import download_track
from converter import convert_audio
from tagger import tag_audio
from config import config
from api import get
from search import search_and_return
from cover import download_cover_image

from tabulate import tabulate

def sanitize_filename(name):
    return ''.join(c for c in name if c.isalnum() or c in ' _-').rstrip()

def find_album_by_title(title: str):
    return search_and_return(title, filter_type="album")

def download_album(album_id: str, quality: str = None):
    result = get("/album", params={"albumId": album_id})
    if not result or "album" not in result:
        print("[Album] Failed to load album.")
        return

    album = result["album"]
    tracks = album.get("tracks", [])
    if not tracks:
        print("[Album] No tracks found in the album.")
        return

    artist = sanitize_filename(album.get("artist", "Unknown Artist"))
    title = sanitize_filename(album.get("title", f"album_{album_id}"))
    output_format = config.output_format
    quality = quality or ("27" if output_format == "flac" else "5")

    album_folder = os.path.join(config.output_directory, f"{artist} - {title} [{output_format.upper()}]")
    os.makedirs(album_folder, exist_ok=True)

    print(f"[Album] Downloading: {title} by {artist} ({len(tracks)} tracks)")

    # Download cover once
    cover_url = album.get("cover") or (tracks[0].get("albumCover") if tracks else None)
    cover_path = None
    if cover_url:
        cover_path = download_cover_image(cover_url, os.path.join(album_folder, "cover.jpg"))

    playlist_paths = []
    for idx, track in enumerate(tracks, 1):
        print(f"[{idx}/{len(tracks)}] {track['title']} — {track['artist']}")

        raw_path = download_track(
            track_id=track["id"],
            quality=quality,
            directory=album_folder,
            index=idx,  # Album keeps numbering
            track_meta=track
        )
        if not raw_path:
            print("[Album] Skipping: download failed.")
            continue

        converted_path = convert_audio(raw_path, output_format)
        if not converted_path:
            print("[Album] Skipping: conversion failed.")
            continue

        metadata = {
            "title": track.get("title", ""),
            "artist": track.get("artist", ""),
            "album": track.get("albumTitle", ""),
            "genre": track.get("genre", ""),
            "date": track.get("releaseDate", "")[:4]
        }
        tag_audio(converted_path, metadata, cover_path=cover_path)

        if config.delete_raw_files and raw_path != converted_path:
            try:
                os.remove(raw_path)
            except Exception as e:
                print(f"[Album] Could not delete raw file: {e}")

        playlist_paths.append(os.path.basename(converted_path))

    # Optionally remove the shared cover
    if cover_path and os.path.exists(cover_path) and not config.keep_cover_file:
        try:
            os.remove(cover_path)
        except Exception:
            pass

    # Write album.m3u8
    m3u_path = os.path.join(album_folder, "album.m3u8")
    with open(m3u_path, "w", encoding="utf-8") as m3u:
        for filename in playlist_paths:
            m3u.write(filename + "\n")

    print(f"[Album] Finished: {len(playlist_paths)} tracks saved to {album_folder}")
    print(f"[Album] Playlist written to: {m3u_path}")