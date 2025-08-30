# artist.py
import os

from tabulate import tabulate

from album import download_album
from api import get
from config import config
from search import search_and_return
from utils import require_login, sanitize_filename


def _search_artist_by_name(name: str):
    print(f"DEBUG: searching artist '{name}'")
    results = search_and_return(name, filter_type="artist")
    if not results:
        print("[Discography] No artist results found.")
        return []
    return results


def get_discography(artist_id, sort_by="year", sort_order="asc", fetch_all=False, limit=None):
    """    
    Returns full structure: {"artist": {...}, "albums": [...]}    
    - fetch_all=True will paginate until no more results.    
    - limit: stops after retrieving this many albums (even if fetch_all=True).    
    """
    full_data = None
    albums = []
    offset = 0
    per_page = 35
    
    while True:
        params = {
            "artistId": artist_id,
            "sortBy": sort_by,
            "sortOrder": sort_order,
            "offset": offset,
            "limit": per_page,
        }
        result = get("/discography", params=params)
        if not result:
            break
        
        if full_data is None:
            full_data = {
                "artist": result.get("artist", {}),
                "albums": [],
            }
        
        albums.extend(result.get("albums", []))
        
        # Stop if limit reached    
        if limit is not None and len(albums) >= limit:
            albums = albums[:limit]
            break
        
        pag = result.get("pagnation", {})
        if not fetch_all or not pag.get("hasMore", False):
            break
        
        offset += per_page
    
    if full_data:
        full_data["albums"] = albums
    return full_data


def print_discography(data):
    artist = data.get("artist", {})
    albums = data.get("albums", [])
    
    if not artist.get('name', None):
        print("[Discography] No artist name found.")
        exit(1)
    
    print(f"[Discography] {artist.get('name', 'Unknown Artist')} ({artist.get('albumsCount', len(albums))} albums)\n")
    table = [
        [
            idx + 1,
            alb.get("title", ""),
            alb.get("releaseDate", "")[:4],
            alb.get("genre", ""),
            alb.get("trackCount", ""),
            alb.get("id", ""),
        ]
        for idx, alb in enumerate(albums)
    ]
    print(tabulate(table, headers=["#", "Title", "Year", "Genre", "Tracks", "Album ID"], tablefmt="fancy_grid"))


def download_discography(
    artist_query: str,
    sort_by: str = "year",
    sort_order: str = "asc",
    view_only=False,
    limit=None,
    cli_args=None,  # <--- add this
):
    if not require_login(config):
        return
    
    # Resolve artist_id from name if needed
    if not (artist_query.isdigit() or artist_query.lower().startswith("ar")):
        matches = _search_artist_by_name(artist_query)
        if not matches:
            return
        if len(matches) == 1:
            artist_id = matches[0]["id"]
            artist_name = matches[0]["name"]
        else:
            print("[Discography] Multiple matches found:\n")
            table = [
                [idx + 1, art["name"], art.get("id", ""), art.get("albumsCount", "")]
                for idx, art in enumerate(matches)
            ]
            print(tabulate(table, headers=["No", "Name", "Artist ID", "Albums"], tablefmt="fancy_grid"))
            try:
                choice = int(input("\nEnter the number of the artist to select: "))
                sel = matches[choice - 1]
                artist_id = sel["id"]
                artist_name = sel["name"]
            except (ValueError, IndexError):
                print("[Discography] Invalid selection.")
                return
    else:
        artist_id = artist_query
        artist_name = artist_query
    
    # Fetch albums
    data = get_discography(
        artist_id,
        sort_by,
        sort_order,
        fetch_all=not view_only or limit is not None,
        limit=limit,
    )
    if not data:
        return
    
    if view_only:
        print_discography(data)
        return
    
    albums = data["albums"]
    artist = data['artist']['name']
    if artist == "Unknown Artist":
        exit(0)
        
    print(f"[Discography] Starting download for {len(albums)} albums by {artist}...\n")
    
    completed = 0
    failed = 0
    for idx, alb in enumerate(albums, 1):
        print(f"\n[Discography] ({idx}/{len(albums)}) {alb['title']} — {alb.get('releaseDate', '')[:4]}")
        try:
            # Pass cli_args to download_album so metadata overrides are applied
            directory = os.path.join(config.output_directory, "discographies", sanitize_filename(f"{artist} - {artist_id}"))
            download_album(alb["id"], cli_args=cli_args, directory=directory, discography_artist=artist)
            completed += 1
        except KeyboardInterrupt:
            print("\n[Discography] Interrupted by user.")
            break
        except Exception as e:
            print(f"[Discography] Failed: {e}")
            failed += 1
    
    print(f"\n[Discography] Finished. Completed: {completed} | Failed: {failed}")
