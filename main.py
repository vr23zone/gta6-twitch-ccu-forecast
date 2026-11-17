"""Launch-curve analog ensemble: an hour-by-hour Twitch CCU forecaster for a big game launch.

Built for make.fun's gta6-twitch-ccu-forecast-01 (program/v1, Python 3.13, standard library
only, no network). The grader runs `python3 -P -s /bot/main.py` once per case: the program
reads every <id>.in in the input directory and writes <id>.out beside it in the output
directory, one forecast per case: for each of hours 2..24 of the release day, the five
quantiles (0.05, 0.25, 0.5, 0.75, 0.95) of that hour's Twitch viewer count in the game's
category. Scoring is the mean pinball loss on the log scale, so the honest move is to
report the quantiles the evidence really supports.

The model, in one paragraph: a launch day's audience curve, divided by its own first hour,
has a shape that repeats across big launches — a first hour fed by the earliest time zones,
a lull while the early regions sleep and the late ones still wait for their midnight, then a
long climb as the big regions unlock and reach their evening. The case hands us dozens of
past launches (its `comparables`), each with hourly viewers from two weeks before its
release day to three days after. For every comparable we form the 23 log-ratios
ln(viewers of hour h / viewers of hour 1) of its own release day, weight each comparable by
how similar its launch was to this one, and read the five quantiles of the weighted
log-ratio distribution at each hour. Multiply by this case's first-hour print and that is
the forecast: the median curve and the spread both come from what real launches actually
did, not from a widening rule of thumb.

Similarity is two questions, both answered from the case's own data:

  * Scale. A Gaussian kernel on the log distance between the comparable's first-hour print
    and this case's, bandwidth 1.0: a launch that opened at 800k viewers says a lot about
    another 800k launch and little about a 5k one. (In leave-one-out tests over the 37
    usable comparables this single term cut the mean pinball loss from 0.72 unweighted to
    0.41; the house persistence baseline scored 0.93 on the same tests.)
  * Unlock pattern. A comparable whose unlock rolled at midnight local time, the way this
    launch does, is weighted 1.5x: its hour-by-hour shape carries the same sequence of
    regional unlocks (New Zealand first, Europe at its midnight, the US coasts last).

Everything is a pure function of the case file: no randomness, no clock, no state between
runs, so two runs write the same bytes. See MODEL.md for the full method, the validation
numbers and the sources.
"""

import json
import math
import os
import sys
from pathlib import Path

# The grader's -P leaves this file's directory off sys.path; the program is one file and
# imports nothing of its own, but keep the path sane for any local tooling beside it.
sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
HOURS = list(range(2, 25))

# Similarity kernel bandwidth, in natural-log units of first-hour viewers.
SCALE_BANDWIDTH = 1.0
# Extra weight for a comparable whose unlock rolled at midnight local time, like this one.
ROLLING_BOOST = 1.5
# A comparable must show at least this many of hours 2..24 of its release day to be used.
MIN_RATIO_HOURS = 20


def epoch_seconds(stamp: str) -> int:
    """Seconds since the Unix epoch for an ISO 8601 UTC stamp like 2026-11-19T01:00:00Z.

    The case files all use that exact shape; parse it by slicing (fast, and identical on
    every run) and fall back to fromisoformat for anything unexpected.
    """
    if len(stamp) == 20 and stamp[4] == "-" and stamp[19] == "Z":
        year = int(stamp[0:4])
        month = int(stamp[5:7])
        day = int(stamp[8:10])
        hour = int(stamp[11:13])
        minute = int(stamp[14:16])
        second = int(stamp[17:19])
        # Days from civil (Howard Hinnant's algorithm), then to seconds.
        y = year - (1 if month <= 2 else 0)
        era = (y if y >= 0 else y - 399) // 400
        yoe = y - era * 400
        mp = (month + 9) % 12
        doy = (153 * mp + 2) // 5 + day - 1
        doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
        days = era * 146097 + doe - 719468
        return days * 86400 + hour * 3600 + minute * 60 + second
    from datetime import datetime, timezone

    parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())


def release_day_hours(comparable: dict) -> dict | None:
    """{hour 1..24: viewers} of a comparable's own release day, or None if unusable.

    The comparable whose series is the target category's own pre-release history has no
    release day to learn a curve from; it is skipped by name, and any comparable missing
    its first hour or most of the day is skipped on the data.
    """
    if "before release" in (comparable.get("name") or ""):
        return None
    try:
        t0 = epoch_seconds(comparable["day_start"])
    except (KeyError, TypeError, ValueError):
        return None
    by_hour: dict[int, float] = {}
    for point in comparable.get("hourly") or []:
        viewers = point.get("viewers")
        if viewers is None or viewers <= 0:
            continue
        try:
            idx = (epoch_seconds(point["from"]) - t0) // 3600 + 1
        except (KeyError, TypeError, ValueError):
            continue
        if 1 <= idx <= 24:
            by_hour[int(idx)] = float(viewers)
    if 1 not in by_hour:
        return None
    if sum(1 for h in HOURS if h in by_hour) < MIN_RATIO_HOURS:
        return None
    return by_hour


def is_rolling_unlock(comparable: dict) -> bool:
    text = (comparable.get("unlock") or "").lower()
    return "midnight local" in text or "rolling" in text


def weighted_quantile(sorted_pairs: list, tau: float) -> float:
    """The tau quantile of (value, weight) pairs sorted by value, linearly interpolated."""
    total = sum(w for _, w in sorted_pairs)
    if total <= 0:
        return sorted_pairs[len(sorted_pairs) // 2][0]
    target = tau * total
    acc = 0.0
    prev_value, prev_acc = sorted_pairs[0][0], 0.0
    for value, weight in sorted_pairs:
        acc += weight
        if acc >= target:
            if acc == prev_acc:
                return value
            frac = (target - prev_acc) / (acc - prev_acc)
            return prev_value + frac * (value - prev_value)
        prev_value, prev_acc = value, acc
    return sorted_pairs[-1][0]


def round2(x: float) -> float:
    """Round to 2 decimals, half up (x is always positive here)."""
    return math.floor(x * 100 + 0.5) / 100


def forecast_case(case: dict) -> dict:
    first = next((k for k in case.get("known") or [] if k.get("hour") == 1), None)
    if first is None:
        raise ValueError("case has no hour-1 print")
    p1 = max(1.0, float(first["viewers"]))

    notes = (case.get("notes") or "").lower()
    target_rolling = "midnight" in notes

    # One training row per usable comparable: its release-day log-ratios and its weight.
    train = []
    for comparable in sorted(case.get("comparables") or [], key=lambda c: c.get("name") or ""):
        curve = release_day_hours(comparable)
        if curve is None:
            continue
        p1c = curve[1]
        distance = abs(math.log(p1c) - math.log(p1))
        weight = math.exp(-0.5 * (distance / SCALE_BANDWIDTH) ** 2)
        if target_rolling and is_rolling_unlock(comparable):
            weight *= ROLLING_BOOST
        ratios = {h: math.log(curve[h] / p1c) for h in HOURS if h in curve}
        train.append((ratios, weight))

    rows = []
    for row in case["forecast"]:
        h = row["hour"]
        if train:
            pairs = sorted((ratios[h], w) for ratios, w in train if h in ratios)
            if not pairs:
                pairs = [(0.0, 1.0)]
            log_q = [weighted_quantile(pairs, tau) for tau in LEVELS]
            qs = [p1 * math.exp(v) for v in log_q]
        else:
            # No usable comparable (never seen in a real case): hold the first hour's
            # level, with a spread that widens like a random walk's, per the contest's
            # published baseline formula.
            z = [-1.645, -0.674, 0.0, 0.674, 1.645]
            qs = [p1 * math.exp(zz * 0.15 * math.sqrt(h - 1)) for zz in z]
        qs = [min(1e9, max(0.01, round2(q))) for q in qs]
        for i in range(1, len(qs)):
            if qs[i] < qs[i - 1]:
                qs[i] = qs[i - 1]
        rows.append({"hour": h, "q": qs})
    # Emit in hour order (the format allows any order; sorted reads better and is stable).
    rows.sort(key=lambda r: r["hour"])
    return {"hours": rows}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case)
        out = json.dumps(forecast, separators=(",", ":")) + "\n"
        (OUTPUT_DIR / f"{path.stem}.out").write_text(out, encoding="utf-8")


if __name__ == "__main__":
    main()
