#!/bin/bash
# Test Airsonic API directly
# Update these values from your config.json

SERVER_URL="http://AIRSONIC_IP:4040"
USERNAME="AIRSONIC_USER_PASSWORD"
PASSWORD="AIRSONIC_PASSWORD"
API_VERSION="1.15.0"

# Generate auth token
SALT=$(openssl rand -hex 3)
TOKEN=$(echo -n "${PASSWORD}${SALT}" | md5sum | cut -d' ' -f1)

echo "Testing Airsonic API at ${SERVER_URL}"
echo ""

# Test 1: Ping
echo "1. Testing ping..."
curl -s "${SERVER_URL}/rest/ping.view?u=${USERNAME}&t=${TOKEN}&s=${SALT}&v=${API_VERSION}&c=test" | head -20
echo ""
echo ""

# Test 2: Get Random Songs
echo "2. Getting random songs..."
curl -s "${SERVER_URL}/rest/getRandomSongs.view?u=${USERNAME}&t=${TOKEN}&s=${SALT}&v=${API_VERSION}&c=test&size=5" | head -50
echo ""
echo ""

# Test 3: List Albums
echo "3. Listing albums..."
curl -s "${SERVER_URL}/rest/getAlbumList.view?u=${USERNAME}&t=${TOKEN}&s=${SALT}&v=${API_VERSION}&c=test&type=random&size=10" | head -50
echo ""
echo ""

# Test 4: Search
echo "4. Searching for songs..."
curl -s "${SERVER_URL}/rest/search3.view?u=${USERNAME}&t=${TOKEN}&s=${SALT}&v=${API_VERSION}&c=test&query=a&songCount=5" | head -50
echo ""

