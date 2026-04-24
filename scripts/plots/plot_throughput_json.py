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
            "  python3 plot_throughput_json.py "
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
        times, throughput_mbps = extract_throughput_series(json_path)
        plt.plot(times, throughput_mbps, linewidth=2, label=label)
        avg = sum(throughput_mbps) / len(throughput_mbps)
        print(f"{label}: average throughput = {avg:.3f} Mbps")

    plt.title(title, fontsize=18, weight="bold")
    plt.xlabel("Time [s]", fontsize=12)
    plt.ylabel("Throughput [Mbps]", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=150)
    print(f"Saved plot to {output_file}")


if __name__ == "__main__":
    main()