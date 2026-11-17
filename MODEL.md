# Method: a launch-curve analog ensemble

## The question

One hour into a big game's release day, say how many people will be watching it live on
Twitch in each of the 23 hours that remain — as five quantiles an hour (5%, 25%, 50%, 75%,
95%), scored by mean pinball loss on the log scale. The only hard fact at forecast time is
hour 1's viewer count. Everything else is judgement about the *shape* of a launch day.

## The idea

Divide a launch day by its own first hour and the level washes out; what remains is a
shape, and the shape repeats. A rolling midnight-local unlock (New Zealand first at
2026-11-18T11:00Z for GTA VI, central Europe at 23:00Z, the UK at 00:00Z, the US east coast
at 05:00Z, the west coast at 08:00Z) means hour 1 UTC is carried by Oceania, Asia and
Europe's midnight players. Hours 2–5 sag: the early regions go to sleep or work and the
Americas are still locked. From the US unlocks onward the audience climbs almost without
interruption into the transatlantic evening, and the day's peak typically lands between
19:00 and 23:00 UTC, at two to three times the first hour.

So the forecaster is an *analog ensemble*. The case file carries dozens of past launches
with their hourly viewers (SullyGnome's hourly Twitch category averages, from 14 days
before each release day to 3 days after). For each past launch we compute the 23
log-ratios `ln(viewers of hour h / viewers of hour 1)` of its own release day. The forecast
for hour h is this case's first-hour print times the exponential of a quantile of those
log-ratios — the median ratio for the median, the 5th-percentile ratio for the 5%
quantile, and so on. The spread is therefore not a formula; it is the observed dispersion
of what launches actually did, hour by hour, which is what a pinball score rewards.

## Similarity weighting

Not every past launch is equally informative, and weighting is where the score is won:

* **Scale kernel (the big term).** Each comparable is weighted by a Gaussian kernel on the
  log distance between its first-hour print and this case's: `exp(-0.5 * (d / 1.0)^2)`.
  An 800k launch is strong evidence about another 800k launch and weak evidence about a
  5k one, because the composition of the audience (and how much of it is there for the
  event rather than the game) changes with scale.
* **Unlock pattern (×1.5).** A comparable whose unlock rolled at midnight local time —
  read from its `unlock` note — gets 1.5× weight when this case's notes describe the same
  rolling pattern, because its shape encodes the same sequence of regional unlocks.

## Validation

Leave-one-out over the 37 usable comparables in the practice cases (each launch in turn
treated as the target, forecast from the other 36, scored with the contest's exact
pinball-on-log loss; the house persistence baseline scored the same way):

| model | mean loss | median loss |
| --- | --- | --- |
| house persistence baseline | 0.930 | 0.325 |
| analog ensemble, unweighted | 0.716 | 0.393 |
| + scale kernel (bandwidth 1.0) | 0.410 | 0.254 |
| + rolling-unlock boost ×1.5 (this entry) | **0.407** | **0.240** |

(The baseline's published practice loss is 0.387 over the four real practice cases; the
0.930 here is the same program over 37 harder pseudo-cases, a few of which it fails
catastrophically — its median is the fairer summary of it, and the ensemble beats that
too. A prize also has to beat the house's one-shot AI forecast, which no local test can
reproduce.)

## What was tried and rejected

* **Launch-spike weighting** (similarity of first-hour print to the pre-launch baseline):
  hurt (0.438) — the pre-launch baseline of a category says more about its everyday
  community than about its launch shape.
* **Console-only boost**: no measurable gain once scale is weighted; dropped for
  simplicity.
* **Smoothing the quantile curves across hours**: neutral (0.409 vs 0.410); dropped —
  the per-hour empirical quantiles are already stable at ~37 analogs per hour.
* **A uniform weight floor** under the kernel: hurt monotonically (0.414 at a 10% floor,
  0.454 at 30%) — breadth is not free.
* **Spread rescaling** (widening or narrowing the empirical quantiles): neutral either
  way; the empirical spread is kept as measured, which is the honest answer a proper
  scoring rule asks for.
* **Within-hour momentum** (tilting hour 2 by the last minutes of hour 1): the final case
  has minute reads that could support it, but no practice data exists to validate it, so
  it was left out rather than shipped untested.

## Context the model is forecasting into

* The single-player launch record on Twitch is Hogwarts Legacy at roughly 1.3M peak
  concurrent viewers (February 2023); Cyberpunk 2077 peaked near 1.14M and Elden Ring near
  0.91M (trackers: Streams Charts, Stream Hatchet, TwitchTracker).
* The Grand Theft Auto V category's all-time Twitch peak is about 1.14M (May 2021, set by
  roleplay servers years after launch, per TwitchTracker) — a sequel's launch day is a
  different animal, and GTA VI's gameplay reveal drew a 3.97M cross-platform peak with
  Twitch taking 44% of hours watched.
* The case's own comparable set agrees: the largest launch in it (Elden Ring) averaged
  875k viewers in its biggest hour. GTA VI is expected at or above the top of the
  comparable range, which is exactly the regime the scale kernel is built for — the
  forecast leans on the handful of genuinely comparable mega-launches.

## Limits

The ensemble can only express shapes that have happened before; a launch that behaves
unlike all 37 analogs (a server outage, a delay announced mid-day, a platform
exclusivity twist) will land outside the quantiles, as it should a few percent of the
time. The final case's hour-1 print is a minute mean while the practice prints are
hourly averages — close measures, not identical ones.

## Sources

* Case data: the contest's `comparables`, sourced from SullyGnome
  (https://sullygnome.com) hourly Twitch category averages, as shipped in the kit's
  practice cases and described in the case `notes`.
* Contest mechanics, unlock schedule and the baseline formula: the competition's
  published rules (kit `RULES.txt` / `competition.yaml`).
* Launch records: Streams Charts and Stream Hatchet reporting on Hogwarts Legacy,
  Cyberpunk 2077 and Elden Ring launch peaks; TwitchTracker, Grand Theft Auto V
  category all-time peak.
