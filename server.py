"""
Servidor MCP para controlar Spotify con comandos básicos.

Herramientas expuestas:
- spotify_play        -> reanudar reproducción, o buscar y reproducir algo específico
- spotify_pause       -> pausar
- spotify_next         -> siguiente canción
- spotify_previous     -> canción anterior
- spotify_set_volume   -> cambiar volumen (0-100)
- spotify_search       -> buscar canciones, artistas o playlists
- spotify_play_playlist -> buscar una playlist por nombre y reproducirla
- spotify_now_playing  -> ver qué se está reproduciendo actualmente
- spotify_list_devices     -> listar dispositivos con Spotify abierto
- spotify_transfer_playback -> cambiar a qué dispositivo se manda la reproducción

Requiere una app registrada en https://developer.spotify.com/dashboard
y una cuenta Spotify Premium (el control de reproducción no funciona con
cuentas gratuitas).
"""

import os
from typing import Literal

import spotipy
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

# Scopes necesarios para leer y controlar la reproducción
SCOPES = " ".join(
    [
        "user-read-playback-state",
        "user-modify-playback-state",
        "user-read-currently-playing",
    ]
)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8080/callback")
CACHE_PATH = os.getenv("SPOTIFY_CACHE_PATH", ".spotify_token_cache")


def get_spotify_client() -> spotipy.Spotify:
    """Crea el cliente de Spotify autenticado.

    La primera vez abrirá el navegador para que autorices la app; después
    reutiliza el token guardado en CACHE_PATH.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        raise RuntimeError(
            "Faltan SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET. "
            "Revisa el archivo .env (ver .env.example)."
        )

    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
        cache_path=CACHE_PATH,
        open_browser=True,
    )
    return spotipy.Spotify(auth_manager=auth_manager)


mcp = FastMCP("spotify-mcp")


def _no_active_device_message() -> str:
    return (
        "No encontré ningún dispositivo Spotify activo. Abre Spotify en tu "
        "teléfono, computadora o parlante y dale play a algo (o pausa) para "
        "que aparezca como dispositivo activo, luego intenta de nuevo."
    )


@mcp.tool()
def spotify_play(query: str = "") -> str:
    """Reproduce música en Spotify.

    Si se deja 'query' vacío, reanuda la reproducción en pausa.
    Si se da un texto (nombre de canción, artista o álbum), lo busca y
    reproduce el primer resultado.
    """
    sp = get_spotify_client()

    try:
        if query.strip():
            results = sp.search(q=query, type="track", limit=1)
            items = results.get("tracks", {}).get("items", [])
            if not items:
                return f"No encontré ningún resultado para '{query}'."
            track = items[0]
            sp.start_playback(uris=[track["uri"]])
            artists = ", ".join(a["name"] for a in track["artists"])
            return f"Reproduciendo '{track['name']}' de {artists}."
        else:
            sp.start_playback()
            return "Reproducción reanudada."
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            return _no_active_device_message()
        return f"Error de Spotify: {e}"


@mcp.tool()
def spotify_pause() -> str:
    """Pausa la reproducción actual en Spotify."""
    sp = get_spotify_client()
    try:
        sp.pause_playback()
        return "Reproducción pausada."
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            return _no_active_device_message()
        return f"Error de Spotify: {e}"


@mcp.tool()
def spotify_next() -> str:
    """Salta a la siguiente canción."""
    sp = get_spotify_client()
    try:
        sp.next_track()
        return "Saltando a la siguiente canción."
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            return _no_active_device_message()
        return f"Error de Spotify: {e}"


@mcp.tool()
def spotify_previous() -> str:
    """Regresa a la canción anterior."""
    sp = get_spotify_client()
    try:
        sp.previous_track()
        return "Regresando a la canción anterior."
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            return _no_active_device_message()
        return f"Error de Spotify: {e}"


@mcp.tool()
def spotify_set_volume(volume: int) -> str:
    """Cambia el volumen de reproducción.

    Args:
        volume: nivel de volumen de 0 a 100.
    """
    if not 0 <= volume <= 100:
        return "El volumen debe estar entre 0 y 100."

    sp = get_spotify_client()
    try:
        sp.volume(volume)
        return f"Volumen ajustado a {volume}%."
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            return _no_active_device_message()
        return f"Error de Spotify: {e}"


@mcp.tool()
def spotify_search(
    query: str,
    search_type: Literal["track", "artist", "playlist"] = "track",
    limit: int = 5,
) -> str:
    """Busca canciones, artistas o playlists en Spotify sin reproducirlos.

    Args:
        query: texto a buscar (nombre de canción, artista, playlist, etc.)
        search_type: 'track' para canciones, 'artist' para artistas o
            'playlist' para playlists.
        limit: número máximo de resultados (1-20).
    """
    limit = max(1, min(limit, 20))
    sp = get_spotify_client()

    results = sp.search(q=query, type=search_type, limit=limit)

    if search_type == "track":
        items = results.get("tracks", {}).get("items", [])
        if not items:
            return f"No encontré canciones para '{query}'."
        lines = []
        for i, t in enumerate(items, 1):
            artists = ", ".join(a["name"] for a in t["artists"])
            lines.append(f"{i}. {t['name']} — {artists} ({t['album']['name']})")
        return "\n".join(lines)

    if search_type == "artist":
        items = results.get("artists", {}).get("items", [])
        if not items:
            return f"No encontré artistas para '{query}'."
        lines = []
        for i, a in enumerate(items, 1):
            genres = ", ".join(a.get("genres", [])[:3]) or "sin género listado"
            lines.append(
                f"{i}. {a['name']} — {genres} — {a['followers']['total']:,} seguidores"
            )
        return "\n".join(lines)

    # search_type == "playlist"
    items = [p for p in results.get("playlists", {}).get("items", []) if p]
    if not items:
        return f"No encontré playlists para '{query}'."
    lines = []
    for i, p in enumerate(items, 1):
        owner = p.get("owner", {}).get("display_name", "desconocido")
        track_count = p.get("tracks", {}).get("total", "?")
        lines.append(
            f"{i}. {p['name']} — por {owner} — {track_count} canciones "
            f"(id: {p['id']})"
        )
    return "\n".join(lines)


@mcp.tool()
def spotify_play_playlist(query: str) -> str:
    """Busca una playlist por nombre y la reproduce (primer resultado).

    Args:
        query: nombre de la playlist a buscar y reproducir.
    """
    sp = get_spotify_client()
    try:
        results = sp.search(q=query, type="playlist", limit=1)
        items = [p for p in results.get("playlists", {}).get("items", []) if p]
        if not items:
            return f"No encontré ninguna playlist para '{query}'."
        playlist = items[0]
        sp.start_playback(context_uri=playlist["uri"])
        owner = playlist.get("owner", {}).get("display_name", "desconocido")
        return f"Reproduciendo la playlist '{playlist['name']}' de {owner}."
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            return _no_active_device_message()
        return f"Error de Spotify: {e}"


@mcp.tool()
def spotify_list_devices() -> str:
    """Lista los dispositivos con Spotify abierto disponibles para reproducir,
    indicando cuál está activo actualmente."""
    sp = get_spotify_client()
    devices = sp.devices().get("devices", [])

    if not devices:
        return (
            "No encontré ningún dispositivo con Spotify abierto. Abre la app "
            "en tu celular, computadora o bocina, y dale play/pausa una vez "
            "para que se registre."
        )

    lines = []
    for d in devices:
        marca = " (activo)" if d.get("is_active") else ""
        lines.append(
            f"- {d['name']} — {d['type']}{marca} — volumen: {d.get('volume_percent', '?')}%"
        )
    return "\n".join(lines)


@mcp.tool()
def spotify_transfer_playback(device_name: str, start_playing: bool = False) -> str:
    """Transfiere la reproducción a otro dispositivo por nombre (o parte del nombre).

    Args:
        device_name: nombre (o parte del nombre) del dispositivo al que quieres
            cambiar, tal como aparece en spotify_list_devices(). Ej. "laptop",
            "iPhone de Juan".
        start_playing: si True, empieza a reproducir de inmediato en el nuevo
            dispositivo. Si False, solo transfiere el control sin reproducir.
    """
    sp = get_spotify_client()
    devices = sp.devices().get("devices", [])

    if not devices:
        return (
            "No encontré ningún dispositivo con Spotify abierto. Abre la app "
            "en el dispositivo al que quieres cambiar y dale play/pausa una vez."
        )

    query = device_name.strip().lower()
    match = next((d for d in devices if query in d["name"].lower()), None)

    if not match:
        nombres = ", ".join(d["name"] for d in devices)
        return (
            f"No encontré ningún dispositivo que coincida con '{device_name}'. "
            f"Dispositivos disponibles: {nombres}."
        )

    sp.transfer_playback(device_id=match["id"], force_play=start_playing)
    accion = "y reproduciendo" if start_playing else "sin reproducir todavía"
    return f"Reproducción transferida a '{match['name']}' ({accion})."


@mcp.tool()
def spotify_now_playing() -> str:
    """Muestra qué canción se está reproduciendo actualmente."""
    sp = get_spotify_client()
    playback = sp.current_playback()

    if not playback or not playback.get("item"):
        return "No hay nada reproduciéndose ahora mismo."

    item = playback["item"]
    artists = ", ".join(a["name"] for a in item["artists"])
    state = "reproduciendo" if playback.get("is_playing") else "pausado"
    progress_ms = playback.get("progress_ms", 0)
    duration_ms = item.get("duration_ms", 0)
    progress_min = progress_ms // 60000
    progress_sec = (progress_ms // 1000) % 60
    duration_min = duration_ms // 60000
    duration_sec = (duration_ms // 1000) % 60

    return (
        f"{item['name']} — {artists} ({state})\n"
        f"{progress_min}:{progress_sec:02d} / {duration_min}:{duration_sec:02d}"
    )


if __name__ == "__main__":
    mcp.run()
