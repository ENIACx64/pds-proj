#!/usr/bin/env bash
set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Now call clear_tc.sh using that absolute path
"$SCRIPT_DIR/../clear_tc.sh"

# 4% packet loss, 20ms delay
sudo ip netns exec ns_router tc qdisc add dev veth_router1 root netem delay 10ms
sudo ip netns exec ns_router tc qdisc add dev veth_router2 root netem delay 10ms loss 4%

echo "Wi-Fi profile applied: delay 20ms, loss 4% on both router interfaces."