#!/bin/bash
# Quick OpenHAB restart (faster than full systemctl restart)
# Usage: ./reload_sitemap.sh

echo "Restarting OpenHAB (this takes ~30 seconds)..."
sudo systemctl restart openhab
echo "Restart initiated. Wait for OpenHAB to come back online..."
