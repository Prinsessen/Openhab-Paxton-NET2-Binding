#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║         Beacon Temperature Monitor (10 minutes)                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Time         Beacon        Temperature    Change"
echo "─────────────────────────────────────────────────────────────────────"

# Monitor for 10 minutes
timeout 600 tail -f /var/log/openhab/events.log | while read line; do
    # Look for beacon temperature changes
    if echo "$line" | grep -q "Beacon.*Temperature.*changed"; then
        timestamp=$(echo "$line" | grep -oP '\d{2}:\d{2}:\d{2}')
        beacon=$(echo "$line" | grep -oP 'Beacon\d')
        temp=$(echo "$line" | grep -oP 'to \K[0-9.]+ °C')
        from=$(echo "$line" | grep -oP 'from \K[0-9.]+ °C')
        
        if [ ! -z "$temp" ]; then
            if [ ! -z "$from" ]; then
                printf "%-12s %-13s %-14s (was %s)\n" "$timestamp" "$beacon" "$temp" "$from"
            else
                printf "%-12s %-13s %-14s\n" "$timestamp" "$beacon" "$temp"
            fi
        fi
    fi
done

echo ""
echo "Monitoring complete."
