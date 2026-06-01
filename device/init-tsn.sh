#!/bin/sh
set -e

############################################
# User configuration
############################################

BR=br0

# Internal CPU-side bridge port
CPU_BR_PORT=sw0p1

# Daisy chain direction
UP_PORT=sw0p3      # PC / root 방향
DOWN_PORT=sw0p2    # 다음 장비 방향

# Management interface (현재 baseline 기준)
MGMT_IF=sw0ep

# root | nonroot | last
ROLE="nonroot"

# STP priorities
ROOT_PRIO=0
NONROOT_PRIO=4096
LAST_PRIO=8192

# Port path cost
CPU_COST=1
UP_COST=10
DOWN_COST=100

# Port priority
CPU_PORT_PRIO=0

# tc policing
ARP_RATE=100kbit
ARP_BURST=10k
BCAST_RATE=2mbit
BCAST_BURST=64k

############################################
# Helpers
############################################

log() {
  echo "[init-stp-daisy-final] $*"
}

cleanup_tc() {
  DEV="$1"
  tc qdisc del dev "$DEV" clsact 2>/dev/null || true
}

add_tc_rules() {
  DEV="$1"

  tc qdisc add dev "$DEV" clsact 2>/dev/null || true

  # 1) clearly invalid destination MAC drop
tc filter add dev "$DEV" ingress protocol all pref 10 flower \
    dst_mac 00:00:00:00:00:00 \
    action drop 2>/dev/null || true

  # 2) ARP policing (환경에서 확인된 문법)
  tc filter add dev "$DEV" ingress protocol arp pref 20 flower \
    action police rate "$ARP_RATE" burst "$ARP_BURST" conform-exceed drop \
    2>/dev/null || true

  # 3) Broadcast policing
  tc filter add dev "$DEV" ingress protocol all pref 30 flower \
    dst_mac ff:ff:ff:ff:ff:ff \
    action police rate "$BCAST_RATE" burst "$BCAST_BURST" conform-exceed drop \
    2>/dev/null || true
}

############################################
# Sanity checks
############################################

for DEV in "$BR" "$CPU_BR_PORT" "$UP_PORT" "$DOWN_PORT" "$MGMT_IF"; do
  ip link show "$DEV" >/dev/null 2>&1 || {
    echo "ERROR: interface $DEV not found"
    exit 1
  }
done

############################################
# Baseline keepalive
############################################

log "Bringing interfaces up"
ip link set dev "$BR" up 2>/dev/null || true
ip link set dev "$CPU_BR_PORT" up 2>/dev/null || true
ip link set dev "$UP_PORT" up 2>/dev/null || true
ip link set dev "$DOWN_PORT" up 2>/dev/null || true
ip link set dev "$MGMT_IF" up 2>/dev/null || true

############################################
# Enable STP
############################################

log "Enabling STP on $BR"
ip link set dev "$BR" type bridge stp_state 1

############################################
# Bridge priority by role
############################################

case "$ROLE" in
  root)
    log "Configuring ROOT bridge priority = $ROOT_PRIO"
    ip link set dev "$BR" type bridge priority "$ROOT_PRIO" 2>/dev/null || true
    ;;
  nonroot)
    log "Configuring NONROOT bridge priority = $NONROOT_PRIO"
    ip link set dev "$BR" type bridge priority "$NONROOT_PRIO" 2>/dev/null || true
    ;;
  last)
    log "Configuring LAST bridge priority = $LAST_PRIO"
    ip link set dev "$BR" type bridge priority "$LAST_PRIO" 2>/dev/null || true
    ;;
  *)
    echo "ERROR: ROLE must be root | nonroot | last"
    exit 1
    ;;
esac

############################################
# Port tuning
############################################

log "Configuring CPU/internal port ($CPU_BR_PORT)"
bridge link set dev "$CPU_BR_PORT" cost "$CPU_COST" 2>/dev/null || true
bridge link set dev "$CPU_BR_PORT" priority "$CPU_PORT_PRIO" 2>/dev/null || true

log "Configuring upstream/downstream port costs"
bridge link set dev "$UP_PORT" cost "$UP_COST" 2>/dev/null || true
bridge link set dev "$DOWN_PORT" cost "$DOWN_COST" 2>/dev/null || true

############################################
# tc protection
############################################

log "Applying tc protection"
cleanup_tc "$UP_PORT"
cleanup_tc "$DOWN_PORT"

add_tc_rules "$UP_PORT"
add_tc_rules "$DOWN_PORT"

############################################
# Status
############################################

log "Bridge state"
bridge link show || true

log "Bridge VLAN"
bridge vlan show || true

log "FDB snapshot"
bridge fdb show || true

log "tc filters"
tc -s filter show dev "$UP_PORT" ingress 2>/dev/null || true
tc -s filter show dev "$DOWN_PORT" ingress 2>/dev/null || true

log "Done"
