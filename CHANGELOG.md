# Changelog

All notable changes to this project will be documented here.

## [1.0.1] - 2025-07-14

### Changed
- Updated API in accordance to what his majesty `superadmin0` advised.
- Unified login failure handling across all modules
- Removed repetitive login prompts and fallback messages
- Eliminated emoji from CLI output for a cleaner terminal experience

### Fixed
- CLI no longer crashes when token/email/password is missing
- Graceful error output when not logged in
- API calls now avoided when not authenticated

---
## [2.0.0] - 2025-08-  

### Changed
- **Smarter Downloader**: Skips already downloaded files and supports pause/resume or stop functionality.  
- **Artist Discography Download**: Added a command to download an entire artist’s discography using either `artistId` or artist name. [#3](https://github.com/sherlockholmesat221b/dabcli/issues/3)  
- **Improved Player**: Player now uses MPV IPC for better functionality and a cleaner UI.  
- **One-line Update & Version Check**: Easily update DAB CLI and check the latest version online.  
- **Lyrics Support**: Downloads and embeds lyrics into tracks automatically.  
- **Simplified Commands**: Removed redundant arguments; tracks are now downloaded using `dabcli.py track <track-id>`.  
- **Metadata & Path Overrides**: Added support for overriding metadata and download paths in `album`, `discography`, and `library` commands.  

### Fixed
- **Album GET Error**: Fixed issues with fetching albums. [#2](https://github.com/sherlockholmesat221b/dabcli/issues/2)  
- **Cover Image Logic**: Tracks, albums, and libraries now download covers correctly:  
  - For individual tracks and libraries: cover image is `{filename}.jpg` and downloaded per track.  
  - For albums: cover image is `cover.jpg`, downloaded once to avoid redundancy.  
- **Removed Converter**: `converter.py` has been removed; format conversion was rolled back.  


---
## [2.1.0] - 2025-08-23

### Changed
- **Universal Controls**: Replaced Unix-only signal handling with a cross-platform keyboard listener.
- **Pause/Resume & Stop**: Downloads can now be paused/resumed with **`p`** and stopped with **`q`** on all platforms.
- **Progress Refresh**: Progress bar refreshes correctly when resuming a paused download.

### Fixed
- **Windows Compatibility**: Removed reliance on `SIGTSTP` and `signal.pause` which caused crashes on Windows.
- **Cross-Platform Behavior**: Unified the control scheme for Linux, macOS, and Windows.


---
