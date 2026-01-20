#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║         Beacon Monitor - All Channels (1 hour)                        ║"
echo "║  Watching: MAC, Name, RSSI, Distance, Battery, LowBattery,            ║"
echo "║            Temperature, Humidity for all 3 beacons                    ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

timeout 3600 tail -f /var/log/openhab/events.log | while read line; do
    if echo "$line" | grep -q "Vehicle10_Beacon"; then
        timestamp=$(echo "$line" | awk '{print $1, $2}')
        
        # Extract beacon number and channel
        if echo "$line" | grep -qE "Vehicle10_Beacon[1-3]_"; then
            beacon=$(echo "$line" | grep -oP 'Vehicle10_Beacon\K[1-3]')
            channel=$(echo "$line" | grep -oP 'Vehicle10_Beacon[1-3]_\K[A-Za-z]+')
            
            # Extract old and new values
            old_value=$(echo "$line" | grep -oP 'from \K[^ ]+' | head -1)
            new_value=$(echo "$line" | grep -oP 'to \K[^ ]+' | head -1)
            
            # Color codes
            CYAN='\033[0;36m'
            GREEN='\033[0;32m'
            YELLOW='\033[1;33m'
            RED='\033[0;31m'
            BLUE='\033[0;34m'
            NC='\033[0m' # No Color
            
            # Choose color based on beacon
            case $beacon in
                1) COLOR=$GREEN ;;
                2) COLOR=$YELLOW ;;
                3) COLOR=$BLUE ;;
            esac
            
            printf "${CYAN}%s${NC} │ ${COLOR}Beacon %s${NC} │ %-12s │ %10s → %-10s\n" \
                "$timestamp" "$beacon" "$channel" "$old_value" "$new_value"
        fi
    fi
done

echo ""
echo "Monitoring complete (1 hour elapsed)"
