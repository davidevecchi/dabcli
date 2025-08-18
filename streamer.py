import subprocess  
import time  
import tempfile  
import os  
import socket  
import json  
import threading  
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
        # Fetch album metadata including track list  
        result = get("/album", params={"albumId": args.album_id})  
        if not result or "album" not in result:  
            print("Album has no tracks or failed to load.")  
            return  
        full_tracks = result["album"].get("tracks", [])  
        if not full_tracks:  
            print("Album has no tracks or failed to load.")  
            return  
        play_ipc_queue(full_tracks, quality=args.quality)  
  
    elif getattr(args, "queue", None):  
        full_tracks = [{"id": tid, "title": f"Track {i+1}", "artist": "Unknown"}  
                       for i, tid in enumerate(args.queue)]  
        play_ipc_queue(full_tracks, quality=args.quality)  
  
    elif getattr(args, "library_id", None):  
        tracks = get_library_tracks(args.library_id)  
        if not tracks:  
            print("Library has no tracks or failed to load.")  
            return  
        play_ipc_queue(tracks, quality=args.quality)  
  
def play_ipc_queue(tracks, quality=None):  
    import itertools, sys, time  
  
    print("\n============ DAB CLI Player ============")  
    print("Loading playlist...", end="", flush=True)  
  
    spinner_running = True  
    def spinner():  
        for frame in itertools.cycle([".", "..", "...", " ..", "  .", "   "]):  
            if not spinner_running:  
                break  
            print(f"\rLoading playlist{frame}", end="", flush=True)  
            time.sleep(0.4)  
  
    spin_t = threading.Thread(target=spinner)  
    spin_t.start()  
  
    urls = []  
    for t in tracks:  
        url = get_stream_url(t['id'], quality=quality)  
        if url:  
            urls.append(url)  
  
    spinner_running = False  
    spin_t.join()  
  
    if not urls:  
        print("\rNo playable stream URLs.")  
        return  
  
    print("\rLoading playlist... Done.     ")  
    print("=========================================")  
  
    sock_path = os.path.join(tempfile.gettempdir(), "dab_mpv.sock")  
    try:  
        os.remove(sock_path)  
    except FileNotFoundError:  
        pass  
  
    cmd = [  
        "mpv",  
        "--no-video",  
        "--force-window=no",  
        "--audio-display=no",  
        "--msg-level=all=no",  
        "--term-playing-msg=",  
        f"--input-ipc-server={sock_path}"  
    ] + urls  
  
    print("\n[SPACE]=Play/Pause | > Next | < Prev | q Quit")  
  
    # State for timer  
    state = {"elapsed": 0, "paused": False, "started": False}  
  
    # IPC listener thread  
    def ipc_listener():  
        # Connect socket  
        time.sleep(0.4)  
        attempts = 0  
        while attempts < 10:  
            try:  
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)  
                s.connect(sock_path)  
                break  
            except FileNotFoundError:  
                attempts += 1  
                time.sleep(0.3)  
        else:  
            return  
  
        # Subscribe to playlist-pos, playback-time, pause  
        s.send(b'{"command": ["observe_property", 1, "playlist-pos"]}\n')  
        s.send(b'{"command": ["observe_property", 2, "playback-time"]}\n')  
        s.send(b'{"command": ["observe_property", 3, "pause"]}\n')  
  
        # Timer thread inside IPC, started when playback begins  
        def timer_loop():  
            while True:  
                if state["started"]:  
                    if state["paused"]:  
                        out = "(Paused)"  
                    else:  
                        # format HH:MM:SS from elapsed  
                        out = "[" + time.strftime("%H:%M:%S", time.gmtime(state["elapsed"])) + "]"  
                    sys.stdout.write("\r" + out)  
                    sys.stdout.flush()  
                time.sleep(1)  
  
        threading.Thread(target=timer_loop, daemon=True).start()  
  
        while True:  
            data = s.recv(4096)  
            if not data:  
                break  
            for raw in data.splitlines():  
                try:  
                    msg = json.loads(raw.decode())  
                except Exception:  
                    continue  
  
                # Track change event  
                if msg.get("event") == "property-change" and msg.get("name") == "playlist-pos":  
                    idx = msg.get("data", 0)  
                    if isinstance(idx, int) and idx < len(tracks):  
                        t = tracks[idx]  
                        state["elapsed"] = 0  
                        state["started"] = True  
                        print(f"\nNow Playing: {t.get('artist', '—')} — {t.get('title', '—')}")  
  
                # Playback time update  
                elif msg.get("event") == "property-change" and msg.get("name") == "playback-time":  
                    state["elapsed"] = int(msg.get("data", 0))  
  
                # Pause state change  
                elif msg.get("event") == "property-change" and msg.get("name") == "pause":  
                    state["paused"] = bool(msg.get("data", False))  
  
    threading.Thread(target=ipc_listener, daemon=True).start()  
  
    try:  
        subprocess.run(cmd)  
    except Exception as e:  
        print("mpv error:", e)  
  
    try:  
        os.remove(sock_path)  
    except Exception:  
        pass  
  
    # Cleanup  
    try:  
        os.remove(sock_path)  
    except Exception:  
        pass