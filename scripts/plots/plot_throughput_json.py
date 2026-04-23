#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_throughput_series(path: Path) -> Tuple[List[float], List[float]]:
    """
    Extract per-interval throughput from iperf3 JSON output.

    Expected source:
        intervals[i]["streams"][0]["bits_per_second"]

    Returns:
        times       -> interval end times in seconds
        throughput  -> throughput in Mbps
    """
    data = load_json(path)

    intervals = data.get("intervals")
    if not intervals:
        raise ValueError(f"{path}: missing or empty 'intervals'")

    times: List[float] = []
    throughput_mbps: List[float] = []

    for idx, interval in enumerate(intervals):
        streams = interval.get("streams", [])
        if not streams:
            continue

        stream = streams[0]

        bps = stream.get("bits_per_second")
        if bps is None:
            raise ValueError(
                f"{path}: interval {idx} has no 'bits_per_second'"
            )

        end_time = stream.get("end")
        if end_time is None:
            end_time = interval.get("sum", {}).get("end")
        if end_time is None:
            raise ValueError(f"{path}: interval {idx} has no end time")

        times.append(float(end_time))
        throughput_mbps.append(float(bps) / 1e6)

    if not times:
        raise ValueError(f"{path}: no throughput samples found")

    return times, throughput_mbps


def main() -> None:
    if len(sys.argv) != 5:
        print(
            "Usage:\n"
            "  python3 plot_throughput_json.py "
            "\"<title>\" <output_file.png> <cubic.json> <bbr.json>"
        )
        sys.exit(1)

    title = sys.argv[1]
    output_file = Path(sys.argv[2])
    cubic_json = Path(sys.argv[3])
    bbr_json = Path(sys.argv[4])

    t_cubic, thr_cubic = extract_throughput_series(cubic_json)
    t_bbr, thr_bbr = extract_throughput_series(bbr_json)

    plt.figure(figsize=(12, 6))
    plt.plot(t_cubic, thr_cubic, linewidth=2, label="CUBIC")
    plt.plot(t_bbr, thr_bbr, linewidth=2, label="BBR")

    plt.title(title, fontsize=18, weight="bold")
    plt.xlabel("Time [s]", fontsize=12)
    plt.ylabel("Throughput [Mbps]", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=150)
    print(f"Saved plot to {output_file}")

    print(
        f"CUBIC average throughput: {sum(thr_cubic) / len(thr_cubic):.3f} Mbps"
    )
    print(
        f"BBR average throughput:   {sum(thr_bbr) / len(thr_bbr):.3f} Mbps"
    )


if __name__ == "__main__":
    main()