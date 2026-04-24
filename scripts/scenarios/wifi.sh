#!/usr/bin/env bash
set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Now call clear_tc.sh using that absolute path
"$SCRIPT_DIR/../clear_tc.sh"

# Apply to both interfaces for bidirectional 50Mbps, 10ms delay, and 4% loss
for dev in veth_router1 veth_router2; do
    sudo ip netns exec ns_router tc qdisc add dev "$dev" root handle 1: htb default 10
    sudo ip netns exec ns_router tc class add dev "$dev" parent 1: classid 1:10 htb rate 50mbit
    sudo ip netns exec ns_router tc qdisc add dev "$dev" parent 1:10 handle 20: netem delay 10ms loss 4%
done

echo "Wi-Fi profile applied: delay 20ms, loss 4% on both router interfaces."