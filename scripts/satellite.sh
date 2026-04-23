#!/usr/bin/env bash
set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Now call clear_tc.sh using that absolute path
"$SCRIPT_DIR/clear_tc.sh"

sudo ip netns exec ns_router tc qdisc add dev veth_router1 root netem delay 300ms 50ms distribution normal
sudo ip netns exec ns_router tc qdisc add dev veth_router2 root netem delay 300ms 50ms distribution normal

echo "Satellite profile applied: ~600 ms RTT with jitter."