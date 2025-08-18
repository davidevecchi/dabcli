# What's New in DAB CLI 2.0?
## 🚀 Smarter Downloads
- Skips existing files automatically.
- Pause, resume, or safely stop downloads mid-way.
- Full metadata and path overrides supported for tracks, albums, artist discographies, and libraries.
- Download individual tracks with dabcli.py track <track-id> — clean, reliable, and fully tagged.

## 🎵 Artist Discography Download 
- Sort by year, title, or popularity. [#3](https://github.com/sherlockholmesat221b/dabcli/issues/3)  
- Download all albums of an artist by name or ID.
- Limit downloads if needed, or fetch everything.
- Works seamlessly with metadata overrides.

## 🎧 MPV IPC Player
- Stream tracks, albums, libraries, or custom queues.
- Terminal-based now playing info, timers, and live updates.
- Play/pause, next, previous, and quit controls with space/arrow/q keys.
- No separate windows — works entirely in your terminal.
- Supports high-quality streaming, with metadata display for each track.

## 🖼️ Cover Art & Lyrics
- Downloads and embeds track covers and album covers correctly.
- Cover naming standardized: track covers {filename}.jpg, album covers cover.jpg.
- Full support for libraries and album downloads.
- Lyrics automatically downloaded and embedded (if available).


## 🔧 Updates & Version Check
- `dabcli.py --version` compares local version with GitHub to ensure you’re up-to-date.
- `dabcli.py update` updates to the latest version from GitHub instantly.

## 📝 Cleaner, More Intuitive CLI
- New help system with detailed subcommand instructions.
- Old redundant arguments removed.
- Improved output formatting across all commands.

## 🐛 Bug Fixes
- Album GET errors fixed.[#2](https://github.com/sherlockholmesat221b/dabcli/issues/2)  
- Cover download logic corrected for tracks, albums, and libraries.
- Removed converter.py — format conversion rolled back for simplicity.
- Multiple artist selection logic fixed in discography downloads.

## ⚡ How to Update?
1. Visit the [DAB CLI GitHub repository](https://github.com/sherlockholmesat221b/dabcli).
2. Download the latest release or clone the repository:
```
git clone https://github.com/sherlockholmesat221b/dabcli.git
```
3. Replace your existing files with the new version.
4. Verify the update:
```
dabcli.py --version
```
Update now and experience faster downloads, full discographies, live streaming with MPV IPC, and cleaner, smarter CLI handling!
