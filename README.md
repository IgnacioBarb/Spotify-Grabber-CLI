# Spotify Grabber CLI

**Spotify Grabber CLI** is a Python command-line utility that downloads entire Spotify playlists as local audio files (mp3, flac, wav, or m4a) with complete metadata and cover art.
It leverages the Spotify API for playlist parsing and YouTube Music as the audio source, supports parallel downloads, customizable output directories, error logging, and detailed reporting.
Requires Spotify API credentials and FFmpeg

## Features

- Download all tracks from a Spotify playlist using YouTube Music as the source
- Supports mp3, flac, wav, and m4a formats
- Adds metadata and cover art (for mp3)
- Parallel downloads for speed
- Custom output folder
- Error logging and customizable report generation

## Installation

### Clone the repository

```bash
git clone https://github.com/IgnacioBarb/Spotify-Grabber-CLI.git
cd Spotify-Grabber-CLI
```

### (Recommended) Create and activate a virtual environment

```bash
python -m venv env
# On Windows:
env\Scripts\activate
# On macOS/Linux:
source env/bin/activate
```

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
    - For an easy way to install FFmpeg, I recommend checking out [Gyan.dev FFmpeg builds](https://www.gyan.dev/ffmpeg/builds/)

### Python dependencies

Install the required Python packages with:
```bash
pip install -r requirements.txt
```

### Spotify Credentials

You will need **Spotify API credentials** (client ID and client secret).  
You can get them by registering an app at the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).

The first time you run the script, it will prompt you to enter these credentials, and optionally store them in:

    ~/.spotify_cli.cfg

## Usage

For all available options and flags, run:

```bash
python spotify_grabber_cli.py --help
```

Example usage:

```bash
python spotify_grabber_cli.py --playlist "SPOTIFY_PLAYLIST_URL" [--output FOLDER] [--format mp3] [--workers 4] [--log] [--no-report]
```

### Example

```bash
python spotify_grabber_cli.py --playlist "https://open.spotify.com/playlist/..." --format mp3 --workers 8 --log
```

## License

MIT License