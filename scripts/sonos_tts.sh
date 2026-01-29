#!/bin/bash
# ==============================================================================
# Sonos TTS Script - Download once and serve locally via OpenHAB
# ==============================================================================
# Usage: sonos_tts.sh <speaker_ip> <message>
# Plays text-to-speech announcement on Sonos speaker
# Downloads TTS from Google once (cached), serves via OpenHAB, plays on Sonos
# ==============================================================================

SPEAKER_IP="$1"
MESSAGE="$2"

# URL encode the message
MESSAGE_ENCODED=$(echo -n "$MESSAGE" | jq -sRr @uri)

# Create hash of message for filename (reuse same file for same message)
MESSAGE_HASH=$(echo -n "$MESSAGE" | md5sum | cut -d' ' -f1)
FILENAME="tts_${MESSAGE_HASH}.mp3"
LOCAL_PATH="/etc/openhab/html/${FILENAME}"

# Only download if file doesn't exist (reuse cached files)
if [ ! -f "${LOCAL_PATH}" ]; then
    # Use Google Translate TTS (free, no API key needed)
    TTS_URL="http://translate.google.com/translate_tts?ie=UTF-8&tl=da&client=tw-ob&q=${MESSAGE_ENCODED}"
    
    # Download TTS file from Google
    curl -s -A "Mozilla/5.0" "${TTS_URL}" -o "${LOCAL_PATH}"
fi

# Get OpenHAB IP address
OPENHAB_IP=$(hostname -I | awk '{print $1}')

# Create local URL that Sonos can access
LOCAL_TTS_URL="http://${OPENHAB_IP}:8080/static/${FILENAME}"

# Get current volume and save it
CURRENT_VOLUME=$(curl -s -X POST "http://${SPEAKER_IP}:1400/MediaRenderer/RenderingControl/Control" \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: urn:schemas-upnp-org:service:RenderingControl:1#GetVolume" \
  -d "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">
  <s:Body>
    <u:GetVolume xmlns:u=\"urn:schemas-upnp-org:service:RenderingControl:1\">
      <InstanceID>0</InstanceID>
      <Channel>Master</Channel>
    </u:GetVolume>
  </s:Body>
</s:Envelope>" | grep -oP '(?<=CurrentVolume>)[0-9]+')

# Save volume to temp file for restoration later
echo "${SPEAKER_IP}:${CURRENT_VOLUME}" >> /tmp/sonos_volumes.txt

# Set volume to 30 to ensure speaker can be heard
curl -s -X POST "http://${SPEAKER_IP}:1400/MediaRenderer/RenderingControl/Control" \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: urn:schemas-upnp-org:service:RenderingControl:1#SetVolume" \
  -d "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">
  <s:Body>
    <u:SetVolume xmlns:u=\"urn:schemas-upnp-org:service:RenderingControl:1\">
      <InstanceID>0</InstanceID>
      <Channel>Master</Channel>
      <DesiredVolume>30</DesiredVolume>
    </u:SetVolume>
  </s:Body>
</s:Envelope>" > /dev/null

# Send SOAP request to play the local TTS URL
curl -s -X POST "http://${SPEAKER_IP}:1400/MediaRenderer/AVTransport/Control" \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: urn:schemas-upnp-org:service:AVTransport:1#SetAVTransportURI" \
  -d "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">
  <s:Body>
    <u:SetAVTransportURI xmlns:u=\"urn:schemas-upnp-org:service:AVTransport:1\">
      <InstanceID>0</InstanceID>
      <CurrentURI>${LOCAL_TTS_URL}</CurrentURI>
      <CurrentURIMetaData></CurrentURIMetaData>
    </u:SetAVTransportURI>
  </s:Body>
</s:Envelope>" > /dev/null

# Play it
curl -s -X POST "http://${SPEAKER_IP}:1400/MediaRenderer/AVTransport/Control" \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: urn:schemas-upnp-org:service:AVTransport:1#Play" \
  -d "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">
  <s:Body>
    <u:Play xmlns:u=\"urn:schemas-upnp-org:service:AVTransport:1\">
      <InstanceID>0</InstanceID>
      <Speed>1</Speed>
    </u:Play>
  </s:Body>
</s:Envelope>" > /dev/null

# Wait for TTS to finish playing (estimate based on message length)
MESSAGE_LENGTH=${#MESSAGE}
PLAY_TIME=$((MESSAGE_LENGTH / 10 + 3))  # Roughly 10 chars per second + 3 second buffer
sleep ${PLAY_TIME}

# Restore original volume
if [ ! -z "$CURRENT_VOLUME" ]; then
  curl -s -X POST "http://${SPEAKER_IP}:1400/MediaRenderer/RenderingControl/Control" \
    -H "Content-Type: text/xml; charset=utf-8" \
    -H "SOAPAction: urn:schemas-upnp-org:service:RenderingControl:1#SetVolume" \
    -d "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">
  <s:Body>
    <u:SetVolume xmlns:u=\"urn:schemas-upnp-org:service:RenderingControl:1\">
      <InstanceID>0</InstanceID>
      <Channel>Master</Channel>
      <DesiredVolume>${CURRENT_VOLUME}</DesiredVolume>
    </u:SetVolume>
  </s:Body>
</s:Envelope>" > /dev/null
fi

# Clean up old TTS files (older than 1 day) to prevent disk filling
find /etc/openhab/html/tts_*.mp3 -type f -mtime +1 -delete 2>/dev/null

echo "TTS sent to ${SPEAKER_IP}: ${MESSAGE}"
