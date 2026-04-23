#!/usr/bin/env bash
set -euo pipefail

SCENARIO="${1:?usage: $0 <scenario> <cc>}"
CC="${2:?usage: $0 <scenario> <cc>}"

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
OUTDIR="$SCRIPT_DIR/results/${SCENARIO}_${CC}_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTDIR"

echo "Saving results to: $OUTDIR"

{
  echo "scenario=$SCENARIO"
  echo "cc=$CC"
  date
} > "$OUTDIR/meta.txt"

# sudo sysctl -w net.ipv4.tcp_congestion_control="$CC" | tee "$OUTDIR/sysctl.txt"

case "$SCENARIO" in
  baseline) "$SCRIPT_DIR/clear_tc.sh" ;;
  wifi) "$SCRIPT_DIR/scenarios/wifi.sh" ;;
  satellite) "$SCRIPT_DIR/scenarios/satellite.sh" ;;
  bufferbloat) "$SCRIPT_DIR/scenarios/bufferbloat.sh" ;;
  *) echo "Unknown scenario"; exit 1 ;;
esac

sudo ip netns exec ns_router tc qdisc show > "$OUTDIR/tc_qdisc.txt"

cleanup() {
  kill "${PING_PID:-}" 2>/dev/null || true
  kill "${TCPDUMP_PID:-}" 2>/dev/null || true
  kill "${SERVER_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT

sudo ip netns exec ns_server pkill iperf3 2>/dev/null || true
sudo ip netns exec ns_server iperf3 -s > "$OUTDIR/iperf_server.log" 2>&1 &
SERVER_PID=$!

sleep 1

sudo ip netns exec ns_router tcpdump -i veth_router2 -n -s 128 '(host 10.0.1.2 and host 10.0.2.2)' -w "$OUTDIR/capture.pcap" > /dev/null 2>&1 &
TCPDUMP_PID=$!

sleep 1

if [[ "$SCENARIO" == "bufferbloat" ]]; then
  sudo ip netns exec ns_client ping -i 0.2 10.0.2.2 > "$OUTDIR/ping_during_load.txt" 2>&1 &
  PING_PID=$!
  sleep 1
else
  sudo ip netns exec ns_client ping -c 20 10.0.2.2 | tee "$OUTDIR/ping.txt"
fi

sudo ip netns exec ns_client iperf3 -c 10.0.2.2 -t 60 -C "$CC" -J > "$OUTDIR/iperf_client.json"

if [[ "$SCENARIO" == "bufferbloat" ]]; then
  kill "$PING_PID" 2>/dev/null || true
  wait "$PING_PID" 2>/dev/null || true
fi

"$SCRIPT_DIR/clear_tc.sh"

echo "Done. Results stored in $OUTDIR"