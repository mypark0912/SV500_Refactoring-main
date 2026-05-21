#!/bin/bash
LOG_FILE="/var/log/link-monitor.log"
INTERFACES="enp8s0"
GATEWAY="192.168.1.1"

log_event() {
    local iface="$1"
    local event="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    {
        echo "========================================"
        echo "[$timestamp] Link $event on $iface"
        echo "========================================"
        
        echo ""
        echo "--- system status ---"
        uptime
        cat /proc/loadavg
        free -m
        
        echo ""
        echo "--- all interfaces status ---"
        for i in $INTERFACES; do
            echo "[$i]"
            echo "  carrier: $(cat /sys/class/net/$i/carrier 2>/dev/null || echo 'N/A')"
            echo "  operstate: $(cat /sys/class/net/$i/operstate 2>/dev/null || echo 'N/A')"
            ip -br link show $i 2>/dev/null
        done
        
        echo ""
        echo "--- ethtool status ($iface) ---"
        ethtool $iface 2>&1 | grep -E "Speed|Duplex|Link detected"
        
        echo ""
        echo "--- hardware errors ($iface) ---"
        ethtool -S $iface 2>/dev/null | grep -iE "error|drop|collision|crc|fail"
        
        echo ""
        echo "--- dmesg (last 30 lines, network related) ---"
        dmesg | grep -iE "enp8s0|eth|link|phy|netdev" | tail -30
        
        echo ""
        echo "--- journalctl (last 30 lines, network related) ---"
        journalctl -u systemd-networkd --no-pager -n 30 2>/dev/null
        journalctl -k --no-pager -n 30 2>/dev/null | grep -iE "enp8s0|eth|link|phy"
        
        echo ""
        echo "--- ping test ---"
        echo "Gateway ($GATEWAY): $(ping -c1 -W2 $GATEWAY 2>&1 | grep -E 'time=|100% packet loss' || echo 'FAIL')"
        echo "External (8.8.8.8): $(ping -c1 -W2 8.8.8.8 2>&1 | grep -E 'time=|100% packet loss' || echo 'FAIL')"
        
        echo ""
        echo "--- routing table ---"
        ip route
        
        echo ""
        echo "--- interface statistics ($iface) ---"
        ip -s link show $iface 2>/dev/null | grep -A2 "RX:\|TX:"
        
        echo ""
    } >> "$LOG_FILE"
}

echo "$(date '+%Y-%m-%d %H:%M:%S') - Link monitor started for: $INTERFACES" >> "$LOG_FILE"

ip monitor link | while read line; do
    for iface in $INTERFACES; do
        if echo "$line" | grep -q "$iface"; then
            if echo "$line" | grep -q "state DOWN"; then
                log_event "$iface" "DOWN"
            elif echo "$line" | grep -q "state UP"; then
                log_event "$iface" "UP"
            fi
        fi
    done
done