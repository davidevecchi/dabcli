# tagger.py

import os
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, ID3NoHeaderError, APIC, USLT
from config import config
from api import get_lyrics

def save_lrc(file_path: str, lyrics: str):
    base, _ = os.path.splitext(file_path)
    lrc_path = base + ".lrc"
    with open(lrc_path, "w", encoding="utf-8") as f:
        f.write(lyrics)
    if config.debug:
        print(f"[tagger] Saved synced lyrics to {lrc_path}")

def tag_audio(file_path: str, metadata: dict, cover_path: str = None):
    """
    Tags metadata, cover art, and lyrics (auto-fetched) into MP3 or FLAC.
    Any other format is skipped.
    """
    if not config.use_metadata_tagging or not os.path.exists(file_path):
        return False

    title  = metadata.get("title", "")
    artist = metadata.get("artist", "")

    lyrics, unsynced = get_lyrics(title, artist) if config.get_lyrics else (None, None)

    ext = os.path.splitext(file_path)[-1].lower()

    try:
        # MP3
        if ext == ".mp3":
            try:
                audio = EasyID3(file_path)
            except ID3NoHeaderError:
                audio = EasyID3()
                audio.save(file_path)
                audio = EasyID3(file_path)

            for key, value in metadata.items():
                if key in EasyID3.valid_keys.keys():
                    audio[key] = value
            audio.save()

            id3 = ID3(file_path)

            if cover_path and os.path.exists(cover_path):
                with open(cover_path, "rb") as img:
                    id3.add(APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=img.read()
                    ))

            if config.get_lyrics and lyrics:
                if unsynced:
                    id3.add(USLT(
                        encoding=3,
                        lang="eng",
                        desc="Lyrics",
                        text=lyrics
                    ))
                else:
                    save_lrc(file_path, lyrics)

            id3.save()

        # FLAC
        elif ext == ".flac":
            audio = FLAC(file_path)
            for key, value in metadata.items():
                audio[key] = value

            if cover_path and os.path.exists(cover_path):
                pic = Picture()
                pic.type = 3
                pic.mime = "image/jpeg"
                pic.desc = "Cover"
                with open(cover_path, "rb") as img:
                    pic.data = img.read()
                audio.add_picture(pic)

            if config.get_lyrics and lyrics:
                if unsynced:
                    audio["LYRICS"] = lyrics
                else:
                    save_lrc(file_path, lyrics)

            audio.save()

        else:
            if config.debug:
                print(f"[tagger] Skipping tag: unsupported format {ext}")
            return False

        return True

    except Exception as e:
        if config.debug:
            print(f"[tagger] Tagging failed for {file_path}: {e}")
        return False