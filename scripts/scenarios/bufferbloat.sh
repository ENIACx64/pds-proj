#!/usr/bin/env bash
set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Now call clear_tc.sh using that absolute path
"$SCRIPT_DIR/../clear_tc.sh"

# 20Mbit bottleneck with a deep (1000 packet) buffer to induce bloat
for dev in veth_router1 veth_router2; do
    sudo ip netns exec ns_router tc qdisc add dev "$dev" root handle 1: htb default 10
    sudo ip netns exec ns_router tc class add dev "$dev" parent 1: classid 1:10 htb rate 20mbit
    sudo ip netns exec ns_router tc qdisc add dev "$dev" parent 1:10 handle 20: netem delay 10ms limit 1000
done

echo "Bufferbloat profile applied: 20mbit limit, 10ms base delay, and 1000-packet deep queue."