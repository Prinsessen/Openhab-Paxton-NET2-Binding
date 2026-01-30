#!/bin/bash
# ==============================================================================
# Sonos Device Error Notification Script
# ==============================================================================
# Usage: sonos_error_notify.sh <speaker_ip> <device_name> <error_message>
# Plays doorbell sound first, then announces error via TTS
# Saves and restores volume and audio source
# ==============================================================================

SPEAKER_IP="$1"
DEVICE_NAME="$2"
ERROR_MESSAGE="$3"

# Get current volume
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

# Get current transport state and URI
TRANSPORT_INFO=$(curl -s -X POST "http://${SPEAKER_IP}:1400/MediaRenderer/AVTransport/Control" \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: urn:schemas-upnp-org:service:AVTransport:1#GetTransportInfo" \
  -d "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">
  <s:Body>
    <u:GetTransportInfo xmlns:u=\"urn:schemas-upnp-org:service:AVTransport:1\">
      <InstanceID>0</InstanceID>
    </u:GetTransportInfo>
  </s:Body>
</s:Envelope>")

CURRENT_STATE=$(echo "$TRANSPORT_INFO" | grep -oP '(?<=CurrentTransportState>)[^<]+')

POSITION_INFO=$(curl -s -X POST "http://${SPEAKER_IP}:1400/MediaRenderer/AVTransport/Control" \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: urn:schemas-upnp-org:service:AVTransport:1#GetPositionInfo" \
  -d "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">
  <s:Body>
    <u:GetPositionInfo xmlns:u=\"urn:schemas-upnp-org:service:AVTransport:1\">
      <InstanceID>0</InstanceID>
    </u:GetPositionInfo>
  </s:Body>
</s:Envelope>")

CURRENT_URI=$(echo "$POSITION_INFO" | grep -oP '(?<=TrackURI>)[^<]+' | head -1)
CURRENT_METADATA=$(echo "$POSITION_INFO" | grep -oP '(?<=TrackMetaData>).*?(?=</TrackMetaData>)' | head -1)

# Set volume to 30 for announcement
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

# Play doorbell sound first
curl -s -X POST "http://${SPEAKER_IP}:1400/MediaRenderer/AVTransport/Control" \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: urn:schemas-upnp-org:service:AVTransport:1#SetAVTransportURI" \
  -d "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">
  <s:Body>
    <u:SetAVTransportURI xmlns:u=\"urn:schemas-upnp-org:service:AVTransport:1\">
      <InstanceID>0</InstanceID>
      <CurrentURI>x-file-cifs://openhab5.agesen.dk/openhab/sounds/doorbell.mp3</CurrentURI>
      <CurrentURIMetaData></CurrentURIMetaData>
    </u:SetAVTransportURI>
  </s:Body>
</s:Envelope>" > /dev/null

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

# Wait for doorbell to finish (approximately 2 seconds)
sleep 3

# URL encode the announcement message
ANNOUNCEMENT="Advarsel: ${DEVICE_NAME} fejl. ${ERROR_MESSAGE}"
ANNOUNCEMENT_ENCODED=$(echo -n "$ANNOUNCEMENT" | jq -sRr @uri)

# Use Google Translate TTS for Danish
TTS_URL="https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=da&q=${ANNOUNCEMENT_ENCODED}"

# Play TTS announcement
curl -s -X POST "http://${SPEAKER_IP}:1400/MediaRenderer/AVTransport/Control" \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: urn:schemas-upnp-org:service:AVTransport:1#SetAVTransportURI" \
  -d "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">
  <s:Body>
    <u:SetAVTransportURI xmlns:u=\"urn:schemas-upnp-org:service:AVTransport:1\">
      <InstanceID>0</InstanceID>
      <CurrentURI>${TTS_URL}</CurrentURI>
      <CurrentURIMetaData></CurrentURIMetaData>
    </u:SetAVTransportURI>
  </s:Body>
</s:Envelope>" > /dev/null

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

# Wait for TTS to finish (estimate based on message length)
ANNOUNCEMENT_LENGTH=${#ANNOUNCEMENT}
SLEEP_TIME=$((ANNOUNCEMENT_LENGTH / 10 + 3))
sleep $SLEEP_TIME

# Restore original volume
if [ -n "$CURRENT_VOLUME" ]; then
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

# Restore original audio source if it was playing something
if [ -n "$CURRENT_URI" ] && [ "$CURRENT_URI" != "NOT_IMPLEMENTED" ]; then
  curl -s -X POST "http://${SPEAKER_IP}:1400/MediaRenderer/AVTransport/Control" \
    -H "Content-Type: text/xml; charset=utf-8" \
    -H "SOAPAction: urn:schemas-upnp-org:service:AVTransport:1#SetAVTransportURI" \
    -d "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">
  <s:Body>
    <u:SetAVTransportURI xmlns:u=\"urn:schemas-upnp-org:service:AVTransport:1\">
      <InstanceID>0</InstanceID>
      <CurrentURI>${CURRENT_URI}</CurrentURI>
      <CurrentURIMetaData>${CURRENT_METADATA}</CurrentURIMetaData>
    </u:SetAVTransportURI>
  </s:Body>
</s:Envelope>" > /dev/null
  
  # Resume playback if it was playing
  if [ "$CURRENT_STATE" = "PLAYING" ]; then
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
  fi
fi

echo "Error notification sent to ${SPEAKER_IP}: ${ANNOUNCEMENT}"
