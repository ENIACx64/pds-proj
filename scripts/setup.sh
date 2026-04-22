#!/usr/bin/env bash
set -euo pipefail

# Cleanup old state if it exists
ip netns del ns_client 2>/dev/null || true
ip netns del ns_router 2>/dev/null || true
ip netns del ns_server 2>/dev/null || true

# Create namespaces
ip netns add ns_client
ip netns add ns_router
ip netns add ns_server

# Create veth pairs
ip link add veth_client type veth peer name veth_router1
ip link add veth_server type veth peer name veth_router2

# Move interfaces into namespaces
ip link set veth_client netns ns_client
ip link set veth_router1 netns ns_router
ip link set veth_server netns ns_server
ip link set veth_router2 netns ns_router

# Assign IP addresses
ip netns exec ns_client ip addr add 10.0.1.2/24 dev veth_client
ip netns exec ns_router ip addr add 10.0.1.1/24 dev veth_router1

ip netns exec ns_router ip addr add 10.0.2.1/24 dev veth_router2
ip netns exec ns_server ip addr add 10.0.2.2/24 dev veth_server

# Bring loopback up
ip netns exec ns_client ip link set lo up
ip netns exec ns_router ip link set lo up
ip netns exec ns_server ip link set lo up

# Bring interfaces up
ip netns exec ns_client ip link set veth_client up
ip netns exec ns_router ip link set veth_router1 up
ip netns exec ns_router ip link set veth_router2 up
ip netns exec ns_server ip link set veth_server up

# Add routes
ip netns exec ns_client ip route add default via 10.0.1.1
ip netns exec ns_server ip route add default via 10.0.2.1

# Enable forwarding in router namespace
ip netns exec ns_router sysctl -w net.ipv4.ip_forward=1

echo "Topology created successfully."
echo "Try: sudo ip netns exec ns_client ping -c 3 10.0.2.2"

echo "Testing client -> router"
ip netns exec ns_client ping -c 1 10.0.1.1

echo "Testing server -> router"
ip netns exec ns_server ping -c 1 10.0.2.1

echo "Testing client -> server"
ip netns exec ns_client ping -c 1 10.0.2.2

echo "Topology OK"