const API_BASE = window.location.origin;
let currentSongId = null;
let currentStreamUrl = null;
let isSeeking = false;
let isMuted = false;
let savedVolume = 100;

const audioPlayer = document.getElementById('audioPlayer');
const seekSlider = document.getElementById('seekSlider');
const volumeSlider = document.getElementById('volumeSlider');
const timeDisplay = document.getElementById('timeDisplay');
const volumeIcon = document.getElementById('volumeIcon');

// Set initial volume
audioPlayer.volume = 1.0;

// Update time display and seek slider
audioPlayer.addEventListener('timeupdate', updateTimeDisplay);
audioPlayer.addEventListener('loadedmetadata', function() {
    seekSlider.max = audioPlayer.duration || 100;
});
audioPlayer.addEventListener('durationchange', function() {
    seekSlider.max = audioPlayer.duration || 100;
});

// Poll for playback state updates
setInterval(updatePlaybackState, 2000);

function formatTime(seconds) {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function updateTimeDisplay() {
    if (!isSeeking) {
        const current = audioPlayer.currentTime || 0;
        const duration = audioPlayer.duration || 0;
        seekSlider.value = duration > 0 ? (current / duration) * 100 : 0;
        timeDisplay.textContent = `${formatTime(current)} / ${formatTime(duration)}`;
    }
}

function seekTo(value) {
    isSeeking = true;
    const duration = audioPlayer.duration || 0;
    if (duration > 0) {
        audioPlayer.currentTime = (value / 100) * duration;
    }
    setTimeout(() => { isSeeking = false; }, 100);
}

function setVolume(value) {
    const volume = value / 100;
    audioPlayer.volume = volume;
    if (volume === 0) {
        volumeIcon.textContent = '🔇';
        isMuted = true;
    } else if (volume < 0.5) {
        volumeIcon.textContent = '🔉';
        isMuted = false;
    } else {
        volumeIcon.textContent = '🔊';
        isMuted = false;
    }
    savedVolume = value;
}

function toggleMute() {
    if (isMuted || audioPlayer.volume === 0) {
        audioPlayer.volume = savedVolume / 100;
        volumeSlider.value = savedVolume;
        if (savedVolume === 0) {
            volumeIcon.textContent = '🔇';
        } else if (savedVolume < 50) {
            volumeIcon.textContent = '🔉';
        } else {
            volumeIcon.textContent = '🔊';
        }
        isMuted = false;
    } else {
        savedVolume = audioPlayer.volume * 100;
        audioPlayer.volume = 0;
        volumeSlider.value = 0;
        volumeIcon.textContent = '🔇';
        isMuted = true;
    }
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    if (tabName === 'browse') {
        document.querySelector('.tab').classList.add('active');
        document.getElementById('browseTab').classList.add('active');
    } else {
        document.querySelectorAll('.tab')[1].classList.add('active');
        document.getElementById('searchTab').classList.add('active');
    }
}

async function updatePlaybackState() {
    try {
        const response = await fetch(`${API_BASE}/api/playback/state`);
        const state = await response.json();
        
        const playerBar = document.getElementById('playerBar');
        const playerStatus = document.getElementById('playerStatus');
        
        if (state.current_song) {
            currentSongId = state.current_song;
            currentStreamUrl = state.current_stream_url;
            
            // Update UI
            document.getElementById('playBtn').disabled = false;
            document.getElementById('pauseBtn').disabled = !state.is_playing;
            document.getElementById('stopBtn').disabled = false;
            
            // Update status
            if (state.is_playing) {
                playerStatus.textContent = 'Playing';
                playerBar.className = 'player-bar status playing';
            } else if (state.is_paused) {
                playerStatus.textContent = 'Paused';
                playerBar.className = 'player-bar status paused';
            } else {
                playerStatus.textContent = 'Stopped';
                playerBar.className = 'player-bar status stopped';
            }
            
            // Update audio player
            if (currentStreamUrl && audioPlayer.src !== currentStreamUrl) {
                audioPlayer.src = currentStreamUrl;
                audioPlayer.load();
                if (state.is_playing) {
                    audioPlayer.play();
                }
            }
            
            // Handle seek position
            if (state.seek_position !== null && state.seek_position !== undefined) {
                audioPlayer.currentTime = state.seek_position;
                // Clear seek position after applying
                fetch(`${API_BASE}/api/playback/control`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'seek', time_seconds: -1 }) // -1 to clear
                });
            }
            
            // Handle volume changes
            if (state.volume !== undefined && state.volume !== null) {
                const volumeValue = state.is_muted ? 0 : state.volume / 100;
                if (Math.abs(audioPlayer.volume - volumeValue) > 0.01) {
                    audioPlayer.volume = volumeValue;
                    volumeSlider.value = state.is_muted ? 0 : state.volume;
                    volumeIcon.textContent = state.is_muted ? '🔇' : (state.volume < 50 ? '🔉' : '🔊');
                    isMuted = state.is_muted;
                    savedVolume = state.volume;
                }
            }
            
            // Get song info
            await updateSongInfo(state.current_song);
        } else {
            // No song playing
            document.getElementById('playerTitle').textContent = 'No song playing';
            document.getElementById('playerArtist').textContent = 'Select a song to play';
            playerStatus.textContent = 'Stopped';
            playerBar.className = 'player-bar status stopped';
            document.getElementById('playBtn').disabled = true;
            document.getElementById('pauseBtn').disabled = true;
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('audioPlayer').src = '';
        }
    } catch (error) {
        console.error('Error updating playback state:', error);
    }
}

async function updateSongInfo(songId) {
    try {
        const response = await fetch(`${API_BASE}/tools/call`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: 'get_current_song',
                arguments: {}
            })
        });
        
        const result = await response.json();
        if (result.result && result.result.content) {
            const text = result.result.content[0].text;
            // Parse song info from text
            const match = text.match(/Current song: (.+?) by (.+?) from album/);
            if (match) {
                const [, title, artist] = match;
                document.getElementById('playerTitle').textContent = title;
                document.getElementById('playerArtist').textContent = artist;
            } else {
                // Fallback
                document.getElementById('playerTitle').textContent = `Song ID: ${songId}`;
                document.getElementById('playerArtist').textContent = 'Playing...';
            }
        }
    } catch (error) {
        console.error('Error updating song info:', error);
    }
}

async function playCurrent() {
    if (!currentStreamUrl) return;
    const audioPlayer = document.getElementById('audioPlayer');
    audioPlayer.play();
    await controlPlayback('resume');
}

async function pausePlayback() {
    const audioPlayer = document.getElementById('audioPlayer');
    audioPlayer.pause();
    await controlPlayback('pause');
}

async function stopPlayback() {
    const audioPlayer = document.getElementById('audioPlayer');
    audioPlayer.pause();
    audioPlayer.currentTime = 0;
    await controlPlayback('stop');
}

async function controlPlayback(action) {
    try {
        await fetch(`${API_BASE}/api/playback/control`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        await updatePlaybackState();
    } catch (error) {
        console.error('Error controlling playback:', error);
    }
}

function renderSongsList(songs, containerId) {
    const container = document.getElementById(containerId);
    if (songs.length === 0) {
        container.innerHTML = '<div class="empty-state">No songs found</div>';
        return;
    }
    
    let html = '';
    songs.forEach(song => {
        html += `
            <div class="song-item" onclick="playSong('${song.songId}')">
                <div class="song-item-info">
                    <div class="song-item-title">${song.title}</div>
                    <div class="song-item-artist">${song.artist}</div>
                </div>
                <span class="song-item-id">ID: ${song.songId}</span>
                <span class="play-icon">▶</span>
            </div>
        `;
    });
    container.innerHTML = html;
}

async function loadRandomSongs() {
    const container = document.getElementById('browseResults');
    container.innerHTML = '<div class="loading">Loading songs...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/tools/call`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: 'get_random_songs',
                arguments: { count: 50 }
            })
        });
        
        const result = await response.json();
        if (result.result && result.result.content) {
            const text = result.result.content[0].text;
            // Parse songs from text
            const lines = text.split('\n').filter(line => line.trim() && /^\d+\./.test(line));
            const songs = [];
            
            lines.forEach(line => {
                const match = line.match(/(\d+)\. (.+?) by (.+?) \(ID: (\d+)\)/);
                if (match) {
                    const [, , title, artist, songId] = match;
                    songs.push({ title, artist, songId });
                }
            });
            
            renderSongsList(songs, 'browseResults');
        } else {
            container.innerHTML = '<div class="empty-state">No songs found</div>';
        }
    } catch (error) {
        console.error('Error loading songs:', error);
        container.innerHTML = '<div class="empty-state">Error loading songs</div>';
    }
}

async function searchSongs() {
    const query = document.getElementById('searchInput').value.trim();
    if (!query) {
        alert('Please enter a search query');
        return;
    }
    
    const container = document.getElementById('searchResults');
    container.innerHTML = '<div class="loading">Searching...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/tools/call`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: 'search_songs',
                arguments: { query }
            })
        });
        
        const result = await response.json();
        if (result.result && result.result.content) {
            const text = result.result.content[0].text;
            // Parse songs from text
            const lines = text.split('\n').filter(line => line.trim() && /^\d+\./.test(line));
            const songs = [];
            
            lines.forEach(line => {
                const match = line.match(/(\d+)\. (.+?) by (.+?) \(ID: (\d+)\)/);
                if (match) {
                    const [, , title, artist, songId] = match;
                    songs.push({ title, artist, songId });
                }
            });
            
            renderSongsList(songs, 'searchResults');
        } else {
            container.innerHTML = '<div class="empty-state">No results found</div>';
        }
    } catch (error) {
        console.error('Error searching songs:', error);
        container.innerHTML = '<div class="empty-state">Error searching songs</div>';
    }
}

async function playSong(songId) {
    try {
        await fetch(`${API_BASE}/tools/call`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: 'play_song',
                arguments: { song_id: songId }
            })
        });
        
        await updatePlaybackState();
    } catch (error) {
        console.error('Error playing song:', error);
        alert('Error playing song');
    }
}

function handleSearchKeyPress(event) {
    if (event.key === 'Enter') {
        searchSongs();
    }
}

// Initial state update and load random songs
updatePlaybackState();
loadRandomSongs();

