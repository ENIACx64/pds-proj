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
    """
    Extract CWND samples from iperf3 JSON output.

    Expected per-interval field:
        intervals[i]["streams"][0]["snd_cwnd"]

    snd_cwnd is reported in bytes.
    Returns:
        times     -> interval end times in seconds
        cwnd_kib  -> congestion window in KiB
    """
    data = load_json(path)

    intervals = data.get("intervals")
    if not intervals:
        raise ValueError(f"{path}: missing or empty 'intervals'")

    times: List[float] = []
    cwnd_kib: List[float] = []

    for idx, interval in enumerate(intervals):
        streams = interval.get("streams", [])
        if not streams:
            continue

        stream = streams[0]

        if "snd_cwnd" not in stream:
            raise ValueError(
                f"{path}: interval {idx} has no 'snd_cwnd'. "
                "This iperf3 JSON does not contain congestion-window samples."
            )

        end_time = stream.get("end")
        if end_time is None:
            end_time = interval.get("sum", {}).get("end")
        if end_time is None:
            raise ValueError(f"{path}: interval {idx} has no end time")

        cwnd_bytes = stream["snd_cwnd"]

        times.append(float(end_time))
        cwnd_kib.append(float(cwnd_bytes) / 1024.0)

    if not times:
        raise ValueError(f"{path}: no CWND samples found")

    return times, cwnd_kib


def style_axis(ax, ylabel: str) -> None:
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, linestyle="--", alpha=0.5)


def main() -> None:
    if len(sys.argv) != 5:
        print(
            "Usage:\n"
            "  python3 plot_cwnd_json_twopanel.py "
            "\"<title>\" <output_file.png> <cubic.json> <bbr.json>"
        )
        sys.exit(1)

    title = sys.argv[1]
    output_file = Path(sys.argv[2])
    cubic_json = Path(sys.argv[3])
    bbr_json = Path(sys.argv[4])

    t_cubic, cwnd_cubic = extract_cwnd_series(cubic_json)
    t_bbr, cwnd_bbr = extract_cwnd_series(bbr_json)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 8), sharex=True, constrained_layout=True
    )

    fig.suptitle(title, fontsize=18, weight="bold")

    ax1.plot(t_cubic, cwnd_cubic, linewidth=2, label="CUBIC")
    style_axis(ax1, "CUBIC CWND [KiB]")
    ax1.legend()

    ax2.plot(t_bbr, cwnd_bbr, linewidth=2, label="BBR")
    style_axis(ax2, "BBR CWND [KiB]")
    ax2.set_xlabel("Time [s]", fontsize=12)
    ax2.legend()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=150)
    print(f"Saved plot to {output_file}")

    print(
        f"CUBIC range: min={min(cwnd_cubic):.3f} KiB, "
        f"max={max(cwnd_cubic):.3f} KiB"
    )
    print(
        f"BBR range:   min={min(cwnd_bbr):.3f} KiB, "
        f"max={max(cwnd_bbr):.3f} KiB"
    )


if __name__ == "__main__":
    main()