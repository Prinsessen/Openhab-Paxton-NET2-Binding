#!/bin/bash
# Reload OpenHAB sitemaps without full restart
# Usage: ./reload_sitemap.sh

echo "Reloading OpenHAB models (sitemaps, items, rules, things)..."
curl -X PUT http://localhost:8080/rest/service/org.openhab.core.model.core/reloadAllModelsOfType/sitemap
echo ""
echo "Sitemap reload triggered. Check UI in a few seconds."
