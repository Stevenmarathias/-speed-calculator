"""Speed-over-60 calculator.

Usage:
    python speed_calc.py 75                  # show stats for 75 mph
    python speed_calc.py 75 --trip 200       # also show savings on a 200-mile trip
    python speed_calc.py --export            # write speeds.csv and time_saved.png
    python speed_calc.py --export --min 60 --max 120 --step 1
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Optional


def stats(mph: float) -> dict:
    """Return speed stats for a given mph, baselined against 60 mph."""
    return {
        "mph": mph,
        "miles_per_minute": mph / 60,
        "seconds_per_mile": 3600 / mph,
        "seconds_saved_per_mile": 60 - 3600 / mph,
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


def print_query(mph: float, trip: Optional[float]) -> None:
    s = stats(mph)
    print(f"Speed:               {s['mph']:.2f} mph")
    print(f"Miles per minute:    {s['miles_per_minute']:.4f}")
    print(f"Seconds per mile:    {s['seconds_per_mile']:.2f}")
    print(f"Sec saved per mile:  {s['seconds_saved_per_mile']:+.2f}  (vs 60 mph)")
    if trip is not None:
        saved = trip * s["seconds_saved_per_mile"]
        trip_time = trip * s["seconds_per_mile"]
        print(f"Trip ({trip} mi) time: {format_duration(trip_time)}")
        print(f"Time saved on trip:  {format_duration(saved)}")


def export(min_mph: int, max_mph: int, step: int, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    speeds = list(range(min_mph, max_mph + 1, step))
    rows = [stats(v) for v in speeds]

    csv_path = out_dir / "speeds.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {csv_path}  ({len(rows)} rows)")

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed - skipping chart.")
        print("Install with: pip install matplotlib")
        return

    fig, ax = plt.subplots(figsize=(9, 5))
    saved = [r["seconds_saved_per_mile"] for r in rows]
    ax.plot(speeds, saved, linewidth=2.2, color="#2b6cb0")
    ax.fill_between(speeds, saved, alpha=0.15, color="#2b6cb0")
    ax.axhline(0, color="#888", linewidth=0.8, linestyle="--")
    ax.axvline(60, color="#888", linewidth=0.8, linestyle="--")
    ax.set_title("Seconds saved per mile vs 60 mph", fontsize=14, pad=12)
    ax.set_xlabel("Speed (mph)")
    ax.set_ylabel("Seconds saved per mile")
    ax.grid(True, alpha=0.25)

    for mark in (70, 80, 100):
        if min_mph <= mark <= max_mph:
            y = 60 - 3600 / mark
            ax.annotate(
                f"{mark} mph\n{y:.1f}s/mi",
                xy=(mark, y),
                xytext=(8, -22),
                textcoords="offset points",
                fontsize=9,
                color="#2b6cb0",
            )

    png_path = out_dir / "time_saved.png"
    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    print(f"Wrote {png_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Speed-over-60 calculator")
    parser.add_argument("speed", nargs="?", type=float, help="speed in mph to query")
    parser.add_argument("--trip", type=float, help="trip distance in miles")
    parser.add_argument("--export", action="store_true", help="write CSV + chart")
    parser.add_argument("--min", dest="min_mph", type=int, default=60, help="min mph for export (default 60)")
    parser.add_argument("--max", dest="max_mph", type=int, default=120, help="max mph for export (default 120)")
    parser.add_argument("--step", type=int, default=1, help="step for export (default 1)")
    parser.add_argument("--out", type=Path, default=Path("."), help="output directory for --export")
    args = parser.parse_args()

    if args.export:
        export(args.min_mph, args.max_mph, args.step, args.out)
        return 0

    if args.speed is None:
        parser.print_help()
        return 1

    print_query(args.speed, args.trip)
    return 0


if __name__ == "__main__":
    sys.exit(main())
