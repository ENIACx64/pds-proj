#!/usr/bin/env bash
set -euo pipefail

# Arguments: chosen scenario, chosen congestion control algorithm
SCENARIO="${1:?usage: $0 <scenario> <cc>}"
CC="${2:?usage: $0 <scenario> <cc>}"

# Get the directory where this script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

OUTDIR="$SCRIPT_DIR/results/${SCENARIO}_${CC}_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTDIR"

echo "Saving results to: $OUTDIR"

# Save metadata
{
  echo "scenario=$SCENARIO"
  echo "cc=$CC"
  date
} > "$OUTDIR/meta.txt"

# Set congestion control and save confirmation
sudo sysctl -w net.ipv4.tcp_congestion_control="$CC" | tee "$OUTDIR/sysctl.txt"

# Apply scenario
case "$SCENARIO" in
  baseline) "$SCRIPT_DIR/clear_tc.sh" ;;
  wifi) "$SCRIPT_DIR/wifi.sh" ;;
  satellite) "$SCRIPT_DIR/satellite.sh" ;;
  bufferbloat) "$SCRIPT_DIR/bufferbloat.sh" ;;
  *) echo "Unknown scenario"; exit 1 ;;
esac

# Save qdisc state after scenario setup
sudo ip netns exec ns_router tc qdisc show > "$OUTDIR/tc_qdisc.txt"

# Stop any old iperf3 server
sudo ip netns exec ns_server pkill iperf3 2>/dev/null || true

# Start new iperf3 server
sudo ip netns exec ns_server iperf3 -s > "$OUTDIR/iperf_server.log" 2>&1 &
SERVER_PID=$!

sleep 1

# Start packet capture
sudo ip netns exec ns_router tcpdump -i any -n -s 128 -w "$OUTDIR/capture.pcap" > /dev/null 2>&1 &
TCPDUMP_PID=$!

sleep 1

# Run ping and save output
sudo ip netns exec ns_client ping -c 20 10.0.2.2 | tee "$OUTDIR/ping.txt"

# Run iperf3 and save output
sudo ip netns exec ns_client iperf3 -c 10.0.2.2 -t 15 -i 1 | tee "$OUTDIR/iperf_client.txt"

# Stop capture and server
kill "$TCPDUMP_PID" 2>/dev/null || true
kill "$SERVER_PID" 2>/dev/null || true

# Return ownership
sudo chown -R "$USER":"$USER" results

echo "Done. Results stored in $OUTDIR"