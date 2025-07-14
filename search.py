# search.py

from api import get
from config import config
from utils import require_login
from tabulate import tabulate

def search_and_return(query: str, filter_type: str = "track"):
    """
    Low-level search, returns a list depending on filter_type.
    """
    if filter_type not in ("track", "album", "artist"):
        print(f"Unknown filter type '{filter_type}' — must be 'track', 'album' or 'artist'")
        return []

    result = get("/search", params={"q": query, "type": filter_type})
    if not result:
        print("API returned no result.")
        return []

    return result.get(
        {"track": "tracks", "album": "albums", "artist": "artists"}[filter_type],
        []
    )

def search_and_print(query: str, filter_type: str = None):
    """
    User-facing smart search:
    - If --type is given: show only that category
    - If not: show tracks + albums + artists
    """
    if not require_login(config):
        return

    if filter_type is not None:
        results = search_and_return(query, filter_type)
        if not results:
            print("No results found.")
            return

        _print_table(results, filter_type)
        return

    # Default case: show all types
    print(f"\nSearching all types for '{query}'...\n")

    types = ["track", "album", "artist"]
    for t in types:
        results = search_and_return(query, t)
        if results:
            _print_table(results, t)

def _print_table(results, result_type: str):
    if result_type == "track":
        print(f"\nFound {len(results)} track(s):\n")
        table = [
            [track["id"], track["title"], track["artist"], track.get("albumTitle", "—")]
            for track in results
        ]
        print(tabulate(table, headers=["ID", "Title", "Artist", "Album"], tablefmt="fancy_grid"))

    elif result_type == "album":
        print(f"\nFound {len(results)} album(s):\n")
        table = [
            [album["id"], album["title"], album["artist"], album.get("releaseDate", "")[:4]]
            for album in results
        ]
        print(tabulate(table, headers=["ID", "Title", "Artist", "Year"], tablefmt="fancy_grid"))

    elif result_type == "artist":
        print(f"\nFound {len(results)} artist(s):\n")
        table = [
            [artist["id"], artist["name"]]
            for artist in results
        ]
        print(tabulate(table, headers=["ID", "Name"], tablefmt="fancy_grid"))

def get_artist_discography(artist_id: str):
    """
    Fetch and display all albums by an artist (via /discography).
    """
    if not require_login(config):
        return

    result = get("/discography", params={"artistId": artist_id})
    if not result:
        print("Could not fetch artist discography.")
        return

    artist_name = result.get("artist", {}).get("name", "Unknown Artist")
    albums = result.get("albums", [])

    if not albums:
        print(f"No albums found for {artist_name}")
        return

    print(f"\nDiscography for {artist_name}:\n")
    table = [
        [album["id"], album["title"], album.get("releaseDate", "")[:4], album.get("genre", "—")]
        for album in albums
    ]
    print(tabulate(table, headers=["ID", "Title", "Year", "Genre"], tablefmt="fancy_grid"))

def get_track_metadata_by_id(track_id: str) -> dict:
    results = search_and_return(str(track_id), filter_type="track")
    for track in results:
        if str(track.get("id")) == str(track_id):
            return track
    return {}