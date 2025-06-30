# spotify2ytmusic-cli

A command-line tool to download Spotify playlists as audio files from YouTube Music, with metadata and cover art.

## Features

- Download all tracks from a Spotify playlist using YouTube Music as the source
- Supports mp3, flac, wav, and m4a formats
- Adds metadata and cover art (for mp3)
- Parallel downloads for speed
- Custom output folder
- Error logging and customizable report generation

## Installation

### System Requirements

- Python 3.8 or higher
- **FFmpeg** (required by yt-dlp to extract audio)
  - Debian/Ubuntu:
    ```bash
    sudo apt install ffmpeg
    ```
  - macOS (Homebrew):
    ```bash
    brew install ffmpeg
    ```
  - Windows:
    - Download from https://ffmpeg.org/download.html and add it to your PATH
    - For an easy way to install FFmpeg, I recommend checking out [Gyan.dev FFmpeg builds](https://www.gyan.dev/ffmpeg/builds/):
### Python dependencies

Install the required Python packages with:
```bash
pip install -r requirements.txt
```
If you do not have a `requirements.txt`, you can create one with this content:

```
yt-dlp
spotipy
ytmusicapi
pandas
tabulate
mutagen
requests
colorama
rich
```

### Spotify Credentials

You will need **Spotify API credentials** (client ID and client secret).  
You can get them by registering an app at the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).

The first time you run the script, it will prompt you to enter these credentials, and optionally store them in:

    ~/.spotify_cli.cfg

## Usage

```bash
python main.py --playlist "SPOTIFY_PLAYLIST_URL" [--output FOLDER] [--format mp3] [--workers 4] [--log] [--no-report]
```

### Example

```bash
python main.py --playlist "https://open.spotify.com/playlist/..." --format mp3 --workers 8 --log
```

## License

MIT License