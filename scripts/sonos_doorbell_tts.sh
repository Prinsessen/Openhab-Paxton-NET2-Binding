#!/bin/bash
# ==============================================================================
# Sonos Doorbell + TTS Script
# ==============================================================================
# Usage: sonos_doorbell_tts.sh <speaker_ip> <message>
# Plays doorbell sound followed by TTS announcement on Sonos speaker
# ==============================================================================

SPEAKER_IP="$1"
MESSAGE="$2"

# Get OpenHAB IP address
OPENHAB_IP=$(hostname -I | awk '{print $1}')

# URL for doorbell sound
DOORBELL_URL="http://${OPENHAB_IP}:8080/static/doorbell.mp3"

# Get current volume and audio source before playing anything
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

CURRENT_URI=$(curl -s -X POST "http://${SPEAKER_IP}:1400/MediaRenderer/AVTransport/Control" \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: urn:schemas-upnp-org:service:AVTransport:1#GetPositionInfo" \
  -d "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">
  <s:Body>
    <u:GetPositionInfo xmlns:u=\"urn:schemas-upnp-org:service:AVTransport:1\">
      <InstanceID>0</InstanceID>
    </u:GetPositionInfo>
  </s:Body>
</s:Envelope>" | grep -oP '(?<=TrackURI>)[^<]+' | head -1)

# Set volume to 30
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

# Play doorbell sound
curl -s -X POST "http://${SPEAKER_IP}:1400/MediaRenderer/AVTransport/Control" \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: urn:schemas-upnp-org:service:AVTransport:1#SetAVTransportURI" \
  -d "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">
  <s:Body>
    <u:SetAVTransportURI xmlns:u=\"urn:schemas-upnp-org:service:AVTransport:1\">
      <InstanceID>0</InstanceID>
      <CurrentURI>${DOORBELL_URL}</CurrentURI>
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

# Wait for doorbell to finish (3 seconds)
sleep 3

# Now play TTS message using the existing script
/etc/openhab/scripts/sonos_tts.sh "${SPEAKER_IP}" "${MESSAGE}"

# Note: sonos_tts.sh will restore volume and source, but we need to ensure it uses our saved values
# So we pass them through environment or let it handle its own restoration

echo "Doorbell + TTS sent to ${SPEAKER_IP}: ${MESSAGE}"
