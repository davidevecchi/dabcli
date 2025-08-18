# search.py  
  
from api import get  
from config import config  
from utils import require_login  
from tabulate import tabulate  
  
def debug_print(msg: str):  
    """Print debug output if test_mode or debug is enabled."""  
    if getattr(config, "test_mode", False) or getattr(config, "debug", False):  
        print(f"[DEBUG] {msg}")  
  
def search_and_return(query: str, filter_type: str = None):  
    debug_print(f"Searching for '{query}' with filter={filter_type}")  
  
    params = {"q": query}  
    if filter_type:  
        params["type"] = filter_type  
  
    result = get("/search", params=params)  
    if not result:  
        print("API returned no result.")  
        return []  
  
    key_map = {"track": "tracks", "album": "albums", "artist": "artists"}  
  
    if filter_type:  
        data = result.get(key_map.get(filter_type, ""), [])  
  
        # Fallback if artists/albums are not returned directly  
        if not data:  
            if filter_type == "artist" and "tracks" in result:  
                seen = {}  
                for t in result["tracks"]:  
                    if t["artistId"] not in seen:  
                        seen[t["artistId"]] = {  
                            "id": t["artistId"],  
                            "name": t["artist"]  
                        }  
                data = list(seen.values())  
            elif filter_type == "album" and "tracks" in result:  
                seen = {}  
                for t in result["tracks"]:  
                    if t["albumId"] not in seen:  
                        seen[t["albumId"]] = {  
                            "id": t["albumId"],  
                            "title": t["albumTitle"],  
                            "artist": t["artist"],  
                            "artistId": t["artistId"],  
                            "releaseDate": t.get("releaseDate", "")  
                        }  
                data = list(seen.values())  
  
        return data  
  
    return result  
def search_and_print(query: str, filter_type: str = None):  
    if not require_login(config):  
        return  
  
    if filter_type:  
        results = search_and_return(query, filter_type)  
        if not results:  
            print("No results found.")  
            return  
        _print_table(results, filter_type)  
        return  
  
    debug_print(f"Performing separate searches for all types for '{query}'...")  
    for t in ["track", "album", "artist"]:  
        results = search_and_return(query, t)  
        if results:  
            _print_table(results, t)  
  
def _print_table(results, result_type: str):  
    if result_type == "track":  
        print(f"\nFound {len(results)} track(s):\n")  
        table = [  
            [track["id"], track["title"], f"{track['artist']} ({track.get('artistId', '—')})", track.get("albumTitle", "—")]  
            for track in results  
        ]  
        print(tabulate(table, headers=["ID", "Title", "Artist (ID)", "Album"], tablefmt="fancy_grid"))  
  
    elif result_type == "album":  
        print(f"\nFound {len(results)} album(s):\n")  
        table = [  
            [album["id"], album["title"], f"{album['artist']} ({album.get('artistId', '—')})", album.get("releaseDate", "")[:4]]  
            for album in results  
        ]  
        print(tabulate(table, headers=["ID", "Title", "Artist (ID)", "Year"], tablefmt="fancy_grid"))  
  
    elif result_type == "artist":  
        print(f"\nFound {len(results)} artist(s):\n")  
        table = [  
            [artist["id"], f"{artist['name']} ({artist['id']})"]  
            for artist in results  
        ]  
        print(tabulate(table, headers=["ID", "Name (ID)"], tablefmt="fancy_grid"))  
  
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