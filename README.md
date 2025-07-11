# 🎧 DABMusic CLI
**DABMusic CLI** is an advanced, extensible, and user-friendly command-line tool for accessing [DABMusic](https://dab.yeet.su) — a free and open-source digital music library and streaming service.  
It supports searching, downloading, metadata tagging, playlist creation, and local streaming — all via the terminal.

---

## 🚀 Features

- Download full albums, tracks, and library playlists
- Stream tracks directly via `mpv`
- Automatic metadata tagging
- Embedded cover art support
- Smart filename generation
- Playlist generation in `.m3u8` format
- Configurable output format (MP3, FLAC)
- Login/logout with token management

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone [https://github.com/yourusername/dabcli.git](https://github.com/sherlockholmesat221b/dabcli)
cd dabcli
```

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

### 🔐 Log In

```bash
python3 dabcli.py login you@example.com yourpassword
```

### 🔓 Log Out

```bash
python3 dabcli.py logout
```

> Removes token and credentials from config.

---

### 🔍 Search

Search for tracks or albums:

```bash
python3 dabcli.py search "Mozart"
```
```bash
python3 dabcli.py search "Mozart" --type album
```

---

### ⬇️ Download

#### Download a Track

```bash
python3 dabcli.py download --track-id 123456789 --format mp3
```

#### Download an Album

```bash
python3 dabcli.py album "Requiem"
```

#### Download a Library Playlist

```bash
python3 dabcli.py library <library_id>
```

---

### ▶️ Stream

Stream a track, album, or playlist:

```bash
python3 dabcli.py play --track-id <id>
python3 dabcli.py play --album-id <id>
python3 dabcli.py play --library-id <id>
```

---

## ⚙️ Configuration

Customize default behavior in `config.json`:

```json
{
  "output_format": "flac",
  "output_directory": "./downloads",
  "use_metadata_tagging": true,
  "stream_quality": "27",
  "stream_player": "mpv",
  "delete_raw_files": true,
  "keep_cover_file": false
}
```

### Config Options

- `output_format`: `"flac"` or `"mp3"`
- `output_directory`: Directory where files will be saved
- `stream_quality`: `27 = FLAC`, `5 = MP3`
- `use_metadata_tagging`: Automatically tag tracks
- `stream_player`: Player used for streaming (e.g., `mpv`)
- `delete_raw_files`: Remove original files after conversion
- `keep_cover_file`: Keep or delete embedded cover images

---

## 🧩 Dependencies

- **Python 3.7+**
- Python packages:
    - `requests`
    - `mutagen`
    - `tqdm`
    - `tabulate`
- External tools:
    - `ffmpeg` (required)
    - `mpv` (optional, for streaming)
    - `nano` (optional, for editing config)

### Install with:

```bash
pip install -r requirements.txt
```

---

## 🌐 About DABMusic

DABMusic is a community-driven open-source platform that provides unrestricted, high-quality music streaming and downloads.

- **Website**: [dab.yeet.su](https://dab.yeet.su) | [dabmusic.xyz](https://dabmusic.xyz)
- **Discord**: [Join the community](https://discord.gg/dabmusic-1347344910008979548)

---

## 👥 Credits

- **Developer**: [sherlockholmesat221b](https://github.com/sherlockholmesat221b)
- superadmin0 : Creator, DABMusic
