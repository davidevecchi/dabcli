import os
import sys
import threading
import time
import unicodedata

import requests
from tqdm import tqdm

from api import get
from config import config
from utils import require_login

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


def _wait_if_paused():
    global _PAUSED, _STOPPED
    while _PAUSED and not _STOPPED:
        time.sleep(0.2)


# --- Filename utilities ---
def _sanitize_filename(name: str) -> str:
    name = unicodedata.normalize("NFKC", name)
    return "".join(c for c in name if c.isalnum() or c in " -_()[]{}.,").strip() or "untitled"


def _format_filename(track: dict, track_id: int, output_format: str, index: int = None) -> str:
    filename = ' - '.join([
        track.get("artist", "unknown"),
        track.get("title", "untitled"),
        str(track_id),
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
    track_meta: dict = None
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
    
    filename = _format_filename(track_meta, track_id, config.output_format, index)
    filename = _sanitize_filename(filename)
    filepath = os.path.join(directory, filename)
    
    # Skip any existing file
    if os.path.exists(filepath):
        tqdm.write(f"[Downloader] Skipped (exists): {filepath}")
        return -1
    
    if config.test_mode:
        tqdm.write(f"[TEST MODE] Would download track {track_id} → {filepath}")
        with open(filepath, "wb") as f:
            f.write(b"PHANTOM DATA")
        return filepath
    
    stream_url = get_stream_url(track_id, quality)
    if not stream_url:
        return None
    
    tqdm.write(f"[Downloader] Downloading: {filepath}")
    tqdm.write("[Controls] Press 'p' = Pause/Resume | 'q' = Stop")
    
    _start_controls()  # launch keyboard thread
    
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
                disable=not getattr(config, "show_progress", True),
            ) as pbar:
                _CURRENT_PBAR = pbar
                for chunk in r.iter_content(chunk_size=8192):
                    if _STOPPED:
                        tqdm.write("[Downloader] Download stopped before completion.")
                        _CURRENT_PBAR = None
                        return None
                    _wait_if_paused()
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            tqdm.write("[Downloader] Download completed.")
            return filepath
    
    except requests.RequestException as e:
        tqdm.write(f"[Downloader] Download failed: {e}")
        return None
    except OSError as e:
        tqdm.write(f"[Downloader] File write error: {e}")
        return None
