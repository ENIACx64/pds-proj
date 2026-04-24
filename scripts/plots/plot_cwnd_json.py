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
                "This JSON does not contain congestion-window samples."
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


def parse_series_args(args: List[str]) -> List[Tuple[str, Path]]:
    if len(args) < 2 or len(args) % 2 != 0:
        raise ValueError(
            "You must provide one or more <label> <file.json> pairs."
        )

    pairs: List[Tuple[str, Path]] = []
    for i in range(0, len(args), 2):
        label = args[i]
        path = Path(args[i + 1])
        pairs.append((label, path))

    return pairs


def main() -> None:
    if len(sys.argv) < 5:
        print(
            "Usage:\n"
            "  python3 plot_cwnd_json.py "
            "\"<title>\" <output_file.png> "
            "<label1> <file1.json> [<label2> <file2.json> ...]"
        )
        sys.exit(1)

    title = sys.argv[1]
    output_file = Path(sys.argv[2])

    if output_file.suffix.lower() not in {
        ".png", ".pdf", ".svg", ".jpg", ".jpeg", ".webp"
    }:
        raise ValueError(
            f"Output file must be an image format, got: {output_file}"
        )

    series = parse_series_args(sys.argv[3:])

    plt.figure(figsize=(12, 6))

    for label, json_path in series:
        times, cwnd_kib = extract_cwnd_series(json_path)
        plt.plot(times, cwnd_kib, linewidth=2, label=label)
        print(
            f"{label}: min CWND = {min(cwnd_kib):.3f} KiB, "
            f"max CWND = {max(cwnd_kib):.3f} KiB"
        )

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