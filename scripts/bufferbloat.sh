#!/usr/bin/env bash
set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Now call clear_tc.sh using that absolute path
"$SCRIPT_DIR/clear_tc.sh"

ip netns exec ns_router tc qdisc add dev veth_router1 root handle 1: netem delay 10ms
ip netns exec ns_router tc qdisc add dev veth_router2 root handle 1: netem delay 10ms

ip netns exec ns_router tc qdisc add dev veth_router1 parent 1:1 handle 10: tbf rate 20mbit burst 32kbit latency 400ms
ip netns exec ns_router tc qdisc add dev veth_router2 parent 1:1 handle 10: tbf rate 20mbit burst 32kbit latency 400ms

echo "Bufferbloat profile applied: limited bandwidth with deep queue."