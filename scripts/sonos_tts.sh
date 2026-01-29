#!/bin/bash
# ==============================================================================
# Sonos TTS Script - Direct SOAP API calls
# ==============================================================================
# Usage: sonos_tts.sh <speaker_ip> <message>
# Plays text-to-speech announcement on Sonos speaker
# ==============================================================================

SPEAKER_IP="$1"
MESSAGE="$2"

# URL encode the message
MESSAGE_ENCODED=$(echo -n "$MESSAGE" | jq -sRr @uri)

# Use Google Translate TTS (free, no API key needed)
TTS_URL="https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=da&q=${MESSAGE_ENCODED}"

# Send SOAP request to play the TTS URL
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

echo "TTS sent to ${SPEAKER_IP}: ${MESSAGE}"
