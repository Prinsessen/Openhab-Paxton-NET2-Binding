#!/bin/bash
# ==============================================================================
# Sonos TTS Script - Download and serve locally via OpenHAB
# ==============================================================================
# Usage: sonos_tts.sh <speaker_ip> <message>
# Plays text-to-speech announcement on Sonos speaker
# Downloads TTS from Google, serves via OpenHAB, plays on Sonos
# ==============================================================================

SPEAKER_IP="$1"
MESSAGE="$2"

# URL encode the message
MESSAGE_ENCODED=$(echo -n "$MESSAGE" | jq -sRr @uri)

# Generate unique filename based on timestamp and hash
TIMESTAMP=$(date +%s%N)
FILENAME="tts_${TIMESTAMP}.mp3"
LOCAL_PATH="/etc/openhab/html/${FILENAME}"

# Use Google Translate TTS (free, no API key needed)
TTS_URL="http://translate.google.com/translate_tts?ie=UTF-8&tl=da&client=tw-ob&q=${MESSAGE_ENCODED}"

# Download TTS file from Google
curl -s -A "Mozilla/5.0" "${TTS_URL}" -o "${LOCAL_PATH}"

# Get OpenHAB IP address
OPENHAB_IP=$(hostname -I | awk '{print $1}')

# Create local URL that Sonos can access
LOCAL_TTS_URL="http://${OPENHAB_IP}:8080/static/${FILENAME}"

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

# Clean up old TTS files (older than 5 minutes) to prevent disk filling
find /etc/openhab/html/tts_*.mp3 -type f -mmin +5 -delete 2>/dev/null

echo "TTS sent to ${SPEAKER_IP}: ${MESSAGE}"
