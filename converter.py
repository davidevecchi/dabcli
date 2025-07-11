# converter.py
import subprocess
import os
from config import config

def convert_audio(input_path: str, output_format: str = "mp3"):
    """
    Converts the given audio file to desired format using ffmpeg.
    Supported formats: mp3, flac, wav
    Returns path to converted file.
    """
    if not os.path.isfile(input_path):
        print("[Converter] File not found:", input_path)
        return None

    in_ext = os.path.splitext(input_path)[1].lower()
    out_ext = f".{output_format.lower()}"

    if in_ext == out_ext:
        print("[Converter] Skipping conversion: already in target format.")
        return input_path

    base, _ = os.path.splitext(input_path)
    output_path = f"{base}.{output_format}"

    # Choose ffmpeg codec
    if output_format == "mp3":
        codec = ["-codec:a", "libmp3lame", "-qscale:a", "2"]
    elif output_format == "flac":
        codec = ["-codec:a", "flac"]
    elif output_format == "wav":
        codec = ["-codec:a", "pcm_s16le"]
    else:
        print("[Converter] Unsupported output format:", output_format)
        return None

    command = ["ffmpeg", "-y", "-i", input_path] + codec + [output_path]

    try:
        subprocess.run(
            command,
            check=True,
            stdout=None if getattr(config, "debug", False) else subprocess.DEVNULL,
            stderr=None if getattr(config, "debug", False) else subprocess.DEVNULL
        )
        if not os.path.exists(output_path):
            print("[Converter] Conversion failed: output file not created.")
            return None

        print(f"[Converter] Converted to {output_format}: {output_path}")
        return output_path

    except subprocess.CalledProcessError as e:
        print("[Converter] ffmpeg conversion failed:", e)
        return None