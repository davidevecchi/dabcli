import os
import json
import requests
from dataclasses import dataclass, field

# === FIX: ALWAYS POINT TO THE CONFIG NEXT TO THIS FILE =========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
# ==============================================================

@dataclass
class Config:
    email: str = ""
    password: str = ""
    output_format: str = "flac"
    output_directory: str = "./downloads"
    use_metadata_tagging: bool = True
    token: str = ""
    stream_quality: str = "27"
    stream_player: str = "mpv"
    test_mode: bool = False
    delete_raw_files: bool = True
    keep_cover_file: bool = False
    get_lyrics: bool = True 

    debug: bool = field(default=False, init=False)
    show_progress: bool = field(default=True, init=False)

    def __post_init__(self):
        if os.path.exists(CONFIG_PATH):
            self._load_config()
    debug: bool = field(default=False, init=False)
    show_progress: bool = field(default=True, init=False)

    def _load_config(self):
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Invalid JSON in config file: {e}")

        self.email = data.get("email", self.email)
        self.password = data.get("password", self.password)
        self.output_format = data.get("output_format", self.output_format)
        self.output_directory = data.get("output_directory", self.output_directory)
        self.use_metadata_tagging = data.get("use_metadata_tagging", self.use_metadata_tagging)
        self.token = data.get("token", self.token)
        self.stream_quality = data.get("stream_quality", self.stream_quality)
        self.stream_player = data.get("stream_player", self.stream_player)
        self.test_mode = data.get("test_mode", self.test_mode)
        self.delete_raw_files = data.get("delete_raw_files", self.delete_raw_files)
        self.keep_cover_file = data.get("keep_cover_file", self.keep_cover_file)
        self.get_lyrics = data.get("get_lyrics", self.get_lyrics)
        self.debug = data.get("debug", self.debug)
        self.show_progress = data.get("show_progress", self.show_progress)

    def _save_token(self, token: str):
        self.token = token
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}

        data.update({
            "token": token,
            "email": self.email,
            "password": self.password,
            "stream_quality": self.stream_quality,
            "stream_player": self.stream_player,
            "output_format": self.output_format,
            "output_directory": self.output_directory,
            "keep_cover_file": self.keep_cover_file,
           "get_lyrics": self.get_lyrics  # save
        })

        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=4)

    def _auto_login_if_needed(self):
        if not self.token and self.email and self.password:
            session = requests.Session()
            url = "https://dab.yeet.su/api/auth/login"
            payload = {"email": self.email, "password": self.password}
            resp = session.post(url, json=payload)

            if resp.status_code == 200 and "session" in session.cookies:
                token = session.cookies.get("session")
                self._save_token(token)
                print("Logged in and token saved to config.")
            else:
                raise Exception("Login failed. Check email/password in config.json.")

    def _retry_login(self):
        if not self.email or not self.password:
            raise Exception("Cannot re-authenticate: Email or password missing from config.json")

        session = requests.Session()
        url = "https://dab.yeet.su/api/auth/login"
        payload = {"email": self.email, "password": self.password}
        resp = session.post(url, json=payload)

        if resp.status_code == 200 and "session" in session.cookies:
            token = session.cookies.get("session")
            self._save_token(token)
            self.token = token
            print("Auto-login successful, token refreshed.")
        else:
            raise Exception("Auto-login failed. Please check credentials in config.json")

    def get_auth_header(self):
        if not self.token:
            print("No token found, attempting login...")
            self._retry_login()
        return {"Cookie": f"session={self.token}"}

    def is_logged_in(self):
        return bool(self.token)

    def logout(self):
        self.token = ""
        self.email = ""
        self.password = ""
        self._save_token("")
        print("You have been logged out.")

def clear_credentials():
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
        else:
            data = {}

        data.pop("token", None)
        data.pop("email", None)
        data.pop("password", None)

        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Failed to clear credentials: {e}")

config = Config()