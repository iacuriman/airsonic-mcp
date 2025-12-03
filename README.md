# Airsonic MCP 🎵

A complete MCP (Model Context Protocol) server that integrates with Airsonic music server, allowing LLMs to control music playback through natural language.

## Features

- ✅ **Full MCP Protocol** - JSON-RPC 2.0 compliant, works with Groq and other MCP clients
- ✅ **Real Airsonic Integration** - Actual API calls to your Airsonic server (no mocks)
- ✅ **Web Audio Player** - HTML5 player accessible via browser
- ✅ **LLM Control** - Search, play, pause, and control music via natural language
- ✅ **Production Ready** - Clean, modular architecture

## Quick Start

### 1. Configure Airsonic Server

Edit `config.json` with your Airsonic server details:

```json
{
  "airsonic": {
    "server_url": "http://localhost:4040",
    "username": "your_username",
    "password": "your_password",
    "api_version": "1.16.0"
  }
}
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the MCP Server

```bash
uvicorn main:app --reload
```

✅ Server running at `http://localhost:8000`

### 4. Access the Web Player

Open your browser and go to:
```
http://localhost:8000/player
```

### 5. Connect to Groq (Optional)

1. Expose your server with Cloudflare Tunnel:
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```

2. Add MCP server in Groq Console:
   - Server URL: `https://your-cloudflare-url.trycloudflare.com`
   - Ask: "Search for songs by The Beatles" or "Play my favorite playlist"

## Available MCP Tools

The LLM can use these tools to control music:

- **search_songs(query)** - Search for songs in your library
- **play_song(song_id)** - Play a specific song
- **pause_playback()** - Pause current playback
- **resume_playback()** - Resume paused playback
- **stop_playback()** - Stop current playback
- **get_current_song()** - Get currently playing song info
- **get_playlists()** - List all playlists
- **play_playlist(playlist_id)** - Play a playlist

## Architecture

```
LLM (Groq) → MCP Server → Airsonic API → Music Library
                    ↓
              Web Player (Browser)
```

## API Endpoints

- `GET /` - Server info
- `POST /initialize` - MCP initialization
- `POST /tools/list` - List available tools
- `POST /tools/call` - Execute a tool
- `GET /player` - Web audio player interface
- `GET /stream/{song_id}` - Stream audio from Airsonic
- `GET /api/playback/state` - Get current playback state
- `POST /api/playback/control` - Control playback (pause/resume/stop)

## Requirements

- Python 3.9+
- Airsonic server running and accessible
- FastAPI, uvicorn, requests, pydantic

## Troubleshooting

### Airsonic Connection Issues

- Verify `config.json` has correct server URL and credentials
- Test Airsonic API directly: `curl "http://your-server:4040/rest/ping.view?u=user&p=pass&v=1.16.0&c=mcp"`
- Check Airsonic server logs for authentication errors

### Playback Not Working

- Ensure Airsonic server is accessible from MCP server
- Check that song IDs are valid (use search_songs to find IDs)
- Verify stream endpoint is accessible: `http://localhost:8000/stream/{song_id}`

### Web Player Issues

- Open browser console for error messages
- Check that `/api/playback/state` endpoint returns valid JSON
- Ensure audio player has proper CORS headers if accessing remotely

## Example Usage

### Via LLM (Groq)

```
User: "Search for songs by Pink Floyd"
LLM: [calls search_songs("Pink Floyd")]
Response: "Found 15 songs: 1. Comfortably Numb (ID: 1234)..."

User: "Play Comfortably Numb"
LLM: [calls play_song("1234")]
Response: "Now playing: Comfortably Numb by Pink Floyd..."
```

### Via Web Player

1. Open `http://localhost:8000/player`
2. Search for songs
3. Use play/pause/stop controls
4. Player auto-updates when LLM changes playback

## License

Open source - feel free to use and modify!

---

**Ready to control music with AI?** Follow the quick start above! 🎶

