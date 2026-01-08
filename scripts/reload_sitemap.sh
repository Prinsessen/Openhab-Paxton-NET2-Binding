#!/bin/bash
# Reload OpenHAB sitemap model without full restart
# Usage: ./reload_sitemap.sh

echo "Reloading sitemap model via OpenHAB console..."
(
  echo "habopen"
  sleep 1
  echo "bundle:restart 215"
  sleep 2
  echo "exit"
) | ssh -p 8101 -o StrictHostKeyChecking=no -o ConnectTimeout=5 openhab@localhost 2>/dev/null

if [ $? -eq 0 ]; then
  echo "✓ Sitemap model reloaded. Check your UI now."
else
  echo "✗ Console command failed. Falling back to full restart..."
  sudo systemctl restart openhab
  echo "Restart initiated. Wait ~30 seconds for OpenHAB to come online."
fi
