# cover.py
import requests
import os

def download_cover_image(url: str, save_path: str) -> str:
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        return save_path
    except Exception as e:
        print(f"Cover download failed: {e}")
        return None