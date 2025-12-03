from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import json
import requests

from models import ModelContextRequest, ModelContextResponse
from toolAirsonic import (
    ALL_TOOLS,
    search_songs,
    list_songs,
    list_albums,
    get_random_songs,
    play_song,
    pause_playback,
    resume_playback,
    stop_playback,
    seek_to,
    set_volume,
    mute,
    unmute,
    get_current_song,
    get_playlists,
    play_playlist,
    playback_state,
    load_config,
    get_airsonic_auth_params
)

app = FastAPI()

# Mount static files from theme folder
app.mount("/theme", StaticFiles(directory="theme"), name="theme")

# Tool registry mapping function names to functions
tool_registry = {
    "search_songs": search_songs,
    "list_songs": list_songs,
    "list_albums": list_albums,
    "get_random_songs": get_random_songs,
    "play_song": play_song,
    "pause_playback": pause_playback,
    "resume_playback": resume_playback,
    "stop_playback": stop_playback,
    "seek_to": seek_to,
    "set_volume": set_volume,
    "mute": mute,
    "unmute": unmute,
    "get_current_song": get_current_song,
    "get_playlists": get_playlists,
    "play_playlist": play_playlist,
}

# Root endpoint - handle initial connection/discovery
@app.get("/")
async def root():
    """Root endpoint - returns server info"""
    return {
        "name": "airsonic-mcp",
        "version": "1.0.0",
        "protocol": "mcp",
        "endpoints": {
            "initialize": "/initialize",
            "tools/list": "/tools/list",
            "tools/call": "/tools/call",
            "player": "/player",
            "stream": "/stream/{song_id}"
        }
    }

@app.post("/")
async def root_post(request: Request):
    """Handle POST to root - might be MCP discovery or JSON-RPC calls"""
    try:
        body = await request.json()
        method = body.get("method")
        
        # Route JSON-RPC requests to appropriate handlers
        if method == "initialize":
            return await mcp_initialize(request)
        elif method == "tools/list":
            return await mcp_tools_list(request)
        elif method == "tools/call":
            return await mcp_tools_call(request)
    except:
        pass
    # Return server info
    return await root()

# MCP Protocol endpoints - JSON-RPC 2.0 format
@app.post("/initialize")
@app.get("/initialize")
async def mcp_initialize(request: Request):
    """MCP initialize endpoint - JSON-RPC 2.0 format"""
    request_id = None
    try:
        body = await request.json()
        request_id = body.get("id") if "id" in body else None
        # Handle JSON-RPC 2.0 format
        if "method" in body and body["method"] == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "airsonic-mcp",
                        "version": "1.0.0"
                    }
                }
            }
            return JSONResponse(content=response)
    except:
        pass
    
    # Always return JSON-RPC 2.0 format for Groq compatibility
    response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "airsonic-mcp",
                "version": "1.0.0"
            }
        }
    }
    return JSONResponse(content=response)

@app.post("/tools/list")
async def mcp_tools_list(request: Request):
    """List available tools - MCP protocol JSON-RPC 2.0"""
    request_id = None
    try:
        body = await request.json()
        request_id = body.get("id") if "id" in body else None
    except:
        pass
    
    # Build tools list from ALL_TOOLS
    tools = [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    param.name: {"type": param.type}
                    for param in tool.parameters
                },
                "required": [param.name for param in tool.parameters]
            }
        }
        for tool in ALL_TOOLS
    ]
    
    # Always return JSON-RPC 2.0 format for Groq compatibility
    response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "tools": tools
        }
    }
    return JSONResponse(content=response)

@app.post("/tools/call")
async def mcp_tools_call(request: Request):
    """Call a tool - MCP protocol JSON-RPC 2.0"""
    try:
        body = await request.json()
        request_id = body.get("id") if "id" in body else None
        
        # Handle JSON-RPC 2.0 format
        if "method" in body and body["method"] == "tools/call":
            params = body.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
        else:
            # Direct format
            tool_name = body.get("name")
            arguments = body.get("arguments", {})
        
        if tool_name not in tool_registry:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Tool {tool_name} not found"
                }
            }
        
        try:
            tool_function = tool_registry[tool_name]
            
            # Filter out empty string arguments (Groq sometimes sends empty strings)
            filtered_arguments = {k: v for k, v in arguments.items() if v != "" and v is not None}
            
            # Get function signature to check if it accepts arguments
            import inspect
            sig = inspect.signature(tool_function)
            param_names = list(sig.parameters.keys())
            
            # Only pass arguments that the function actually accepts
            final_arguments = {k: v for k, v in filtered_arguments.items() if k in param_names}
            
            result = tool_function(**final_arguments)
            
            response = {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ]
            }
            
            # Always return JSON-RPC 2.0 format for Groq compatibility
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": response
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Error executing tool: {str(e)}"
                }
            }
    except json.JSONDecodeError:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": "Parse error"
            }
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

# Player endpoint - serve HTML player
@app.get("/player")
async def player():
    """Serve the web audio player"""
    with open("player.html", "r") as f:
        return HTMLResponse(content=f.read())

# Stream proxy endpoint - proxy Airsonic streams
@app.get("/stream/{song_id}")
async def stream_song(song_id: str):
    """Proxy audio stream from Airsonic"""
    try:
        config = load_config()
        server_url = config.get("server_url", "http://localhost:4040")
        auth_params = get_airsonic_auth_params()
        auth_params["id"] = song_id
        
        stream_url = f"{server_url}/rest/stream.view"
        
        # Stream the audio from Airsonic
        response = requests.get(stream_url, params=auth_params, stream=True, timeout=30)
        response.raise_for_status()
        
        return StreamingResponse(
            response.iter_content(chunk_size=8192),
            media_type=response.headers.get("Content-Type", "audio/mpeg"),
            headers={
                "Content-Disposition": f'inline; filename="song_{song_id}.mp3"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error streaming song: {str(e)}")

# API endpoint to get current playback state
@app.get("/api/playback/state")
async def get_playback_state():
    """Get current playback state for player"""
    return JSONResponse(content=playback_state)

# API endpoint to update playback state
@app.post("/api/playback/control")
async def control_playback(request: Request):
    """Control playback from web player"""
    try:
        body = await request.json()
        action = body.get("action")
        
        if action == "pause":
            result = pause_playback()
        elif action == "resume":
            result = resume_playback()
        elif action == "stop":
            result = stop_playback()
        elif action == "seek":
            time_seconds = body.get("time_seconds", 0)
            if time_seconds < 0:
                # Clear seek position
                playback_state["seek_position"] = None
                result = "Seek position cleared"
            else:
                result = seek_to(int(time_seconds))
        elif action == "set_volume":
            volume = body.get("volume", 100)
            result = set_volume(int(volume))
        elif action == "mute":
            result = mute()
        elif action == "unmute":
            result = unmute()
        else:
            return JSONResponse(content={"error": "Invalid action"}, status_code=400)
        
        return JSONResponse(content={"status": "success", "message": result})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Legacy MCP endpoint for backward compatibility
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP endpoint - handles JSON-RPC 2.0 and legacy format"""
    try:
        body = await request.json()
        
        # Check if it's JSON-RPC 2.0 format
        if "jsonrpc" in body and "method" in body:
            method = body["method"]
            params = body.get("params", {})
            
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "airsonic-mcp",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "tools/list":
                tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                param.name: {"type": param.type}
                                for param in tool.parameters
                            },
                            "required": [param.name for param in tool.parameters]
                        }
                    }
                    for tool in ALL_TOOLS
                ]
                return {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {
                        "tools": tools
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name not in tool_registry:
                    return {
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "error": {
                            "code": -32601,
                            "message": f"Tool {tool_name} not found"
                        }
                    }
                
                try:
                    tool_function = tool_registry[tool_name]
                    
                    # Filter out empty string arguments and validate against function signature
                    import inspect
                    filtered_arguments = {k: v for k, v in arguments.items() if v != "" and v is not None}
                    sig = inspect.signature(tool_function)
                    param_names = list(sig.parameters.keys())
                    final_arguments = {k: v for k, v in filtered_arguments.items() if k in param_names}
                    
                    result = tool_function(**final_arguments)
                    
                    return {
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": str(result)
                                }
                            ]
                        }
                    }
                except Exception as e:
                    return {
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "error": {
                            "code": -32603,
                            "message": f"Error executing tool: {str(e)}"
                        }
                    }
        
        # Legacy format (verb-based)
        if "verb" in body:
            if body["verb"] == "discovery":
                return ModelContextResponse(tools=ALL_TOOLS)
            elif body["verb"] == "execute":
                tool_name = body.get("tool_name")
                arguments = body.get("arguments", {})
                
                if tool_name not in tool_registry:
                    raise HTTPException(status_code=400, detail=f"Tool {tool_name} not found")
                
                tool_function = tool_registry[tool_name]
                
                # Filter out empty string arguments and validate against function signature
                import inspect
                filtered_arguments = {k: v for k, v in arguments.items() if v != "" and v is not None}
                sig = inspect.signature(tool_function)
                param_names = list(sig.parameters.keys())
                final_arguments = {k: v for k, v in filtered_arguments.items() if k in param_names}
                
                result = tool_function(**final_arguments)
                return ModelContextResponse(result=result)
            
            raise HTTPException(status_code=400, detail=f"Invalid verb: {body['verb']}")
        
        # If we get here, the format is unknown
        raise HTTPException(status_code=422, detail="Invalid request format")
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Also add endpoints under /mcp/ path for Groq
@app.post("/mcp/initialize")
async def mcp_initialize_alt(request: Request):
    return await mcp_initialize(request)

@app.post("/mcp/tools/list")
async def mcp_tools_list_alt(request: Request):
    return await mcp_tools_list(request)

@app.post("/mcp/tools/call")
async def mcp_tools_call_alt(request: Request):
    return await mcp_tools_call(request)

