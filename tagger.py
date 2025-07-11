import os
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, APIC, ID3NoHeaderError
from config import config


def tag_audio(file_path: str, metadata: dict, cover_path: str = None):
    """
    Tags metadata into a music file and optionally embeds cover art.

    metadata = {
        'title': ..., 'artist': ..., 'album': ..., 'genre': ..., 'date': ...
    }
    """

    if not config.use_metadata_tagging:
        print("Skipping tagging (disabled in config).")
        return False

    if not os.path.exists(file_path):
        print("File not found:", file_path)
        return False

    ext = os.path.splitext(file_path)[-1].lower()

    try:
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

            if cover_path and os.path.exists(cover_path):
                id3 = ID3(file_path)
                with open(cover_path, "rb") as img:
                    id3.add(APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=img.read()
                    ))
                id3.save()

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
            audio.save()

        else:
            print("Unsupported format for tagging:", ext)
            return False

        print(f"Metadata tagged: {file_path}")
        return True

    except Exception as e:
        print("Tagging failed:", str(e))
        return False