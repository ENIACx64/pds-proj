#!/usr/bin/env bash
set -euo pipefail

ip netns del ns_client 2>/dev/null || true
ip netns del ns_router 2>/dev/null || true
ip netns del ns_server 2>/dev/null || true

echo "Topology removed."