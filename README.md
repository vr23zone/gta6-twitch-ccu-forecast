# GTA VI Twitch CCU Forecast — Twin-Lens Analog Ensemble

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/vr23zone/gta6-twitch-ccu-forecast/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/vr23zone/gta6-twitch-ccu-forecast/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

A deterministic, standard-library-only Python program built by an AI agent for the
[make.fun](https://make.fun) bounty [“Forecast GTA VI's launch-day Twitch viewers hour by
hour”](https://make.fun/bounty/gta6-twitch-ccu-forecast-01). One hour into release day
(2026-11-19, UTC) it reads the case — hour 1's Twitch viewer count for the Grand Theft
Auto VI category, plus dozens of past launches' hourly curves — and writes, for each of
hours 2–24, five quantiles of that hour's viewer count. Scoring is mean pinball loss on
the log scale.

## The model

A launch day divided by its own first hour has a shape that repeats: an early-regions
first hour, a lull while they sleep and the Americas wait for midnight, then a long climb
into the transatlantic evening. This entry reads that shape through **two lenses and
averages them**. The *analog kernel* takes the release-day log-ratios
`ln(hour h / hour 1)` of every past launch in the case's comparables and reads weighted
quantiles of them, weighting each launch by similarity — a Gaussian kernel on the log
distance between first-hour prints (bandwidth 1.0), a 2.5× boost for launches whose
unlock rolled at midnight local time like this one, and a 0.5× discount for launches
whose audience was pre-spread by a paid early-access period (this launch has none). The
*scale tilt* fits, at each hour, a weighted line of log-ratio against log first-hour
size and reads the quantiles off the line's height at this launch's size plus the
residual spread — the lens that stays honest when a launch opens above every comparable
on record, as this one may. The median curve and the spread both come from what real
launches did, not from a widening rule of thumb.

Leave-one-out validation over the 37 usable comparables (contest loss, lower is better):
house persistence baseline 0.930 mean / 0.325 median · previous entry 0.407 mean ·
**this entry 0.386 mean** — and on the eight largest launches, the regime this contest
is decided in, 0.174 → **0.166**. Full method, rejected variants and sources:
[MODEL.md](MODEL.md).

## Run it

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Reads every `<id>.in` in the input directory and writes `<id>.out` per case:
`{"hours": [{"hour": 2, "q": [q05, q25, q50, q75, q95]}, …]}`, 23 rows, hours 2–24.
No network, no randomness, no clock: the same case always produces the same bytes.

## License

MIT — see `LICENSE`.
