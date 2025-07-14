import subprocess
import time
from api import get
from config import config
from utils import require_login

def get_stream_url(track_id: str, quality: str = None) -> str:
    if not require_login(config):
        return None

    quality = quality or config.stream_quality
    result = get("/stream", params={"trackId": track_id, "quality": quality})
    if not result:
        print(f"Could not fetch stream URL for track {track_id}.")
        return None
    return result.get("url")

def _print_metadata(track):
    if not track:
        return
    print("\nNow Playing:")
    print(f"   Title : {track.get('title', '—')}")
    print(f"   Artist: {track.get('artist', '—')}")
    print(f"   Album : {track.get('albumTitle', '—')}")
    print(f"   Year  : {track.get('releaseDate', '')[:4]}")
    print(f"   Genre : {track.get('genre', '—')}\n")

def _launch_mpv(stream_url: str, title: str = None):
    cmd = ["mpv", "--no-video", "--force-window=no", "--audio-display=no"]
    if title:
        cmd.append(f"--term-playing-msg=Now Playing: {title}")
    cmd.append(stream_url)

    try:
        subprocess.run(cmd)
    except FileNotFoundError:
        print("mpv not found. Please install it.")
    except Exception as e:
        print(f"Playback error: {e}")

def play_single(track_id: str, quality: str = None):
    if not require_login(config):
        return

    stream_url = get_stream_url(track_id, quality)
    if not stream_url:
        return
    print("Now Playing: Track ID", track_id)
    _launch_mpv(stream_url, title=f"Track ID {track_id}")

def play_queue(track_ids: list, quality: str = None):
    if not require_login(config):
        return

    for idx, track_id in enumerate(track_ids):
        print(f"\nTrack {idx + 1} of {len(track_ids)} — ID: {track_id}")
        play_single(track_id, quality=quality)
        time.sleep(1)

def get_library_tracks(library_id: str):
    if not require_login(config):
        return []

    result = get(f"/libraries/{library_id}")
    if not result or "library" not in result:
        print("Could not load library.")
        return []
    return result["library"].get("tracks", [])

def get_album_track_ids(album_id: str):
    if not require_login(config):
        return []

    result = get("/album", params={"albumId": album_id})
    if not result:
        return []
    album = result.get("album", result)
    return [t["id"] for t in album.get("tracks", [])]

def play_queue_with_metadata(tracks: list, quality: str = None):
    if not require_login(config):
        return

    for idx, track in enumerate(tracks):
        print(f"\nTrack {idx + 1} of {len(tracks)} — ID: {track['id']}")
        stream_url = get_stream_url(track["id"], quality)
        if not stream_url:
            continue
        _print_metadata(track)
        _launch_mpv(stream_url, title=track.get("title", None))
        time.sleep(1)

def stream_cli_entry(args):
    if getattr(args, "track_id", None):
        play_single(args.track_id, quality=args.quality)

    elif getattr(args, "album_id", None):
        track_ids = get_album_track_ids(args.album_id)
        if not track_ids:
            print("Album has no tracks or failed to load.")
            return
        play_queue(track_ids, quality=args.quality)

    elif getattr(args, "library_id", None):
        tracks = get_library_tracks(args.library_id)
        if not tracks:
            print("Library has no tracks or failed to load.")
            return

        if getattr(args, "mode", "stream") == "download":
            from downloader import download_track
            from converter import convert_audio

            print("Downloading library tracks...")
            output_format = config.output_format
            for idx, track in enumerate(tracks, 1):
                print(f"\n[{idx}/{len(tracks)}] Downloading track ID: {track['id']}")
                raw_path = download_track(
                    track_id=track["id"],
                    quality="27" if output_format == "flac" else "5",
                    directory=config.output_directory
                )
                if raw_path:
                    convert_audio(raw_path, output_format)
        else:
            play_queue_with_metadata(tracks, quality=args.quality)

    elif getattr(args, "queue", None):
        play_queue(args.queue, quality=args.quality)

    else:
        print("Please provide a --track-id, --album-id, --library-id, or --queue.")