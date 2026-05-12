"""Speed-over-60 calculator.

The math is unit-symmetric: at 60 mph you cover 1 mile/min, and at 60 km/h you
cover 1 km/min. Pass --unit to choose; mi is the default.

Usage:
    python speed_calc.py 75                       # 75 mph
    python speed_calc.py 110 --unit km            # 110 km/h
    python speed_calc.py 75 --trip 200            # plus savings on a 200 mi trip
    python speed_calc.py 110 --trip 300 --unit km # 300 km trip
    python speed_calc.py --export                 # write CSV + chart (mph)
    python speed_calc.py --export --unit km --min 60 --max 200 --step 5
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Optional


UNIT_LABELS = {
    "mi": {"speed": "mph", "dist": "mile", "dist_plural": "miles"},
    "km": {"speed": "km/h", "dist": "km", "dist_plural": "km"},
}


def stats(speed: float) -> dict:
    """Speed-baselined stats. Works for any unit where baseline = 60 unit/h."""
    return {
        "speed": speed,
        "dist_per_minute": speed / 60,
        "seconds_per_dist": 3600 / speed,
        "seconds_saved_per_dist": 60 - 3600 / speed,
    }


def format_duration(seconds: float) -> str:
    sign = "-" if seconds < 0 else ""
    s = abs(seconds)
    hours, rem = divmod(s, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if hours:
        parts.append(f"{int(hours)}h")
    if minutes or hours:
        parts.append(f"{int(minutes)}m")
    parts.append(f"{secs:.1f}s")
    return sign + " ".join(parts)


def print_query(speed: float, trip: Optional[float], unit: str) -> None:
    s = stats(speed)
    lbl = UNIT_LABELS[unit]
    print(f"Speed:                  {s['speed']:.2f} {lbl['speed']}")
    print(f"{lbl['dist_plural'].capitalize()} per minute:        {s['dist_per_minute']:.4f}")
    print(f"Seconds per {lbl['dist']}:        {s['seconds_per_dist']:.2f}")
    print(f"Sec saved per {lbl['dist']}:      {s['seconds_saved_per_dist']:+.2f}  (vs 60 {lbl['speed']})")
    if trip is not None:
        saved = trip * s["seconds_saved_per_dist"]
        trip_time = trip * s["seconds_per_dist"]
        print(f"Trip ({trip} {lbl['dist']}) time:  {format_duration(trip_time)}")
        print(f"Time saved on trip:     {format_duration(saved)}")


def export(min_v: int, max_v: int, step: int, out_dir: Path, unit: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    speeds = list(range(min_v, max_v + 1, step))
    rows = [stats(v) for v in speeds]
    lbl = UNIT_LABELS[unit]

    headers = {
        "speed": f"speed_{lbl['speed'].replace('/', '_per_')}",
        "dist_per_minute": f"{lbl['dist_plural']}_per_minute",
        "seconds_per_dist": f"seconds_per_{lbl['dist']}",
        "seconds_saved_per_dist": f"seconds_saved_per_{lbl['dist']}",
    }
    csv_path = out_dir / f"speeds_{unit}.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(list(headers.values()))
        for r in rows:
            writer.writerow([r[k] for k in headers])
    print(f"Wrote {csv_path}  ({len(rows)} rows)")

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed - skipping chart.")
        print("Install with: pip install matplotlib")
        return

    fig, ax = plt.subplots(figsize=(9, 5))
    saved = [r["seconds_saved_per_dist"] for r in rows]
    ax.plot(speeds, saved, linewidth=2.2, color="#2b6cb0")
    ax.fill_between(speeds, saved, alpha=0.15, color="#2b6cb0")
    ax.axhline(0, color="#888", linewidth=0.8, linestyle="--")
    ax.axvline(60, color="#888", linewidth=0.8, linestyle="--")
    ax.set_title(f"Seconds saved per {lbl['dist']} vs 60 {lbl['speed']}", fontsize=14, pad=12)
    ax.set_xlabel(f"Speed ({lbl['speed']})")
    ax.set_ylabel(f"Seconds saved per {lbl['dist']}")
    ax.grid(True, alpha=0.25)

    annotations_mi = (70, 80, 100)
    annotations_km = (90, 110, 130)
    marks = annotations_mi if unit == "mi" else annotations_km
    for mark in marks:
        if min_v <= mark <= max_v:
            y = 60 - 3600 / mark
            ax.annotate(
                f"{mark} {lbl['speed']}\n{y:.1f}s/{lbl['dist']}",
                xy=(mark, y),
                xytext=(8, -22),
                textcoords="offset points",
                fontsize=9,
                color="#2b6cb0",
            )

    png_path = out_dir / f"time_saved_{unit}.png"
    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    print(f"Wrote {png_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Speed-over-60 calculator (mi or km)")
    parser.add_argument("speed", nargs="?", type=float, help="speed to query (in chosen unit)")
    parser.add_argument("--trip", type=float, help="trip distance (in chosen unit)")
    parser.add_argument("--unit", choices=["mi", "km"], default="mi", help="mi = mph/miles, km = km/h/km (default mi)")
    parser.add_argument("--export", action="store_true", help="write CSV + chart")
    parser.add_argument("--min", dest="min_v", type=int, default=60, help="min speed for export (default 60)")
    parser.add_argument("--max", dest="max_v", type=int, default=120, help="max speed for export (default 120)")
    parser.add_argument("--step", type=int, default=1, help="step for export (default 1)")
    parser.add_argument("--out", type=Path, default=Path("."), help="output directory for --export")
    args = parser.parse_args()

    if args.export:
        export(args.min_v, args.max_v, args.step, args.out, args.unit)
        return 0

    if args.speed is None:
        parser.print_help()
        return 1

    print_query(args.speed, args.trip, args.unit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
