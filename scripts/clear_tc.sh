#!/usr/bin/env bash
set -euo pipefail

ip netns exec ns_router tc qdisc del dev veth_router1 root 2>/dev/null || true
ip netns exec ns_router tc qdisc del dev veth_router2 root 2>/dev/null || true

echo "tc rules cleared."