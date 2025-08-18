# 🎧 DABMusic CLI

**DABMusic CLI** is an advanced, extensible, and user-friendly command-line tool for accessing [DABMusic](https://dab.yeet.su) — a free, open-source digital music library and streaming service.  
It supports searching, downloading, metadata tagging, artist discography downloads, local streaming, and more — all from your terminal.

---

## 🚀 What's New in v2.0

- **Smarter Downloader**: Skips existing files; supports pause/resume/stop  
- **Artist Discography Download**: Fetch all albums by artist name or ID  
- **Enhanced MPV IPC Player**: Stream tracks, albums, libraries, or queues with live metadata, timers, and playback controls (space=play/pause, arrows=next/prev, q=quit)  
- **Lyrics & Cover Embedding**: Auto-download covers and lyrics  
- **Metadata Overrides**: Customize title, artist, album, genre, date, and path during downloads  
- **Version Checking & Improved CLI Help**: Always know if your CLI is up-to-date  

> v2.0 makes downloads smarter, streaming interactive, and metadata fully customizable.

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/sherlockholmesat221b/dabcli.git
cd dabcli
````

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the CLI

```bash
python3 dabcli.py
```

---

## 💡 Usage Examples

### 🔐 Log In / 🔓 Log Out

```bash
python3 dabcli.py login you@example.com yourpassword
python3 dabcli.py logout
```

### 🔍 Search

```bash
python3 dabcli.py search "Michael Jackson"
python3 dabcli.py search "Michael Jackson" --type album
python3 dabcli.py search "Michael Jackson" --type artist
```

### ⬇️ Download

```bash
python3 dabcli.py track <track-id>
python3 dabcli.py album "Requiem"
python3 dabcli.py album buhzzhfz660ma
python3 dabcli.py library <library_id>
python3 dabcli.py discography "Michael Jackson"
```

> Supports metadata overrides for format, title, artist, album, genre, date, and path.

### ▶️ Stream

```bash
python3 dabcli.py play --track-id <id>
python3 dabcli.py play --album-id <id>
python3 dabcli.py play --library-id <id>
python3 dabcli.py play --queue <id1> <id2> <id3>
```

---

## ⚙️ Configuration

Customize default behavior in `config.json`:

```json
{
  "stream_quality": "27",
  "stream_player": "mpv",
  "output_format": "flac",
  "output_directory": "./Downloads",
  "keep_cover_file": false,
  "get_lyrics": true
}
```

### Config Options

- `output_format`: `"flac"` or `"mp3"` — format for downloaded tracks  
- `output_directory`: Directory where all downloads will be saved  
- `stream_quality`: `"27"` = FLAC, `"5"` = MP3 — controls quality of streaming/downloads  
- `stream_player`: Player used for streaming (currently only `mpv` supported)  
- `get_lyrics`: Download and embed lyrics into tracks if available  
- `keep_cover_file`: Keep a separate cover image file per track/album, or only embed it in metadata

---

## 🧩 Dependencies

- **Python 3.7+**
- Python packages: `requests`, `mutagen`, `tqdm`, `tabulate`
- External tools: `mpv` (optional, for streaming)

```bash
pip install -r requirements.txt
```

---

## 🌐 About DABMusic

DABMusic is a community-driven open-source platform providing high-quality, unrestricted music streaming and downloads.

- **Website**: [dab.yeet.su](https://dab.yeet.su) | [dabmusic.xyz](https://dabmusic.xyz)
- **Discord**: [Join the community](https://discord.gg/dabmusic-1347344910008979548)

---

## 👥 Credits

- **Developer:** [sherlockholmesat221b](https://github.com/sherlockholmesat221b)
- **superadmin0 (Creator of DABMusic)**
- **Contributors and Testers:** [joehacks](https://github.com/holmesisback), [uimaxbai](https://github.com/uimaxbai)

---

## ⚠️ Disclaimer

This software is provided **for educational and archival purposes only**.  
It does **not host or distribute music files**, nor circumvent DRM.  
Users are **responsible for complying with all applicable laws**.

---

## ⚡ How to Update?

```bash
git clone https://github.com/sherlockholmesat221b/dabcli.git
python3 dabcli.py --version
```

---