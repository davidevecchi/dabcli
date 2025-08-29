from api import get
from config import config
from utils import require_login
from downloader import download_track
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

def download_album(album_id: str, cli_args=None, directory=None):
    """
    Download an album by ID.
    cli_args: optional object containing --title, --artist, --album, --genre, --date
    """
    if not require_login(config):
        return

    album_data = get(f"/album?albumId={album_id}")
    if not album_data or "album" not in album_data:
        print("Could not fetch album details.")
        return

    album = album_data["album"]
    tracks = album.get("tracks", [])

    if not tracks:
        print("Album has no tracks or failed to load.")
        return

    title = album.get("title", f"album_{album_id}")[:64]
    artist = album.get("artist", f"album_{album_id}")[:64]
    output_format = config.output_format
    quality = "5" if output_format == "mp3" else "27"
    
    output_directory = directory or os.path.join(config.output_directory, "albums")
    album_folder = os.path.join(output_directory, f"{artist} - {title}")
    os.makedirs(album_folder, exist_ok=True)

    print(f"Downloading Album: {title} ({len(tracks)} tracks)")

    # Download album cover once
    cover_url = album.get("cover")
    album_cover_path = None
    if cover_url:
        album_cover_path = download_cover_image(cover_url, os.path.join(album_folder, "cover.jpg"))

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

        # Convert only if needed (e.g., remove ffmpeg if not used)
        converted_path = raw_path  # assuming same format as output; update if you use convert_audio
        # converted_path = convert_audio(raw_path, output_format)

        # Build metadata, applying CLI overrides if present
        metadata = {
            "title": getattr(cli_args, "title", None) or track.get("title", ""),
            "artist": getattr(cli_args, "artist", None) or track.get("artist", ""),
            "album": getattr(cli_args, "album", None) or album.get("title", ""),
            "genre": getattr(cli_args, "genre", None) or album.get("genre", ""),
            "date": getattr(cli_args, "date", None) or album.get("releaseDate", "")[:4]
        }

        # Embed cover
        tag_audio(converted_path, metadata, cover_path=album_cover_path)

        # Remove temporary raw file if configured
        if config.delete_raw_files and raw_path != converted_path:
            try:
                os.remove(raw_path)
            except Exception:
                pass

    # Optionally clean cover.jpg after embedding
    if not config.keep_cover_file:
        try:
            os.remove(os.path.join(album_folder, "cover.jpg"))
        except Exception:
            pass