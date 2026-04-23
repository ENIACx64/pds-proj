#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np
import matplotlib.pyplot as plt


LINE_RE = re.compile(
    r"""
    ^\[\s*\d+\]\s+
    (?P<t0>\d+\.\d+)-(?P<t1>\d+\.\d+)\s+sec\s+
    .*?
    (?P<cwnd>\d+(\.\d+)?)\s+
    (?P<unit>KBytes|MBytes|Bytes)\s*$
    """,
    re.VERBOSE,
)


def cwnd_to_kib(value: float, unit: str) -> float:
    if unit == "Bytes":
        return value / 1024.0
    if unit == "KBytes":
        return value
    if unit == "MBytes":
        return value * 1024.0
    raise ValueError(f"Unsupported unit: {unit}")


def parse_iperf_cwnd(path: Path) -> Tuple[np.ndarray, np.ndarray]:
    times: List[float] = []
    cwnds: List[float] = []

    for line in path.read_text(errors="ignore").splitlines():
        m = LINE_RE.match(line.strip())
        if not m:
            continue

        t1 = float(m.group("t1"))
        cwnd_val = float(m.group("cwnd"))
        cwnd_unit = m.group("unit")

        times.append(t1)
        cwnds.append(cwnd_to_kib(cwnd_val, cwnd_unit))

    if not times:
        raise ValueError(f"No CWND samples found in {path}")

    return np.array(times), np.array(cwnds)


def align_runs(files: List[Path]) -> Tuple[np.ndarray, np.ndarray]:
    parsed = [parse_iperf_cwnd(f) for f in files]

    min_len = min(len(times) for times, _ in parsed)
    ref_times = parsed[0][0][:min_len]

    matrix = np.vstack([cwnd[:min_len] for _, cwnd in parsed])
    return ref_times, matrix


def mean_std(files: List[Path]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    times, matrix = align_runs(files)
    mean = np.mean(matrix, axis=0)
    std = np.std(matrix, axis=0)
    return times, mean, std


def parse_file_list(arg: str) -> List[Path]:
    # files are passed as a semicolon-separated list
    return [Path(x) for x in arg.split(";") if x.strip()]


def main() -> None:
    if len(sys.argv) != 6:
        print(
            "Usage:\n"
            "  python plot_cwnd_compare.py "
            "\"<title>\" <output.png> "
            "\"<cubic1.txt;cubic2.txt;...>\" "
            "\"<bbr1.txt;bbr2.txt;...>\" "
            "<show_std:true|false>"
        )
        sys.exit(1)

    title = sys.argv[1]
    output = Path(sys.argv[2])
    cubic_files = parse_file_list(sys.argv[3])
    bbr_files = parse_file_list(sys.argv[4])
    show_std = sys.argv[5].lower() == "true"

    if not cubic_files:
        raise ValueError("No CUBIC files given")
    if not bbr_files:
        raise ValueError("No BBR files given")

    t_c, mean_c, std_c = mean_std(cubic_files)
    t_b, mean_b, std_b = mean_std(bbr_files)

    min_len = min(len(t_c), len(t_b))
    t = t_c[:min_len]
    mean_c = mean_c[:min_len]
    std_c = std_c[:min_len]
    mean_b = mean_b[:min_len]
    std_b = std_b[:min_len]

    plt.figure(figsize=(12, 6))
    plt.plot(t, mean_c, linewidth=2, label="CUBIC")
    plt.plot(t, mean_b, linewidth=2, label="BBR")

    if show_std:
        plt.fill_between(t, mean_c - std_c, mean_c + std_c, alpha=0.18)
        plt.fill_between(t, mean_b - std_b, mean_b + std_b, alpha=0.18)

    plt.title(title, fontsize=16, weight="bold")
    plt.xlabel("Time [s]", fontsize=14)
    plt.ylabel("Congestion Window [KiB]", fontsize=14)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    print(f"Saved plot to {output}")


if __name__ == "__main__":
    main()