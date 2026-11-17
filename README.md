# GTA VI Twitch CCU Forecast — Launch-Curve Analog Ensemble

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
into the transatlantic evening. This entry is an **analog ensemble**: it takes the
release-day log-ratios `ln(hour h / hour 1)` of every past launch in the case's
comparables, weights each launch by similarity — a Gaussian kernel on the log distance
between first-hour prints (bandwidth 1.0), with a 1.5× boost for launches whose unlock
rolled at midnight local time like this one — and reads the five quantiles of the
weighted distribution at each hour. The median curve and the spread both come from what
real launches did, not from a widening rule of thumb.

Leave-one-out validation over the 37 usable comparables (contest loss, lower is better):
house persistence baseline 0.930 mean / 0.325 median · unweighted analogs 0.716 ·
**this model 0.407 mean / 0.240 median**. Full method, rejected variants and sources:
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
