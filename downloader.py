#downloader.py  
  
import signal    
import os    
import unicodedata    
import requests    
from tqdm import tqdm    
from config import config    
from api import get    
from utils import require_login    
    
_PAUSED = False    
_STOPPED = False    
    
def _sanitize_filename(name: str) -> str:    
    name = unicodedata.normalize("NFKC", name)    
    return "".join(c for c in name if c.isalnum() or c in " -_()[]{}.,").strip() or "untitled"    
    
def _format_filename(track: dict, output_format: str, index: int = None) -> str:    
    title = _sanitize_filename(track.get("title") or "untitled")    
    if index is not None:    
        return f"{index:02d} - {title}.{output_format}"    
    return f"{title}.{output_format}"    
    
def get_stream_url(track_id: str, quality: str = "27"):    
    if not require_login(config):    
        return None    
    result = get("/stream", params={"trackId": track_id, "quality": quality})    
    if not result:    
        return None    
    return result.get("url")    
    
def _toggle_pause(signum, frame):    
    global _PAUSED    
    _PAUSED = not _PAUSED    
    if _PAUSED:    
        tqdm.write("[Downloader] Paused — press Ctrl+Z to resume, Ctrl+C to stop")    
    else:    
        tqdm.write("[Downloader] Resumed")    
        if _CURRENT_PBAR:    
            _CURRENT_PBAR.refresh()    
    
def _stop_download(signum, frame):    
    global _STOPPED    
    _STOPPED = True    
    tqdm.write("[Downloader] Stopped by user")    
    
# Register keys: Ctrl+Z = pause/resume, Ctrl+C = stop    
signal.signal(signal.SIGTSTP, _toggle_pause)    
signal.signal(signal.SIGINT, _stop_download)    
    
_CURRENT_PBAR = None  # holds current tqdm object for refresh on resume    
    
def download_track(track_id: str, filename: str = None, quality: str = None, directory: str = None, index: int = None, track_meta: dict = None):    
    global _CURRENT_PBAR, _PAUSED, _STOPPED    
    _PAUSED = False    
    _STOPPED = False    
    
    if not require_login(config):    
        return None    
    
    quality = quality or ("27" if config.output_format == "flac" else "5")    
    directory = directory or config.output_directory    
    os.makedirs(directory, exist_ok=True)    
    
    if not filename and track_meta:    
        filename = _format_filename(track_meta, config.output_format, index)    
    
    filename = _sanitize_filename(filename)    
    filepath = os.path.join(directory, filename)    
    
    # Skip any existing file    
    if os.path.exists(filepath):    
        tqdm.write(f"[Downloader] Skipped (exists): {filepath}")    
        return filepath    
    
    if config.test_mode:    
        tqdm.write(f"[TEST MODE] Would download track {track_id} → {filepath}")    
        with open(filepath, "wb") as f:    
            f.write(b"PHANTOM DATA")    
        return filepath    
    
    stream_url = get_stream_url(track_id, quality)    
    if not stream_url:    
        return None    
    
    tqdm.write(f"[Downloader] Downloading: {filepath}")    
    tqdm.write("[Controls] Ctrl+Z = Pause/Resume | Ctrl+C = Stop")    
    
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
                disable=not getattr(config, "show_progress", True)    
            ) as pbar:    
                _CURRENT_PBAR = pbar    
                for chunk in r.iter_content(chunk_size=8192):    
                    if _STOPPED:    
                        tqdm.write("[Downloader] Download stopped before completion.")    
                        _CURRENT_PBAR = None    
                        return None    
                    while _PAUSED and not _STOPPED:    
                        signal.pause()  # wait until resumed or stopped    
                    if chunk:    
                        f.write(chunk)    
                        pbar.update(len(chunk))    
    
        # After tqdm close and download completion    
            tqdm.write("[Downloader] Download completed.")    
            return filepath    
    
    except requests.RequestException as e:    
        tqdm.write(f"[Downloader] Download failed: {e}")    
        return None    
    except OSError as e:    
        tqdm.write(f"[Downloader] File write error: {e}")    
        return None