import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import pandas as pd
from ytmusicapi import YTMusic
import re
from tabulate import tabulate
import os
import shutil
import requests
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
import argparse
import concurrent.futures
import traceback
import configparser
from colorama import init, Fore, Style
from rich.progress import Progress

# Configuración del archivo donde se guardan las credenciales
CFG_FILENAME = os.path.join(os.path.expanduser("~"), ".spotify_cli.cfg")

# Inicializa colorama para Windows y otros sistemas
init(autoreset=True)

# Función para escribir errores en un archivo log
def log_error(final_path, message, enable_log=True):
    if enable_log:
        with open(os.path.join(final_path, "error.log"), "a", encoding="utf-8") as f:
            f.write(message + "\n")

# Función para ponderar el mejor match por duración y autor
def score_match(entry, desired_author, desired_duration):
    duration_diff = abs(entry.get('duration_seconds', 0) - desired_duration)
    artists = [artist['name'].lower() for artist in entry.get('artists', [])]
    author_match = 0 if desired_author.lower() in artists else 10
    return duration_diff + author_match

# Función para obtener credenciales de Spotify
def get_spotify_credentials(args):
    # 1. Si se pasan por parámetro, usar esos
    if args.client_id and args.client_secret:
        return args.client_id, args.client_secret

    # 2. Si existe archivo de configuración, leerlo
    if os.path.exists(CFG_FILENAME):
        config = configparser.ConfigParser()
        config.read(CFG_FILENAME)
        if "spotify" in config and "client_id" in config["spotify"] and "client_secret" in config["spotify"]:
            return config["spotify"]["client_id"], config["spotify"]["client_secret"]

    # 3. Pedir por consola
    print("Spotify credentials are required.")
    client_id = input("Enter your Spotify client_id: ").strip()
    client_secret = input("Enter your Spotify client_secret (input hidden): ").strip()

    # Preguntar si se quieren guardar
    save = input("Do you want to save these credentials for future use? (y/n): ").strip().lower()
    if save == "y":
        config = configparser.ConfigParser()
        config["spotify"] = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        with open(CFG_FILENAME, "w") as cfgfile:
            config.write(cfgfile)
        print(f"Credentials saved in {CFG_FILENAME}")
    return client_id, client_secret

# Función principal para procesar cada track
def process_track(track, args, ytmusic, sp, download_opts, final_path, playlist_name):
    result = {}
    track_name = track['name']
    artist_name = track['artists'][0]['name']
    duration_ms = track['duration_ms']
    seconds = int(duration_ms / 1000)
    album_name = track.get('album', {}).get('name', '')

    # Buscar la canción en YouTube Music
    search_results = ytmusic.search(track_name, filter="songs", limit=10)

    if not search_results:
        result = {
            'track_name': track_name,
            'status': "404",
            'url': ""
        }
        return result

    # Seleccionar el mejor match
    best_match = min(
        search_results,
        key=lambda e: score_match(e, artist_name, seconds)
    )

    # Expresión regular para caracteres CJK
    cjk_pattern = re.compile(
        r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]')

    status = []
    if cjk_pattern.search(best_match['title']):
        status.append("504")
    else:
        if best_match['title'].lower() != track_name.lower():
            status.append("501")
    artists = [artist['name'].lower()
               for artist in best_match.get('artists', [])]
    if artist_name.lower() not in artists:
        status.append("502")
    if abs(best_match['duration_seconds'] - seconds) > 10:
        status.append("503")
    if not status:
        status.append("200")

    video_id = best_match.get('videoId')
    url = f"https://music.youtube.com/watch?v={video_id}" if video_id else ""

    # Nombre del archivo destino
    out_file = os.path.join(final_path, f"{best_match['title']}.{args.format}")

    # Reintentar la descarga hasta 3 veces
    success = False
    download_filename = ""
    for attempt in range(3):
        try:
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                download_filename = os.path.splitext(
                    ydl.prepare_filename(info_dict))[0]
                ydl.download([url])
            success = True
            break
        except Exception as e:
            log_error(final_path, f"Download error for {track_name}, attempt {attempt+1}: {e}\n{traceback.format_exc()}", args.log)
    if not success:
        log_error(final_path, f"Failed to download {track_name} after 3 attempts.", args.log)
        result = {
            'track_name': track_name,
            'status': "404",
            'url': url
        }
        return result

    # Renombrar el archivo descargado
    try:
        original_file = os.path.join(final_path, f"{download_filename}.{args.format}")
        desired_file = os.path.join(final_path, f"{best_match['title']}.{args.format}");

        if os.path.exists(original_file):
            os.rename(original_file, desired_file)
        else:
            log_error(final_path, f"File not found to rename: {original_file}", args.log)
    except Exception as e:
        log_error(final_path, f"Error renaming file: {e}\n{traceback.format_exc()}", args.log)

    # Descargar portada y agregar metadatos (solo para mp3)
    if args.format == "mp3":
        try:
            thumb_url = best_match['thumbnails'][-1]['url']
            cover_path = os.path.join(final_path, "cover.jpg")
            r = requests.get(thumb_url, stream=True)
            if r.status_code == 200:
                with open(cover_path, 'wb') as f:
                    f.write(r.content)

            audio = MP3(desired_file, ID3=ID3)

            if audio.tags is None:
                audio.add_tags()

            audio.tags.add(TIT2(encoding=3, text=track_name))
            audio.tags.add(TPE1(encoding=3, text=artist_name))
            audio.tags.add(TALB(encoding=3, text=album_name))
            with open(cover_path, 'rb') as albumart:
                audio.tags.add(
                    APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc=u'Cover',
                        data=albumart.read()
                    )
                )
            audio.save()
            if os.path.exists(cover_path):
                os.remove(cover_path)
        except Exception as e:
            status.append("505")  # Añadir código de error de metadatos
            log_error(final_path, f"Error processing metadata for {track_name}: {e}\n{traceback.format_exc()}", args.log)

    result = {
        'track_name': track_name,
        'status': "; ".join(status),
        'url': url
    }
    return result

def main():
    parser = argparse.ArgumentParser(
        description="Download a Spotify playlist as audio files from YouTube Music."
    )
    parser.add_argument('--playlist', type=str, required=True, help="Spotify playlist URL (required)")
    parser.add_argument('--output', type=str, default=None, help="Output folder (default: Downloads/playlist_name)")
    parser.add_argument('--format', type=str, default="mp3", choices=["mp3", "flac", "wav", "m4a"], help="Audio format (default: mp3)")
    parser.add_argument('--workers', type=int, default=4, help="Number of parallel downloads (default: 4)")
    parser.add_argument('--client-id', type=str, default=None, help="Spotify client_id (optional, will prompt if not provided)")
    parser.add_argument('--client-secret', type=str, default=None, help="Spotify client_secret (optional, will prompt if not provided)")
    parser.add_argument('--log', dest='log', action='store_true', help="Generate error log file (will note genrate by default)")
    parser.add_argument('--no-report', dest='report', action='store_false', help="Do not generate report file (will generate by default)")
    parser.set_defaults(report=True, log=False)
    args = parser.parse_args()

    # Definir el directorio de descargas
    download_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    # Inicializar YTMusic en modo anónimo
    ytmusic = YTMusic()

    # Obtener credenciales de Spotify (parámetro, archivo o consola)
    client_id, client_secret = get_spotify_credentials(args)

    # Configuración del cliente de Spotify
    auth_manager = SpotifyClientCredentials(
        client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Extraer el ID de la playlist
    playlist_url = args.playlist
    playlist_id = playlist_url.split("/")[-1].split("?")[0]

    # Obtener información de la playlist
    playlist = sp.playlist(playlist_id)

    # Mostrar datos generales de la playlist con color
    print("===================================")
    print(f"Playlist name: {playlist['name']}")
    print(f"Creator: {playlist['owner']['display_name']}")
    print(f"Number of tracks: {playlist['tracks']['total']}")
    print("===================================\n")

    # Definir la ruta final de descarga
    final_path = args.output if args.output else os.path.join(download_dir, playlist['name'])

    # Verificar si la carpeta de descarga ya existe
    if os.path.exists(final_path):
        response = input(
            Fore.YELLOW + f"The folder '{final_path}' already exists. Do you want to replace it? (y/n): " + Style.RESET_ALL)
        if response.lower() == 'y':
            shutil.rmtree(final_path)
            os.makedirs(final_path)
            print(Fore.GREEN + f"Folder '{final_path}' replaced.")
        else:
            print(Fore.YELLOW + f"The existing folder will be kept: {final_path}")
    else:
        os.makedirs(final_path)
        print(Fore.GREEN + f"Folder '{final_path}' created.")

    # Controlar paginación para obtener todas las canciones
    limit = 100
    offset = 0
    total_tracks = playlist['tracks']['total']

    # Opciones de yt_dlp para la descarga
    download_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(final_path, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': args.format,
            'preferredquality': '320',
        }],
        'quiet': True,
        'no_warnings': True
    }

    # Obtener todos los tracks de la playlist
    all_tracks = []
    while offset < total_tracks:
        results_spotify = sp.playlist_items(playlist_id, offset=offset, limit=limit)
        all_tracks.extend([item['track']
                          for item in results_spotify['items'] if item['track']])
        offset += limit

    # Descarga en paralelo usando ThreadPoolExecutor
    results = []
    with Progress() as progress:
        task = progress.add_task("[cyan]Processing tracks...", total=len(all_tracks))
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(process_track, track, args, ytmusic, sp, download_opts, final_path, playlist['name'])
                for track in all_tracks
            ]
            for f in concurrent.futures.as_completed(futures):
                try:
                    result = f.result()
                    results.append(result)
                except Exception as e:
                    log_error(final_path, f"Unexpected error: {e}\n{traceback.format_exc()}", args.log)
                progress.update(task, advance=1)

    # Crear DataFrame y tabla de resultados
    df = pd.DataFrame(results)

    legend = """
Status codes:
200: Match OK
501: Title does not match
502: Author does not match
503: Duration differs (more than 10s difference)
504: Title omitted due to Chinese, Japanese, or Korean characters
505: Metadata error (cover or tags)
404: Song not found
"""

    table = tabulate(df, headers="keys", tablefmt="grid",
                     colalign=("left", "left", "left"))

    report_path = os.path.join(final_path, 'report.txt')
    error_log_path = os.path.join(final_path, 'error.log')

    # Guardar el reporte si corresponde
    if args.report:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(legend + "\n\n" + table)

    # Mostrar mensajes finales según los flags
    print(Fore.CYAN + "\n" + "="*50)
    print(Fore.GREEN + "Process completed successfully!")
    print(Fore.CYAN + "-"*50)
    if args.report:
        print(Fore.WHITE + "Report available at: " + Fore.YELLOW + f"{report_path}")
    else:
        print(Fore.WHITE + "Report file was not generated (--no-report).")
    if args.log:
        if os.path.exists(error_log_path) and os.path.getsize(error_log_path) > 0:
            print(Fore.WHITE + "Error log (if any): " + Fore.RED + f"{error_log_path}")
        else:
            print(Fore.WHITE + "No errors were logged.")
    print(Fore.CYAN + "="*50 + "\n")


if __name__ == "__main__":
    main()
