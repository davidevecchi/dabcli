# api.py

import requests
from config import config

BASE_URL = "https://dab.yeet.su/api"

def get_auth_header():
    return config.get_auth_header()

def login(email: str, password: str):
    session = requests.Session()
    url = "https://dab.yeet.su/api/auth/login"
    payload = {"email": email, "password": password}

    try:
        resp = session.post(url, json=payload)
    except requests.RequestException as e:
        print(f"Network error during login: {e}")
        return

    if resp.status_code == 200 and "session" in session.cookies:
        token = session.cookies.get("session")
        config.email = email
        config.password = password
        config._save_token(token)
        print("Login successful. Token and credentials saved.")
    else:
        print("Login failed. Check email/password.")
        print(resp.text)

# --- Unified response handler ---
def _safe_json(resp, endpoint):
    try:
        return resp.json()
    except ValueError:
        print(f"Invalid JSON response from {endpoint}")
        if config.debug:
            print(f"Raw response:\n{resp.text[:300]}...\n")
        return None

# --- Request core ---
def _request(method: str, endpoint: str, **kwargs):
    headers = config.get_auth_header()
    url = BASE_URL + endpoint
    if config.debug:
        print(f"[DEBUG] {method} {url} | {kwargs}")
    try:
        resp = requests.request(method, url, headers=headers, **kwargs)
        resp.raise_for_status()
        return _safe_json(resp, endpoint)
    except requests.RequestException as e:
        print(f"{method} error on {endpoint}: {e}")
        return None

# --- API method wrappers ---
def get(endpoint: str, params=None):
    return _request("GET", endpoint, params=params)

def post(endpoint: str, json=None):
    return _request("POST", endpoint, json=json)

def delete(endpoint: str, params=None):
    return _request("DELETE", endpoint, params=params)

def patch(endpoint: str, json=None):
    return _request("PATCH", endpoint, json=json)