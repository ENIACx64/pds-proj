#!/usr/bin/env bash
set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Now call clear_tc.sh using that absolute path
"$SCRIPT_DIR/../clear_tc.sh"

# Apply 300ms delay + jitter to each side to reach 600ms+ RTT total
for dev in veth_router1 veth_router2; do
    sudo ip netns exec ns_router tc qdisc add dev "$dev" root handle 1: htb default 10
    sudo ip netns exec ns_router tc class add dev "$dev" parent 1: classid 1:10 htb rate 100mbit
    sudo ip netns exec ns_router tc qdisc add dev "$dev" parent 1:10 handle 20: netem delay 300ms 50ms distribution normal limit 2000
done

echo "Satellite profile applied: ~600 ms RTT with jitter."