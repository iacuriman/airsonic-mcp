# Quick Start - Airsonic MCP with Groq

## 1. Start MCP Server
```bash
cd airsonic-mcp
uvicorn main:app --reload
```

## 2. Expose with Cloudflare Tunnel (new terminal)
```bash
cloudflared tunnel --url http://localhost:8000
```
Copy the public URL (e.g., `https://abc123.trycloudflare.com`)

## 3. Add to Groq Console
1. Go to [Groq Playground](https://console.groq.com/playground)
2. Click **"+ Add MCP Server"**
3. Fill in:
   - **Server Name**: `Airsonic MCP`
   - **Server URL**: `[your-cloudflare-url]` (no /mcp needed)
4. Select model with **FUNCTION CALLING / TOOL USE** support

## 4. Test Commands
Ask Groq:
- "Search for songs by Pink Floyd"
- "Play song ID 2"
- "Get random songs from my library"
- "List my playlists"

## 5. Test Direct (optional)
```bash
# List tools
curl -X POST http://localhost:8000/tools/list -H "Content-Type: application/json" -d '{}'

# Get random songs
curl -X POST http://localhost:8000/tools/call -H "Content-Type: application/json" -d '{"name": "get_random_songs", "arguments": {"count": 10}}'
```

