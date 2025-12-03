# Testing Airsonic MCP Server

Quick curl commands to test the server without LLM integration.

## Prerequisites

Make sure your server is running:
```bash
uvicorn main:app --reload
```

## Test Commands

### 1. Check Server Status

```bash
curl http://localhost:8000/
```

Should return server info with available endpoints.

### 2. Test MCP Discovery (List Tools)

```bash
curl -X POST http://localhost:8000/tools/list \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or with JSON-RPC format:
```bash
curl -X POST http://localhost:8000/tools/list \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

Should return list of all 8 MCP tools.

### 3. Test Search Songs Tool

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "search_songs",
    "arguments": {
      "query": "beatles"
    }
  }'
```

Or JSON-RPC format:
```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search_songs",
      "arguments": {
        "query": "beatles"
      }
    }
  }'
```

### 4. Test Get Playlists

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_playlists",
    "arguments": {}
  }'
```

### 5. Test Play a Song (replace SONG_ID with actual ID from search)

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "play_song",
    "arguments": {
      "song_id": "12345"
    }
  }'
```

### 6. Test Get Current Song

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_current_song",
    "arguments": {}
  }'
```

### 7. Test Playback Control

Pause:
```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pause_playback",
    "arguments": {}
  }'
```

Resume:
```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "resume_playback",
    "arguments": {}
  }'
```

Stop:
```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "stop_playback",
    "arguments": {}
  }'
```

### 8. Test Playback State API

```bash
curl http://localhost:8000/api/playback/state
```

### 9. Test Stream Endpoint (replace SONG_ID)

```bash
curl http://localhost:8000/stream/12345 -o test_song.mp3
```

This downloads the audio stream. Check if file is created and playable.

### 10. Test Player Page

Open in browser:
```
http://localhost:8000/player
```

Or check if it loads:
```bash
curl http://localhost:8000/player
```

## Complete Test Flow

1. **List tools:**
```bash
curl -X POST http://localhost:8000/tools/list -H "Content-Type: application/json" -d '{}'
```

2. **Search for songs:**
```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "search_songs", "arguments": {"query": "your search term"}}'
```

3. **Get playlists:**
```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_playlists", "arguments": {}}'
```

4. **Play a song (use ID from search results):**
```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "play_song", "arguments": {"song_id": "YOUR_SONG_ID"}}'
```

5. **Check current song:**
```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_current_song", "arguments": {}}'
```

6. **Get playback state:**
```bash
curl http://localhost:8000/api/playback/state
```

## Expected Responses

All tool calls should return JSON-RPC 2.0 format:
```json
{
  "jsonrpc": "2.0",
  "id": null,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Tool execution result here..."
      }
    ]
  }
}
```

If there's an error:
```json
{
  "jsonrpc": "2.0",
  "id": null,
  "error": {
    "code": -32603,
    "message": "Error message here..."
  }
}
```

## Troubleshooting

- **Connection errors**: Check `config.json` has correct Airsonic server URL
- **Authentication errors**: Verify username/password in `config.json`
- **No results**: Make sure your Airsonic server has music indexed
- **Stream errors**: Check Airsonic server is accessible and song ID is valid

