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


def extract_cwnd_series(path: Path) -> Tuple[List[float], List[float]]:
    data = load_json(path)

    if "intervals" not in data:
        raise ValueError(f"{path}: missing 'intervals' in JSON")

    times: List[float] = []
    cwnd_kib: List[float] = []

    for idx, interval in enumerate(data["intervals"]):
        streams = interval.get("streams", [])
        if not streams:
            continue

        stream0 = streams[0]

        if "snd_cwnd" not in stream0:
            raise ValueError(
                f"{path}: missing 'snd_cwnd' in interval {idx}. "
                "This iperf3 JSON does not appear to contain CWND samples."
            )

        end_time = stream0.get("end")
        if end_time is None:
            end_time = interval.get("sum", {}).get("end")
        if end_time is None:
            raise ValueError(f"{path}: missing interval end time at interval {idx}")

        cwnd_bytes = stream0["snd_cwnd"]

        times.append(float(end_time))
        cwnd_kib.append(float(cwnd_bytes) / 1024.0)

    if not times:
        raise ValueError(f"{path}: no CWND samples found")

    return times, cwnd_kib


def main() -> None:
    if len(sys.argv) != 5:
        print(
            "Usage:\n"
            "  python plot_cwnd_json.py "
            "\"<title>\" <output_file.png> <cubic.json> <bbr.json>"
        )
        sys.exit(1)

    title = sys.argv[1]
    output_file = Path(sys.argv[2])
    cubic_json = Path(sys.argv[3])
    bbr_json = Path(sys.argv[4])

    t_cubic, cwnd_cubic = extract_cwnd_series(cubic_json)
    t_bbr, cwnd_bbr = extract_cwnd_series(bbr_json)

    plt.figure(figsize=(12, 6))
    plt.plot(t_cubic, cwnd_cubic, linewidth=2, label="CUBIC")
    plt.plot(t_bbr, cwnd_bbr, linewidth=2, label="BBR")

    plt.title(title, fontsize=16, weight="bold")
    plt.xlabel("Time [s]", fontsize=13)
    plt.ylabel("Congestion Window [KiB]", fontsize=13)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=150)
    print(f"Saved plot to {output_file}")


if __name__ == "__main__":
    main()