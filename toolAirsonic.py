from models import Tool, ToolParameter
import requests
import json
import xml.etree.ElementTree as ET
import hashlib
import base64
from typing import Dict, Optional

# Global state for playback control
playback_state = {
    "current_song": None,
    "is_playing": False,
    "is_paused": False,
    "current_stream_url": None,
    "seek_position": None,  # Position in seconds to seek to
    "volume": 100,  # Volume percentage (0-100)
    "is_muted": False  # Mute state
}

# Load config
def load_config():
    """Load Airsonic configuration from config.json"""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return config.get("airsonic", {})
    except FileNotFoundError:
        raise Exception("config.json not found. Please create it with your Airsonic server details.")
    except json.JSONDecodeError:
        raise Exception("Invalid config.json format.")

def get_airsonic_auth_params():
    """Generate Airsonic authentication parameters"""
    config = load_config()
    username = config.get("username")
    password = config.get("password")
    api_version = config.get("api_version", "1.15.0")
    use_token_auth = config.get("use_token_auth", True)
    
    if use_token_auth:
        # Airsonic uses token-based auth: salt + md5(password + salt)
        import random
        import string
        salt = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        token = hashlib.md5((password + salt).encode()).hexdigest()
        
        return {
            "u": username,
            "t": token,
            "s": salt,
            "v": api_version,
            "c": "airsonic-mcp"
        }
    else:
        # Fallback to password-based auth (less secure)
        return {
            "u": username,
            "p": password,
            "v": api_version,
            "c": "airsonic-mcp"
        }

def make_airsonic_request(endpoint: str, params: Optional[Dict] = None):
    """Make a request to Airsonic API"""
    config = load_config()
    server_url = config.get("server_url", "http://localhost:4040")
    
    auth_params = get_airsonic_auth_params()
    if params:
        auth_params.update(params)
    
    url = f"{server_url}/rest/{endpoint}"
    try:
        response = requests.get(url, params=auth_params, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        raise Exception(f"Airsonic API error: {str(e)}")

def parse_xml_response(response):
    """Parse XML response from Airsonic"""
    try:
        # Remove namespaces from XML to simplify parsing
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        # Remove namespace declarations
        content = content.replace('xmlns="http://subsonic.org/restapi"', '')
        root = ET.fromstring(content)
        # Check for errors in response
        status = root.get("status")
        if status == "failed":
            error = root.find(".//error")
            if error is not None:
                error_msg = error.get("message", "Unknown error")
                raise Exception(f"Airsonic API error: {error_msg}")
        return root
    except ET.ParseError as e:
        raise Exception(f"Failed to parse Airsonic response: {str(e)}")

# MCP Tool Functions
def list_albums(size: int = 50) -> str:
    """List albums from Airsonic library"""
    try:
        response = make_airsonic_request("getAlbumList.view", {"type": "random", "size": size})
        root = parse_xml_response(response)
        
        albums = []
        # Find albums - namespace is stripped in parse_xml_response
        album_elements = root.findall(".//album")
        
        for album in album_elements:
            album_id = album.get("id")
            name = album.get("name", "Unknown")
            artist = album.get("artist", "Unknown")
            song_count = album.get("songCount", "0")
            albums.append({
                "id": album_id,
                "name": name,
                "artist": artist,
                "song_count": song_count
            })
        
        if not albums:
            return "No albums found in library."
        
        result = f"Found {len(albums)} albums:\n"
        for i, album in enumerate(albums[:20], 1):  # Show first 20
            result += f"{i}. {album['name']} by {album['artist']} ({album['song_count']} songs, ID: {album['id']})\n"
        
        return result
    except Exception as e:
        return f"Error listing albums: {str(e)}"

def get_random_songs(count: int = 20) -> str:
    """Get random songs from library"""
    try:
        response = make_airsonic_request("getRandomSongs.view", {"size": count})
        root = parse_xml_response(response)
        
        songs = []
        # Find songs - namespace is stripped in parse_xml_response
        song_elements = root.findall(".//song")
        
        for song in song_elements:
            song_id = song.get("id")
            title = song.get("title", "Unknown")
            artist = song.get("artist", "Unknown")
            album = song.get("album", "Unknown")
            duration = song.get("duration", "0")
            songs.append({
                "id": song_id,
                "title": title,
                "artist": artist,
                "album": album,
                "duration": duration
            })
        
        if not songs:
            return "No songs found in library."
        
        result = f"Random {len(songs)} songs from library:\n"
        for i, song in enumerate(songs, 1):
            result += f"{i}. {song['title']} by {song['artist']} (ID: {song['id']})\n"
        
        return result
    except Exception as e:
        return f"Error getting random songs: {str(e)}"

def list_songs(count: int = 10) -> str:
    """List songs from the music library"""
    try:
        # Use search with empty query to get songs, or use getNewestSongs
        # Try getNewestSongs first, fallback to search with empty query
        try:
            response = make_airsonic_request("getNewestSongs.view", {"size": count})
        except:
            # Fallback to search with empty query
            response = make_airsonic_request("search3.view", {"query": "", "songCount": count})
        
        root = parse_xml_response(response)
        
        songs = []
        # Find songs - namespace is stripped in parse_xml_response
        song_elements = root.findall(".//song")
        
        for song in song_elements:
            song_id = song.get("id")
            title = song.get("title", "Unknown")
            artist = song.get("artist", "Unknown")
            album = song.get("album", "Unknown")
            duration = song.get("duration", "0")
            songs.append({
                "id": song_id,
                "title": title,
                "artist": artist,
                "album": album,
                "duration": duration
            })
        
        if not songs:
            return "No songs found in library."
        
        result = f"Found {len(songs)} songs from library:\n"
        for i, song in enumerate(songs, 1):
            result += f"{i}. {song['title']} by {song['artist']} (ID: {song['id']})\n"
        
        return result
    except Exception as e:
        return f"Error listing songs: {str(e)}"

def search_songs(query: str) -> str:
    """Search for songs in Airsonic library"""
    try:
        response = make_airsonic_request("search3.view", {"query": query, "songCount": 20})
        root = parse_xml_response(response)
        
        songs = []
        # Find songs - namespace is stripped in parse_xml_response
        song_elements = root.findall(".//song")
        
        for song in song_elements:
            song_id = song.get("id")
            title = song.get("title", "Unknown")
            artist = song.get("artist", "Unknown")
            album = song.get("album", "Unknown")
            duration = song.get("duration", "0")
            songs.append({
                "id": song_id,
                "title": title,
                "artist": artist,
                "album": album,
                "duration": duration
            })
        
        if not songs:
            return f"No songs found for query: '{query}'"
        
        result = f"Found {len(songs)} songs:\n"
        for i, song in enumerate(songs[:10], 1):  # Show first 10
            result += f"{i}. {song['title']} by {song['artist']} (ID: {song['id']})\n"
        
        return result
    except Exception as e:
        return f"Error searching songs: {str(e)}"

def play_song(song_id: str) -> str:
    """Start playing a song and return stream URL"""
    try:
        config = load_config()
        server_url = config.get("server_url", "http://localhost:4040")
        auth_params = get_airsonic_auth_params()
        
        # Get stream URL
        stream_url = f"{server_url}/rest/stream.view"
        auth_params["id"] = song_id
        
        # Update playback state
        playback_state["current_song"] = song_id
        playback_state["is_playing"] = True
        playback_state["is_paused"] = False
        playback_state["current_stream_url"] = stream_url + "?" + "&".join([f"{k}={v}" for k, v in auth_params.items()])
        
        # Get song info
        response = make_airsonic_request("getSong.view", {"id": song_id})
        root = parse_xml_response(response)
        song = root.find(".//song")
        
        if song is not None:
            title = song.get("title", "Unknown")
            artist = song.get("artist", "Unknown")
            return f"Now playing: {title} by {artist}. Stream URL: {playback_state['current_stream_url']}"
        else:
            return f"Playing song ID: {song_id}. Stream URL: {playback_state['current_stream_url']}"
    except Exception as e:
        return f"Error playing song: {str(e)}"

def pause_playback() -> str:
    """Pause current playback"""
    if not playback_state["current_song"]:
        return "No song is currently playing."
    
    playback_state["is_paused"] = True
    playback_state["is_playing"] = False
    return "Playback paused."

def resume_playback() -> str:
    """Resume paused playback"""
    if not playback_state["current_song"]:
        return "No song to resume."
    
    if not playback_state["is_paused"]:
        return "Playback is not paused."
    
    playback_state["is_paused"] = False
    playback_state["is_playing"] = True
    return "Playback resumed."

def stop_playback() -> str:
    """Stop current playback"""
    if not playback_state["current_song"]:
        return "No song is currently playing."
    
    playback_state["current_song"] = None
    playback_state["is_playing"] = False
    playback_state["is_paused"] = False
    playback_state["current_stream_url"] = None
    return "Playback stopped."

def get_current_song() -> str:
    """Get currently playing song info"""
    if not playback_state["current_song"]:
        return "No song is currently playing."
    
    try:
        response = make_airsonic_request("getSong.view", {"id": playback_state["current_song"]})
        root = parse_xml_response(response)
        song = root.find(".//song")
        
        if song is not None:
            title = song.get("title", "Unknown")
            artist = song.get("artist", "Unknown")
            album = song.get("album", "Unknown")
            duration = song.get("duration", "0")
            status = "playing" if playback_state["is_playing"] else "paused"
            return f"Current song: {title} by {artist} from album {album} ({duration}s) - Status: {status}"
        else:
            return f"Playing song ID: {playback_state['current_song']} - Status: {'playing' if playback_state['is_playing'] else 'paused'}"
    except Exception as e:
        return f"Error getting current song: {str(e)}"

def get_playlists() -> str:
    """List available playlists"""
    try:
        response = make_airsonic_request("getPlaylists.view")
        root = parse_xml_response(response)
        
        playlists = []
        for playlist in root.findall(".//playlist"):
            playlist_id = playlist.get("id")
            name = playlist.get("name", "Unknown")
            song_count = playlist.get("songCount", "0")
            playlists.append({
                "id": playlist_id,
                "name": name,
                "song_count": song_count
            })
        
        if not playlists:
            return "No playlists found."
        
        result = f"Found {len(playlists)} playlists:\n"
        for playlist in playlists:
            result += f"- {playlist['name']} (ID: {playlist['id']}, {playlist['song_count']} songs)\n"
        
        return result
    except Exception as e:
        return f"Error getting playlists: {str(e)}"

def seek_to(time_seconds: int) -> str:
    """Seek to a specific time position in the currently playing song (time in seconds)"""
    if not playback_state["current_song"]:
        return "No song is currently playing."
    
    if time_seconds < 0:
        return "Time position must be positive."
    
    playback_state["seek_position"] = time_seconds
    
    # Get song duration to validate
    try:
        response = make_airsonic_request("getSong.view", {"id": playback_state["current_song"]})
        root = parse_xml_response(response)
        song = root.find(".//song")
        
        if song is not None:
            duration = int(song.get("duration", "0"))
            if time_seconds > duration:
                return f"Time position {time_seconds}s exceeds song duration of {duration}s."
            
            minutes = time_seconds // 60
            seconds = time_seconds % 60
            return f"Seeking to {minutes}:{seconds:02d} in the current song."
        else:
            return f"Seeking to {time_seconds}s in the current song."
    except Exception as e:
        return f"Seeking to {time_seconds}s. Note: {str(e)}"

def set_volume(volume: int) -> str:
    """Set the volume level (0-100 percentage)"""
    if volume < 0 or volume > 100:
        return "Volume must be between 0 and 100."
    
    playback_state["volume"] = volume
    playback_state["is_muted"] = False  # Unmute when setting volume
    
    return f"Volume set to {volume}%."

def mute() -> str:
    """Mute the audio playback"""
    playback_state["is_muted"] = True
    return "Audio muted."

def unmute() -> str:
    """Unmute the audio playback"""
    playback_state["is_muted"] = False
    return f"Audio unmuted. Volume is at {playback_state['volume']}%."

def play_playlist(playlist_id: str) -> str:
    """Play a playlist (starts with first song)"""
    try:
        response = make_airsonic_request("getPlaylist.view", {"id": playlist_id})
        root = parse_xml_response(response)
        
        playlist_name = root.find(".//playlist").get("name", "Unknown Playlist")
        songs = root.findall(".//song")
        
        if not songs:
            return f"Playlist '{playlist_name}' is empty."
        
        # Play first song
        first_song = songs[0]
        song_id = first_song.get("id")
        title = first_song.get("title", "Unknown")
        artist = first_song.get("artist", "Unknown")
        
        # Update state
        playback_state["current_song"] = song_id
        playback_state["is_playing"] = True
        playback_state["is_paused"] = False
        
        config = load_config()
        server_url = config.get("server_url", "http://localhost:4040")
        auth_params = get_airsonic_auth_params()
        auth_params["id"] = song_id
        playback_state["current_stream_url"] = f"{server_url}/rest/stream.view?" + "&".join([f"{k}={v}" for k, v in auth_params.items()])
        
        return f"Playing playlist '{playlist_name}': {title} by {artist} (first of {len(songs)} songs). Stream URL: {playback_state['current_stream_url']}"
    except Exception as e:
        return f"Error playing playlist: {str(e)}"

# MCP Tool Definitions
SEARCH_SONGS_TOOL = Tool(
    name="search_songs",
    description="Search for songs in the Airsonic music library",
    parameters=[ToolParameter(name="query", type="string")]
)

PLAY_SONG_TOOL = Tool(
    name="play_song",
    description="Start playing a song by its ID (use search_songs to find song IDs)",
    parameters=[ToolParameter(name="song_id", type="string")]
)

PAUSE_PLAYBACK_TOOL = Tool(
    name="pause_playback",
    description="Pause the currently playing song",
    parameters=[]
)

RESUME_PLAYBACK_TOOL = Tool(
    name="resume_playback",
    description="Resume paused playback",
    parameters=[]
)

STOP_PLAYBACK_TOOL = Tool(
    name="stop_playback",
    description="Stop the currently playing song",
    parameters=[]
)

GET_CURRENT_SONG_TOOL = Tool(
    name="get_current_song",
    description="Get information about the currently playing song",
    parameters=[]
)

GET_PLAYLISTS_TOOL = Tool(
    name="get_playlists",
    description="List all available playlists in Airsonic",
    parameters=[]
)

PLAY_PLAYLIST_TOOL = Tool(
    name="play_playlist",
    description="Play a playlist by its ID (starts with first song)",
    parameters=[ToolParameter(name="playlist_id", type="string")]
)

LIST_ALBUMS_TOOL = Tool(
    name="list_albums",
    description="List albums from the Airsonic music library",
    parameters=[ToolParameter(name="size", type="number")]
)

GET_RANDOM_SONGS_TOOL = Tool(
    name="get_random_songs",
    description="Get random songs from the Airsonic music library",
    parameters=[ToolParameter(name="count", type="number")]
)

LIST_SONGS_TOOL = Tool(
    name="list_songs",
    description="List songs from the music library (returns first N songs)",
    parameters=[ToolParameter(name="count", type="number")]
)

SEEK_TO_TOOL = Tool(
    name="seek_to",
    description="Seek to a specific time position in the currently playing song (time in seconds). Example: 60 for 1 minute, 120 for 2 minutes",
    parameters=[ToolParameter(name="time_seconds", type="number")]
)

SET_VOLUME_TOOL = Tool(
    name="set_volume",
    description="Set the volume level (0-100 percentage). Example: 50 for 50%, 0 for mute, 100 for maximum",
    parameters=[ToolParameter(name="volume", type="number")]
)

MUTE_TOOL = Tool(
    name="mute",
    description="Mute the audio playback",
    parameters=[]
)

UNMUTE_TOOL = Tool(
    name="unmute",
    description="Unmute the audio playback",
    parameters=[]
)

# Export all tools
ALL_TOOLS = [
    SEARCH_SONGS_TOOL,
    LIST_SONGS_TOOL,
    LIST_ALBUMS_TOOL,
    GET_RANDOM_SONGS_TOOL,
    PLAY_SONG_TOOL,
    PAUSE_PLAYBACK_TOOL,
    RESUME_PLAYBACK_TOOL,
    STOP_PLAYBACK_TOOL,
    SEEK_TO_TOOL,
    SET_VOLUME_TOOL,
    MUTE_TOOL,
    UNMUTE_TOOL,
    GET_CURRENT_SONG_TOOL,
    GET_PLAYLISTS_TOOL,
    PLAY_PLAYLIST_TOOL
]

