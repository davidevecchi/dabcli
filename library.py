import os

from api import get
from config import config
from cover import download_cover_image
from downloader import download_track
from tagger import tag_audio
from utils import require_login
from tqdm import tqdm
import shutil


def sanitize_filename(name):
    return ''.join(c for c in name if c.isalnum() or c in ' _-').rstrip()


def download_library(library_id: str, quality: str = None, cli_args=None):
    if not require_login(config):
        return
    
    result = get(f"/libraries/{library_id}?limit=9999&page=1")
    if not result or "library" not in result:
        print("[Library] Failed to load library.")
        return
    
    library = result["library"]
    tracks = library.get("tracks", [])
    if not tracks:
        print("[Library] No tracks found.")
        return
    
    title = sanitize_filename(library.get("name", f"library_{library_id}"))
    output_format = config.output_format
    quality = quality or ("27" if output_format == "flac" else "5")
    
    lib_folder = os.path.join(config.output_directory, f"{title} [{output_format.upper()}]")
    os.makedirs(lib_folder, exist_ok=True)
    
    tqdm.write(f"[Library] Downloading: {title} ({len(tracks)} tracks)")
    
    playlist_paths = []
    pbar = tqdm(tracks, position=1, dynamic_ncols=True)
    for idx, track in enumerate(pbar, 1):
        tqdm.write(f"[{idx}/{len(tracks)}] {track['title']} — {track['artist']}")
        raw_path = download_track(
            track_id=track["id"],
            quality=quality,
            directory=lib_folder,
            track_meta=track,
        )
        if raw_path == -1:
            continue
        if not raw_path:
            tqdm.write("[Library] Skipping: download failed.")
            continue
        
        converted_path = raw_path  # same format assumption
        # converted_path = convert_audio(raw_path, output_format)
        
        # Build metadata with CLI overrides
        metadata = {
            "title": getattr(cli_args, "title", None) or track.get("title", ""),
            "artist": getattr(cli_args, "artist", None) or track.get("artist", ""),
            "album": getattr(cli_args, "album", None) or track.get("albumTitle", ""),
            "genre": getattr(cli_args, "genre", None) or track.get("genre", ""),
            "date": getattr(cli_args, "date", None) or track.get("releaseDate", "")[:4],
        }
        
        # Download a cover file for this track (named via song title)
        from downloader import _sanitize_filename
        cover_url = track.get("albumCover")
        cover_path = None
        if cover_url:
            clean_title = _sanitize_filename(track.get("title", "cover"))
            cover_path = download_cover_image(
                cover_url, os.path.join(lib_folder, f"{clean_title}.jpg"),
            )
        
        # Tag the converted audio
        tag_audio(converted_path, metadata, cover_path=cover_path)
        
        # Delete the cover file unless user wants to keep it
        if cover_path and os.path.exists(cover_path) and not config.keep_cover_file:
            try:
                os.remove(cover_path)
            except Exception:
                pass
        
        # Remove raw file if needed
        if config.delete_raw_files and raw_path != converted_path:
            try:
                os.remove(raw_path)
            except Exception as e:
                tqdm.write(f"[Library] Could not delete raw file: {e}")
        
        playlist_paths.append(os.path.basename(converted_path))
        print()
        pbar.update(1)   # no need to touch ncols yourself
    
    # Write playlist
    # m3u_path = os.path.join(lib_folder, "library.m3u8")
    # with open(m3u_path, "w", encoding="utf-8") as m3u:
    #     for filename in playlist_paths:
    #         m3u.write(filename + "\n")
    
    print(f"[Library] Finished: {len(playlist_paths)} tracks saved to {lib_folder}")
    # print(f"[Library] Playlist written to: {m3u_path}")
