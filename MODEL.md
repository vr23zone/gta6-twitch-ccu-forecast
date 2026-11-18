# Method: a twin-lens analog ensemble

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

This entry reads the shape through **two lenses and averages them** (a vincentized
ensemble, 50/50 on the log-ratio scale, per hour and per quantile):

* **Lens 1 — the analog kernel.** For every past launch in the case's comparables, form
  the 23 log-ratios `ln(viewers of hour h / viewers of hour 1)` of its own release day.
  The forecast at hour h is a *weighted quantile* of those ratios across launches,
  weighted by similarity (below). Local, empirical, and safe: it can only say things
  that are between things real launches did.
* **Lens 2 — the scale tilt.** Shape is not independent of size: the sag-and-climb of a
  900k launch is systematically different from a 9k one's. At each hour, fit a weighted
  straight line of log-ratio against log first-hour size across the comparables (same
  similarity weights), read the line's height at *this* launch's size — the shift
  clipped to ±0.5 log units, so the line may lean but never run away — and take the
  quantiles from the weighted spread of the residuals around the line. The tilt is what
  keeps the forecast honest in extrapolation: GTA VI may open above every comparable on
  record, where a pure kernel can only repeat the largest launches it has seen, while
  the tilt follows the direction shape has been moving with scale.

The spread is therefore not a formula in either lens; it is the observed dispersion of
what launches actually did, hour by hour, which is what a pinball score rewards.

## Similarity weighting

Both lenses share one weighting of the comparables, three judgements:

* **Scale kernel (the big term).** A Gaussian kernel on the log distance between the
  comparable's first-hour print and this case's: `exp(-0.5 * (d / 1.0)^2)`. An 800k
  launch is strong evidence about another 800k launch and weak evidence about a 5k one,
  because the composition of the audience changes with scale.
* **Unlock pattern (×2.5).** A comparable whose unlock rolled at midnight local time —
  read from its `unlock` note — gets 2.5× weight when this case's notes describe the
  same rolling pattern, because its shape encodes the same sequence of regional unlocks.
* **Clean release day (×0.5).** A comparable whose audience was pre-spread by a paid
  early-access period gets half weight when this launch has none. The case data itself
  flags several comparables "early-access-contaminated" (Diablo IV, Starfield, Forza
  Horizon, Death Stranding 2, DOOM: The Dark Ages, Assassin's Creed Shadows), and
  Hogwarts Legacy's note affirms its 72-hour early access outright. Those launches'
  release days are second acts — the day-one spike already happened — and their curves
  are flattened in a way a clean day-one curve is not. GTA VI has no early access, so
  the discount applies here; the detector keys on the notes' own words and treats
  "no early access" as the clean statement it is.

## Validation

Leave-one-out over the 37 usable comparables in the practice cases (each launch in turn
treated as the target, forecast from the other 36, scored with the contest's exact
pinball-on-log loss; the house persistence baseline scored the same way):

| model | mean loss | median loss |
| --- | --- | --- |
| house persistence baseline | 0.930 | 0.325 |
| previous entry (analog kernel, boost ×1.5) | 0.407 | 0.240 |
| + scale tilt lens, boost ×2.5, EA discount (this entry) | **0.386** | 0.245 |

The median is a wash; the mean — the quantity the contest itself averages — is not the
whole story either, because this contest is decided by a *single* case in the giant
regime. On the launches that resemble it, the improvement is uniform:

| subset of LOO targets | previous entry | this entry |
| --- | --- | --- |
| 16 launches with hour 1 ≥ 100k | 0.209 | **0.197** |
| 8 largest launches | 0.174 | **0.166** |
| 5 largest launches | 0.133 | **0.124** |

And on five synthetic final-like cases — each giant launch in turn rebuilt as a case of
the final's exact shape (its own hour-1 print as the known, the other launches as
comparables, its pre-release series attached as the case history) and scored through the
shipped programs themselves: previous entry 0.133 mean, **this entry 0.123**, winning
four of the five (the loss is Diablo IV, itself an early-access launch — the one giant
whose day GTA VI's clean launch should *not* resemble).

(The baseline's published practice loss is 0.387 over the four real practice cases; the
0.930 here is the same program over 37 harder pseudo-cases, a few of which it fails
catastrophically — its median is the fairer summary of it, and the ensemble beats that
too. A prize also has to beat the house's one-shot AI forecast, which no local test can
reproduce.)

## What was tried and rejected

* **Installed-base kernel** (similarity of the seven-day pre-launch baseline of each
  category): the best *full-field* variant found — 0.363 mean against this entry's
  0.386. Its gains concentrate in small and mid-size launches whose baselines expose
  them as confounded (Marathon, ARC Raiders, Black Myth: Wukong, Saros), but it
  consistently *costs* the giant regime this contest is decided in (eight largest:
  0.174 with it, 0.166 without; Diablo IV 0.196 vs 0.162), and it leans on the case's
  recorded history being long and fresh. Rejected for this contest, on this evidence,
  and recorded here so the trade is explicit.
* **Recalibration** (per-level tau shifts; per-level spread rescaling around the
  median): fitted honestly by cross-fitting — calibrate on 36 launches, apply to the
  held-out one — it does not survive out of sample (0.366–0.367 cross-fitted vs 0.363
  uncalibrated on the configuration tested). The empirical quantiles are shipped as
  measured.
* **Viewers-per-channel kernel** (similarity of hour 1's viewers per live channel):
  hurt at every bandwidth (0.410–0.428). The channel count says more about a category's
  streamer ecology than about its day shape.
* **Launch-spike weighting** (hour 1 against the pre-launch baseline): hurt (0.438 in
  the previous entry's tests) — the baseline says more about a category's everyday
  community than about its launch shape.
* **Recency weighting, weekday matching, per-analog curve smoothing, weight caps,
  console-only boost**: neutral to slightly negative each; left out. Breadth and
  cleverness are not free at 37 analogs.
* **Within-hour momentum** (tilting hour 2 by the last minutes of hour 1): the final
  case has minute reads that could support it, but no practice data exists to validate
  it, so it was left out rather than shipped untested.

## Context the model is forecasting into

* The single-player launch record on Twitch is Hogwarts Legacy at roughly 1.3M peak
  concurrent viewers (February 2023); Cyberpunk 2077 peaked near 1.14M and Elden Ring
  near 0.91M (trackers: Streams Charts, Stream Hatchet, TwitchTracker).
* The Grand Theft Auto V category's all-time Twitch peak is about 1.14M (May 2021, set
  by roleplay servers years after launch, per TwitchTracker) — a sequel's launch day is
  a different animal, and GTA VI's gameplay reveal drew a 3.97M cross-platform peak with
  Twitch taking 44% of hours watched.
* The case's own comparable set agrees: the largest launch in it (Elden Ring) averaged
  875k viewers in its biggest hour. GTA VI is expected at or above the top of the
  comparable range — exactly the regime the scale tilt is built for, and the regime the
  validation above is weighted toward.

## Limits

The ensemble can only express shapes that have happened before, tilted by how shape has
moved with scale; a launch that behaves unlike all 37 analogs (a server outage, a delay
announced mid-day, a platform exclusivity twist) will land outside the quantiles, as it
should a few percent of the time. The final case's hour-1 print is a minute mean while
the practice prints are hourly averages — close measures, not identical ones.

## Sources

* Case data: the contest's `comparables`, sourced from SullyGnome
  (https://sullygnome.com) hourly Twitch category averages, as shipped in the kit's
  practice cases and described in the case `notes`.
* Contest mechanics, unlock schedule and the baseline formula: the competition's
  published rules (kit `RULES.txt` / `competition.yaml`).
* Launch records: Streams Charts and Stream Hatchet reporting on Hogwarts Legacy,
  Cyberpunk 2077 and Elden Ring launch peaks; TwitchTracker, Grand Theft Auto V
  category all-time peak.
