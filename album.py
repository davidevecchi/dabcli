import glob
import os
import shutil

from api import get
from config import config
from cover import download_cover_image
from downloader import download_track
from tagger import tag_audio
from utils import require_login, sanitize_filename


def find_album_by_title(title: str):
    if not require_login(config):
        return []
    
    results = get("/search", params={"q": title, "type": "album"})
    if not results:
        print("API returned no result.")
        return []
    
    return results.get("albums", [])


def download_album(album_id: str, cli_args=None, directory=None, discography_artist=None):
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
    year = album.get("releaseDate", "")[:4]
    
    output_format = cli_args.format or config.output_format
    quality = "5" if output_format == "mp3" else "27"
    
    output_directory = directory or os.path.join(config.output_directory, "albums")
    album_folder = os.path.join(output_directory, sanitize_filename(f"{year} - {artist} - {title} - {album_id}"))
    
    excluded_matches = glob.glob(os.path.join(output_directory, '.excluded', f'*{album_id}'))
    if len(excluded_matches) > 0:
        print(f"Album {album_id} is excluded.")
        for match in excluded_matches:
            for track in glob.glob(os.path.join(match, "*")):
                os.remove(track)
        return
    
    os.makedirs(album_folder, exist_ok=True)
    
    print(f"Downloading Album: {title} ({len(tracks)} tracks)")
    
    # Download album cover once
    cover_url = album.get("cover")
    album_cover_path = None
    if cover_url:
        album_cover_path = download_cover_image(cover_url, os.path.join(album_folder, "cover.jpg"))
    
    count = 0
    for idx, track in enumerate(tracks, 1):
        if discography_artist is None or (
            discography_artist in title or
            discography_artist in artist or
            discography_artist in track['title'] or
            discography_artist in track['artist']
        ):
            print(f"[{idx}/{len(tracks)}] {track['title']} — {track['artist']}")
            count += 1
            
            raw_path = download_track(
                track_id=track["id"],
                quality=quality,
                directory=album_folder,
                index=idx,
                track_meta=track,
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
                "date": getattr(cli_args, "date", None) or album.get("releaseDate", "")[:4],
            }
            
            # Embed cover
            tag_audio(converted_path, metadata, cover_path=album_cover_path)
            
            # Remove temporary raw file if configured
            if config.delete_raw_files and raw_path != converted_path:
                try:
                    os.remove(raw_path)
                except Exception:
                    pass
    
    try:
        if count == 0:
            shutil.rmtree(album_folder)
            print(f"Deleting empty {album_folder}")
        elif not config.keep_cover_file:
            os.remove(os.path.join(album_folder, "cover.jpg"))
    except Exception:
        pass
