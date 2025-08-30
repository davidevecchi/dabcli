import glob
import os
import sys
import threading
import time

import requests
from tqdm import tqdm

from api import get
from config import config
from utils import require_login, sanitize_filename

# --- State flags ---
_PAUSED = False
_STOPPED = False
_CURRENT_PBAR = None


# --- Keyboard listener (cross-platform) ---
def _keypress_listener():
    """Thread: watches keyboard input for pause/resume/stop."""
    global _PAUSED, _STOPPED
    
    if os.name == "nt":  # Windows
        import msvcrt
        while not _STOPPED:
            if msvcrt.kbhit():
                key = msvcrt.getch().decode(errors="ignore").lower()
                if key == "p":
                    _PAUSED = not _PAUSED
                    tqdm.write("[Downloader] Paused" if _PAUSED else "[Downloader] Resumed")
                    if _CURRENT_PBAR and not _PAUSED:
                        _CURRENT_PBAR.refresh()
                elif key == "q":
                    _STOPPED = True
                    tqdm.write("[Downloader] Stopped by user")
            time.sleep(0.1)
    else:  # POSIX (Linux/macOS)
        import termios, tty, select
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        try:
            while not _STOPPED:
                dr, _, _ = select.select([sys.stdin], [], [], 0.1)
                if dr:
                    key = sys.stdin.read(1).lower()
                    if key == "p":
                        _PAUSED = not _PAUSED
                        tqdm.write("[Downloader] Paused" if _PAUSED else "[Downloader] Resumed")
                        if _CURRENT_PBAR and not _PAUSED:
                            _CURRENT_PBAR.refresh()
                    elif key == "q":
                        _STOPPED = True
                        tqdm.write("[Downloader] Stopped by user")
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _start_controls():
    t = threading.Thread(target=_keypress_listener, daemon=True)
    t.start()


_start_controls()  # launch keyboard thread


def _wait_if_paused():
    global _PAUSED, _STOPPED
    while _PAUSED and not _STOPPED:
        time.sleep(0.2)


def _format_filename(track: dict, track_id: str, output_format: str, index: int = None) -> str:
    filename = ' - '.join([
        track.get("artist", "unknown")[:64],
        track.get("title", "untitled")[:64],
        track_id,
    ])
    if index is not None:
        return f"{index:02d} - {filename}.{output_format}"
    return f"{filename}.{output_format}"


def get_stream_url(track_id: str, quality: str = "27"):
    if not require_login(config):
        return None
    result = get("/stream", params={"trackId": track_id, "quality": quality})
    if not result:
        return None
    return result.get("url")


# --- Main download ---
def download_track(
    track_id: str,
    quality: str = None,
    directory: str = None,
    index: int = None,
    track_meta: dict = None,
):
    global _CURRENT_PBAR, _PAUSED, _STOPPED
    _PAUSED = False
    _STOPPED = False
    _CURRENT_PBAR = None
    
    if not require_login(config):
        return None
    
    quality = quality or ("27" if config.output_format == "flac" else "5")
    
    directory = directory or config.output_directory
    os.makedirs(directory, exist_ok=True)
    
    filename = _format_filename(track_meta, str(track_id), config.output_format, index)
    filename = sanitize_filename(filename)
    filepath = os.path.join(directory, filename)
    suffix = f" - {track_id}.{config.output_format}"
    
    # Skip any existing file
    if os.path.exists(filepath):
        tqdm.write(f"[Downloader] ⏭️ Skipped (exists): {filepath}\n")
        return -1
    
    pattern = os.path.join(directory, "*{suffix}")
    matches = glob.glob(pattern, recursive=False)
    for src_path in matches:
        os.rename(src_path, filepath)
        tqdm.write(f"[Downloader] ✏️ Renamed (exists): {filepath}\n")
        return -1
    
    pattern = os.path.join(config.output_directory, "**", f"*{suffix}")
    matches = glob.glob(pattern, recursive=True)
    for src_path in matches:
        # Only real files, skip links
        if not os.path.isfile(src_path) or os.path.islink(src_path):
            continue
        
        try:
            os.link(src_path, filepath)
            tqdm.write(f"[Downloader] 🔗 Linked existing file → {filepath}\n"
                       f"             (hardlink from {src_path})\n")
            return -1
        except OSError:
            try:
                os.symlink(src_path, filepath)
                tqdm.write(f"[Downloader] ↗️ Linked existing file → {filepath}\n"
                           f"             (symlink to {src_path})\n")
                return -1
            except OSError as e2:
                tqdm.write(f"[Downloader] ❌ Failed to create link to existing file: {e2}")
                break
    
    if config.test_mode:
        tqdm.write(f"[TEST MODE] Would download track {track_id} → {filepath}")
        with open(filepath, "wb") as f:
            f.write(b"PHANTOM DATA")
        return filepath
    
    stream_url = get_stream_url(track_id, quality)
    if not stream_url:
        return None
    
    tqdm.write(f"[Downloader] Downloading: {filepath}")
    # tqdm.write("[Controls] Press 'p' = Pause/Resume | 'q' = Stop")
    
    completed = False
    try:
        with requests.get(stream_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            with open(filepath, "wb") as f, tqdm(
                total=total,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc="Downloading",
                ncols=70,
                leave=False,
                disable=not getattr(config, "show_progress", True),
                position=0,
            ) as pbar:
                _CURRENT_PBAR = pbar
                for chunk in r.iter_content(chunk_size=8192):
                    if _STOPPED:
                        tqdm.write("[Downloader] ❌ Download stopped before completion.")
                        os.remove(filepath)
                        _CURRENT_PBAR = None
                        return None
                    _wait_if_paused()
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            tqdm.write("[Downloader] ✅ Download completed.")
            completed = True
    
    except requests.RequestException as e:
        tqdm.write(f"[Downloader] ❌ Download failed: {e}")
    except OSError as e:
        tqdm.write(f"[Downloader] ❌ File write error: {e}")
    except KeyboardInterrupt as e:
        tqdm.write(f"[Downloader] ❌ Session stopped by user")
        os.remove(filepath)
        exit(0)
    finally:
        tqdm.write("")
        if completed:
            return filepath
        os.remove(filepath)
        return None
