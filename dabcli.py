import argparse
import os
from tabulate import tabulate

from api import login
from search import search_and_print, search_and_return, get_artist_discography, get_track_metadata_by_id
from downloader import download_track
from converter import convert_audio
from tagger import tag_audio
from album import download_album, find_album_by_title
from config import config, clear_credentials
from streamer import stream_cli_entry
from cover import download_cover_image
from utils import require_login

ASCII_ART = r"""
  _____          ____  __  __           _         _____ _      _____   
 |  __ \   /\   |  _ \|  \/  |         (_)       / ____| |    |_   _|  
 | |  | | /  \  | |_) | \  / |_   _ ___ _  ___  | |    | |      | |    
 | |  | |/ /\ \ |  _ <| |\/| | | | / __| |/ __| | |    | |      | |    
 | |__| / ____ \| |_) | |  | | |_| \__ \ | (__  | |____| |____ _| |_   
 |_____/_/    \_\____/|_|  |_|\__,_|___/_|\___|  \_____|______|_____|  
"""

CREDITS = """
Developed By: sherlockholmesat221b (sherlockholmesat221b@proton.me)
Special Thanks To: His Majesty superadmin0 (Creator of DABMusic)
Happy Birthday sherlockholmes221b (06 July)
"""

COMMANDS_HELP = """
Available Commands:

  dabcli.py login <email> <password>
      → Login with your DAB account

  dabcli.py status
      → Check login/authentication status

  dabcli.py logout
      → Clear saved credentials

  dabcli.py search "<query>" [--type track|album|artist]
      → Search for tracks, albums, or artists

  dabcli.py discography --artist-id <id>
      → Show all albums by a specific artist

  dabcli.py download --track-id <id> [--format mp3|flac|wav]
      → Download and tag a single track

  dabcli.py album "<album id or title>"
      → Download an entire album by ID or title

  dabcli.py play --track-id <id> | --album-id <id> | --queue <ids...> | --library-id <id>
      → Stream tracks, albums, or libraries

  dabcli.py library <library_id> [--quality ...]
      → Download an entire library by ID
      
  dabcli.py --version
      → Check version of DABMusic CLI
"""

def main():
    parser = argparse.ArgumentParser(
        description="DAB CLI — Download and Browse music from DAB Music Player",
        add_help=False
    )

    subparsers = parser.add_subparsers(dest="command")

    parser.add_argument("--version", action="store_true", help="Show current version")

    subparsers.add_parser("status", help="Check login/authentication status")
    subparsers.add_parser("logout", help="Clear token and credentials")

    login_parser = subparsers.add_parser("login", help="Login with your DAB account")
    login_parser.add_argument("email", help="Your DAB email")
    login_parser.add_argument("password", help="Your DAB password")

    search_parser = subparsers.add_parser("search", help="Search tracks, albums, and artists")
    search_parser.add_argument("query", help="Search query string")
    search_parser.add_argument("--type", choices=["track", "album", "artist"], default=None, help="Filter results")

    discog_parser = subparsers.add_parser("discography", help="Get artist discography")
    discog_parser.add_argument("--artist-id", required=True, help="Artist ID to fetch albums")

    dl_parser = subparsers.add_parser("download", help="Download and convert a track")
    dl_parser.add_argument("--track-id", required=True)
    dl_parser.add_argument("--format", choices=["mp3", "flac", "wav"])
    dl_parser.add_argument("--title", help="Track title")
    dl_parser.add_argument("--artist", help="Artist name")
    dl_parser.add_argument("--album", help="Album title")
    dl_parser.add_argument("--genre", help="Genre")
    dl_parser.add_argument("--date", help="Release year")
    dl_parser.add_argument("--path", help="Custom download directory")

    album_parser = subparsers.add_parser("album", help="Download an album by ID or title")
    album_parser.add_argument("album_id_or_title")

    play_parser = subparsers.add_parser("play", help="Stream one or more tracks")
    play_parser.add_argument("--track-id", help="Track ID to stream")
    play_parser.add_argument("--album-id", help="Album ID to stream entire album")
    play_parser.add_argument("--queue", nargs="+", help="List of track IDs to stream")
    play_parser.add_argument("--library-id", help="Library ID to stream all tracks")
    play_parser.add_argument("--quality", help="Audio quality (27 = FLAC, 5 = MP3)")
    play_parser.add_argument("--mode", choices=["stream", "download"], default="stream", help="Stream or download")

    library_parser = subparsers.add_parser("library", help="Download all tracks in a library")
    library_parser.add_argument("library_id", help="Library ID to download")
    library_parser.add_argument("--quality", help="Audio quality (27 = FLAC, 5 = MP3)")

    args = parser.parse_args()

    if args.version:
            try:
                        from pathlib import Path
                        version = Path("VERSION").read_text().strip()
            except Exception:
                        version = "unknown"
            print(f"DAB CLI Version: {version}")
            return

    if not args.command:
        print(ASCII_ART)
        print(CREDITS)
        print(COMMANDS_HELP)
        return

    if args.command == "login":
        login(args.email, args.password)

    elif args.command == "status":
        print("=== DAB CLI Authentication Status ===")
        if config.token:
            masked_email = config.email[:2] + "****" + config.email[-6:] if config.email else "(unknown)"
            print("Login status  : Logged in")
            print("Email         :", masked_email)
            print("Token present :", "Yes")
        else:
            print("Login status  : Not logged in")
            print("Token present : No")

    elif args.command == "logout":
        clear_credentials()
        print("You are now logged out.")

    elif args.command == "search":
        if not require_login(config): return
        search_and_print(args.query, args.type)

    elif args.command == "discography":
        if not require_login(config): return
        get_artist_discography(args.artist_id)

    elif args.command == "download":
        if not require_login(config): return
        print("Starting full download pipeline...")
        output_format = args.format or config.output_format
        directory = args.path or config.output_directory

        track_meta_raw = get_track_metadata_by_id(args.track_id)
        if not track_meta_raw:
            print("Track not found or unavailable.")
            return

        track_meta = {
            "title": args.title or track_meta_raw.get("title", ""),
            "artist": args.artist or track_meta_raw.get("artist", ""),
            "albumTitle": args.album or track_meta_raw.get("albumTitle", ""),
            "genre": args.genre or track_meta_raw.get("genre", ""),
            "releaseDate": args.date or track_meta_raw.get("releaseDate", "")
        }

        raw_path = download_track(
            track_id=args.track_id,
            quality="27" if output_format == "flac" else "5",
            directory=directory,
            track_meta=track_meta
        )
        if not raw_path:
            return

        final_path = convert_audio(raw_path, output_format)
        if not final_path:
            return

        cover_url = track_meta.get("albumCover")
        cover_path = download_cover_image(cover_url, os.path.join(directory, "cover.jpg")) if cover_url else None

        if config.use_metadata_tagging:
            tag_audio(final_path, {
                "title": track_meta["title"],
                "artist": track_meta["artist"],
                "album": track_meta["albumTitle"],
                "genre": track_meta["genre"],
                "date": track_meta["releaseDate"][:4]
            }, cover_path=cover_path)

        if cover_path and os.path.exists(cover_path) and not config.keep_cover_file:
            os.remove(cover_path)

    elif args.command == "album":
        if not require_login(config): return
        album_input = args.album_id_or_title
        print(f"Searching for album titled '{album_input}'...")
        matches = find_album_by_title(album_input)

        if not matches:
            print("No albums found matching that title.")
            return

        if len(matches) == 1:
            album = matches[0]
            print(f"Selected: {album['title']} by {album['artist']} (ID: {album['id']})")
            download_album(album["id"])
            return

        print("Multiple matches found:\n")
        table = [
            [idx, album["title"], album["artist"], album.get("releaseDate", "")[:4], album["id"]]
            for idx, album in enumerate(matches, 1)
        ]
        print(tabulate(table, headers=["No", "Title", "Artist", "Year", "Album ID"], tablefmt="fancy_grid"))

        try:
            choice = int(input("\nEnter the number of the album to download: "))
            selected = matches[choice - 1]
            download_album(selected["id"])
        except (ValueError, IndexError):
            print("Invalid selection.")

    elif args.command == "play":
        if not require_login(config): return
        stream_cli_entry(args)

    elif args.command == "library":
        if not require_login(config): return
        from library import download_library
        download_library(args.library_id, quality=args.quality)

    else:
        print("Unknown command.\n")
        print(ASCII_ART)
        print(COMMANDS_HELP)

if __name__ == "__main__":
    main()