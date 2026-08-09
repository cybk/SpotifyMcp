# Spotify MCP — comandos básicos

Servidor MCP en Python que permite controlar Spotify desde Claude (u otro
cliente MCP): reproducir, pausar, saltar canciones, cambiar volumen y buscar
canciones/artistas.

> ⚠️ El control de reproducción (play, pause, next, previous, volumen)
> requiere **Spotify Premium**. La búsqueda funciona con cualquier cuenta.

## 1. Crear una app en Spotify

1. Ve a https://developer.spotify.com/dashboard e inicia sesión.
2. Clic en **Create app**.
3. Ponle un nombre (ej. "MCP básico") y una descripción cualquiera.
4. En **Redirect URI** agrega exactamente:
   `http://127.0.0.1:8080/callback`
5. Guarda. Copia el **Client ID** y el **Client Secret** (Settings → View
   client secret).

## 2. Instalar dependencias

```bash
cd spotify-mcp
python -m venv venv
source venv/bin/activate   # en Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` y pega tu `SPOTIFY_CLIENT_ID` y `SPOTIFY_CLIENT_SECRET`.

## 4. Probar el servidor localmente (opcional)

```bash
mcp dev server.py
```

Esto abre el MCP Inspector en el navegador para probar cada herramienta sin
necesidad de conectarlo a Claude todavía. La primera vez que uses una
herramienta que requiera datos de tu cuenta, se abrirá el navegador pidiendo
que autorices la app — es normal, solo pasa una vez (el token se guarda en
`.spotify_token_cache`).

## 5. Conectarlo a Claude Desktop

Edita tu archivo de configuración de Claude Desktop:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Y agrega (ajustando la ruta absoluta a tu proyecto):

```json
{
  "mcpServers": {
    "spotify": {
      "command": "/ruta/absoluta/a/spotify-mcp/venv/bin/python",
      "args": ["/ruta/absoluta/a/spotify-mcp/server.py"]
    }
  }
}
```

En Windows, `command` normalmente sería algo como
`C:\\ruta\\a\\spotify-mcp\\venv\\Scripts\\python.exe`.

Reinicia Claude Desktop. Deberías ver el servidor "spotify" y sus
herramientas disponibles.

## Herramientas disponibles

| Herramienta | Qué hace |
|---|---|
| `spotify_play(query="")` | Reanuda reproducción, o busca y reproduce si le das un texto |
| `spotify_pause()` | Pausa |
| `spotify_next()` | Siguiente canción |
| `spotify_previous()` | Canción anterior |
| `spotify_set_volume(volume)` | Cambia volumen (0-100) |
| `spotify_search(query, search_type, limit)` | Busca canciones, artistas o playlists sin reproducir |
| `spotify_play_playlist(query)` | Busca una playlist por nombre y la reproduce |
| `spotify_now_playing()` | Muestra qué se está reproduciendo |
| `spotify_list_devices()` | Lista dispositivos con Spotify abierto y cuál está activo |
| `spotify_transfer_playback(device_name, start_playing)` | Cambia a qué dispositivo se manda la reproducción |

## Notas

- Necesitas tener Spotify **abierto y activo** en algún dispositivo (celular,
  computadora, parlante) para que los comandos de reproducción funcionen —
  la API necesita un "dispositivo activo" al cual mandar el comando.
- Si mueves el proyecto de carpeta, borra `.spotify_token_cache` y vuelve a
  autorizar, o actualiza `SPOTIFY_CACHE_PATH`.
- No subas tu archivo `.env` ni `.spotify_token_cache` a ningún repositorio
  público — contienen credenciales.
