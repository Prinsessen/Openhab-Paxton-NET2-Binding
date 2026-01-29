#!/bin/bash
# ==============================================================================
# Sonos Volume Restoration Script
# ==============================================================================
# Restores speaker volumes saved by sonos_tts.sh
# Usage: Called after TTS announcements complete
# ==============================================================================

VOLUME_FILE="/tmp/sonos_volumes.txt"

if [ ! -f "$VOLUME_FILE" ]; then
    echo "No volumes to restore"
    exit 0
fi

# Read each line and restore volume
while IFS=: read -r ip volume; do
    if [ ! -z "$ip" ] && [ ! -z "$volume" ]; then
        echo "Restoring $ip to volume $volume..."
        curl -s -X POST "http://${ip}:1400/MediaRenderer/RenderingControl/Control" \
          -H "Content-Type: text/xml; charset=utf-8" \
          -H "SOAPAction: urn:schemas-upnp-org:service:RenderingControl:1#SetVolume" \
          -d "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">
  <s:Body>
    <u:SetVolume xmlns:u=\"urn:schemas-upnp-org:service:RenderingControl:1\">
      <InstanceID>0</InstanceID>
      <Channel>Master</Channel>
      <DesiredVolume>${volume}</DesiredVolume>
    </u:SetVolume>
  </s:Body>
</s:Envelope>" > /dev/null
    fi
done < "$VOLUME_FILE"

# Clean up volume file
rm -f "$VOLUME_FILE"

echo "All volumes restored"
