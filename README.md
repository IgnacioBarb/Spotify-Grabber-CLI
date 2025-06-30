# spotify2ytmusic-cli

A command-line tool to download Spotify playlists as audio files from YouTube Music, with metadata and cover art.

## Features

- Download all tracks from a Spotify playlist using YouTube Music as source
- Supports mp3, flac, wav, m4a formats
- Adds metadata and cover art (for mp3)
- Parallel downloads for speed
- Custom output folder
- Error logging and customizable report generation

## Usage

```sh
python main.py --playlist "SPOTIFY_PLAYLIST_URL" [--output FOLDER] [--format mp3] [--workers 4] [--log] [--no-report]
```

### Example

```sh
python main.py --playlist "https://open.spotify.com/playlist/..." --format mp3 --workers 8 --log
```

## Requirements

- Python 3.8+
- yt-dlp
- spotipy
- ytmusicapi
- pandas
- tabulate
- mutagen
- requests
- colorama
- rich

Install dependencies:

```sh
pip install -r requirements.txt
```

## License

MIT License