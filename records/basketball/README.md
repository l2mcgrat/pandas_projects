# Basketball data contract — schema 1

The owner-authored [series.json](series.json) is the only input. The engine is
read-only: it neither edits this log nor publishes JSON, JavaScript, CSV, HTML,
or projections. The parent publisher owns serialization and rendering.

## Python API for the parent

- `site_content.basketball.analyze_series(data: dict) -> dict`: validate an
  already-decoded source and return a new, JSON-compatible analysis. No I/O.
- `site_content.basketball.load_basketball(root: Path) -> dict`: read
  [series.json](series.json) below the repository root, validate, then analyze.
  The argument is the repository root, **not** the records directory.
- `site_content.basketball.export_rows(result: dict) -> dict[str, list[dict]]`:
  accept the enriched analysis, **not the raw source**, and return 12 new,
  scalar-only tables described below. No writes or serialization.
- `BasketballValidationError(ValueError)` identifies invalid or unsupported
  source with a JSON-style location. File-not-found, UTF-8 decoding and JSON
  syntax errors propagate; there is no silent fallback or partial analysis.
  Duplicate JSON object keys and non-finite JSON constants are rejected.

All counts are integers. All rates are **fractions in [0, 1], not percentages**.
Undefined rates use Python `None` / JSON `null`, not zero. The result passes
strict JSON serialization with `allow_nan=False`. Empty logs are supported;
any series that is present must be completed.

The parent should call `load_basketball(root)`, serialize its return value for
JSON and data-JS with its existing `safe_json`, and pass that same result to
`export_rows`. All strings remain unescaped source data. Use text-only DOM
insertion / HTML escaping, script-safe JSON embedding, and spreadsheet-safe CSV
handling in the parent; ordinary CSV quoting does not prevent formula execution.

## Input validation and chronology

Required root fields: `schemaVersion` (integer `1`, never boolean), `title`,
`sourceTitle`, `players`, `provenance`, `series`. The two titles are nonempty
strings. `provenance` is an object of nonempty string keys and values, including
`source`; its contents are copied exactly. Other root fields are rejected.

`players` is exactly the two `{id, name}` objects for `L` / `Liam` and `O` /
`Owen`, without duplicate IDs. Input player-array order may vary. These public
sports shortnames do **not** rename the professional profile. The supplied
source heading, `Liam McGrath-Dent`, stays in `source.sourceTitle`.

Each series requires `id`, `date`, `sourceDate`, `session`, `order`, `games`:

- `date` is an actual calendar date in strict `YYYY-MM-DD` form, not a timestamp.
  `sourceDate` is M/D/YYYY (one or two digits for month/day) and must match it.
- `id` is exactly `date-session`, with an unpadded positive integer session.
  IDs cannot repeat. Sessions for each date start at 1 and increment in **source
  entry order**, without gaps or duplicates. A new date restarts at 1.
- Analysis is stably sorted by ISO date. Entries sharing a date keep their
  source order; no start times, elapsed gaps, or artificial clock times are
  invented. `sourceIndex` and `sequenceIndex` are both 1-based and make this
  distinction explicit. The input list itself is never sorted in place.
- `games` has 4–7 objects, each with a known `challenge` and a winner of `L` or
  `O`. A series ends exactly when a player first reaches four round wins.
  Incomplete series and any round after the clinch are rejected.
- `order` must be the exact concatenation of game winners; it is not corrected,
  trimmed, or reconstructed in place.
- Optional series fields are `court` (nonempty string or null),
  `rimHeightInches` (positive finite number or null, never boolean), and `note`
  (string). Absent court/rim metadata becomes null, never carried forward.
- Game optional fields are `scoreRaw`, `timeRaw`, `note`. Unknown fields or
  additional players/formats are rejected rather than silently interpreted as
  a multiplayer or in-progress extension.
- Repeated challenge kinds within a series are **allowed and flagged**. A
  no-repeats rule is unconfirmed. Aggregations still count every played round.

Canonical challenge order, also the matrix row/column order:
`shooting`, `bump`, `horse`, `backboard`, `three-point`, `rim`, `one-on-one`.
Display labels are Shooting, Bump, HORSE, Backboard, 3 Point, Rim, and 1v1.

### Scores and times

For HORSE and Bump, `scoreRaw` is preserved as a nonempty string without
interpreting the numeric/letter orientation or mechanics. For example, a raw
5–x score is not converted to basketball points, letters earned, or a mercy.

Only 1v1 scores become winner–loser points. Its supported raw notation is
`7-3` / `7:3` (and similarly a winner at 8 and loser from 0 to 6). The normalized
form uses a hyphen while preserving the raw string. Seven is the minimum
winning total; a two-point shot can finish at eight. This is a rule note, not
an assertion that an additional 8-point match occurred. There is no win-by-two
or overtime inference. Missing scores are allowed. Scores on other challenge
kinds are rejected in this input version.

`timeRaw` applies only to 3 Point and must be a string. It accepts M:SS or MM:SS
(one or two minute digits, exactly two second digits, seconds below 60), `TBD`,
or `N/A`. Whitespace, floats, booleans, nulls, signs and other formats are rejected.
All listed times describe the **winning player's completion time**, not a series
start time or a losing-player time.

| Situation | `status` | `raw` | `seconds` | `played` in timing entries |
|---|---|---|---|---|
| Recorded duration | `valid` | exact source string | integer, including 0 | true |
| `TBD` | `pending` | `TBD` | null | true |
| `N/A` | `not-recorded` | `N/A` | null | true |
| Played, field absent | `missing` | null | null | true |
| No 3 Point round in series | `not-played` | null | null | false |

Non-3-Point rounds have a round-local time status of `not-applicable`; those
rounds are not individual timing entries. A genuine `00:00` remains numeric
zero and is never confused with a missing or unplayed challenge.

## Enriched return value: exact UI shapes

`PlayerCounts` means `{L: int, O: int}`; `PlayerRates` means
`{L: float|null, O: float|null}`. Every array is deterministic; none is a set.

### Top-level fields

| Field | Shape / purpose |
|---|---|
| `schemaVersion`, `title` | `1`, source title string |
| `source` | `{path, schemaVersion, sourceTitle, chronology}`; relative input path and explicit ordering statement |
| `provenance` | exact deep copy of source provenance |
| `players` | copied two-object `{id, name}` array |
| `challengeDefinitions` | seven `{id, label, hasWinnerTime, scoreSemantics, repeatPolicy}` objects |
| `series` | chronological enriched series, described below |
| `summary` | counts, fractions and streak, described below |
| `challenges` | seven `{id, label, played, wins, winRateDenominator, winRates, seriesWithChallenge, notPlayed, duplicateSeriesCount}` objects |
| `transitions` | within-series next-round events, described below |
| `byPicker` | two `{player, countPicks, denominator, holds, losses, holdRate, lossRate}` objects |
| `transitionMatrix` | `{challengeOrder: string[7], counts: int[7][7]}`; row = previous, column = next challenge |
| `conditionalNextChallenge` | fourteen `{player, nextChallenge, countPicks, countWins, countLosses, pickerTotal, choiceShare, winRate}` objects |
| `seriesLengths` | four `{roundCount, seriesCount, seriesRate, seriesWins}` bins for lengths 4–7 |
| `comebacks` | four `{winnerMaxDeficit, seriesCount, seriesWins}` bins for deficits 0–3; zero is **not** a comeback |
| `trajectories` | flat `{seriesId, date, session, round, L, O, margin}` points, including origin for every series |
| `timing` | timing counts, entries and bests, described below |
| `caveats` | displayable limitations; keep these visible with the descriptive charts |

For each challenge, `played` counts rounds, not series. `wins` is `PlayerCounts`.
`winRates[p] = wins[p] / played`, with `winRateDenominator = played`.
`seriesWithChallenge` counts distinct series containing it; `notPlayed` is
`seriesCount - seriesWithChallenge`. Thus repeats can increase `played` beyond
the number of series without making `notPlayed` negative. `duplicateSeriesCount`
counts series in which that particular challenge repeats.

### Summary

Scalar fields: `seriesCount`, `challengeCount`, `distinctDateCount`, `firstDate`,
`lastDate`, `sweeps`, `deciders`, `comebacks`, `openingWinnerWonSeries`,
`openingWinnerWinRate`. Dates are ISO strings or null for an empty log.

- `seriesWins`, `challengeWins`, `sweepWins`, `deciderWins`: `PlayerCounts`.
- `seriesWinRates`: `PlayerRates`, denominator `seriesCount`.
- `challengeWinRates`: `PlayerRates`, denominator `challengeCount`.
- `currStreak`: `{player: "L"|"O"|null, length: int}` — consecutive **series**
  wins at the chronological end of this supplied log, not an all-time claim.
- `transitions`: `{total, switches, retentions, switchRate, retentionRate}`;
  both rates have denominator `total`.
- `openingWinnerWonSeries` counts series where the first round winner also won
  the series; `openingWinnerWinRate` divides this count by `seriesCount`.
- Sweeps are four-round completions; deciders are seven-round completions.
  `comebacks` counts series whose eventual winner was strictly behind at least
  once, not merely tied or the loser of round one.

### Enriched series and rounds

Every source series keeps its original `id`, `date`, `sourceDate`, `session`,
`order`, optional `note`, and **deep-copied, unaltered `games`**. Optional courts
and rim heights become explicit nulls when absent. Added series fields:

- `sourceIndex`, `sequenceIndex`, `roundCount`, `winner`, `loser`,
  `challengeWins: PlayerCounts`, `finalScore` (series winner–loser round wins).
- `openingWinner`, `openingWinnerWonSeries: bool`, `sweep: bool`, `decider: bool`.
- `winnerMaxDeficit: int`, `comeback: bool`.
- `duplicateChallenges: [{challenge, count}]`, only counts above one.
- `transitionCount`, `retentions`, `switches`, `retentionRate`, `switchRate`.
- `trajectory: [{round, L, O, margin}]`, starting at `{round:0,L:0,O:0,margin:0}`,
  then a point after **every** round. Margin is always cumulative L minus O,
  regardless of which player wins the series.
- `rounds`: enriched objects separate from the raw `games` array.

Each round retains all source game fields, and adds:

- `number` (1-based), `loser`, `cumulativeWins: PlayerCounts`, `margin` (L minus O).
- `previousWinner`, `inferredPicker`: L/O after round one; otherwise null.
- `retained`: whether previous winner won this round; null on round one.
- `score: {raw, normalized, winnerPoints, loserPoints, status}`. Status is
  `recorded-uninterpreted`, `winner-loser-points`, `not-recorded`, or
  `not-applicable`. Numeric points and normalized string exist only for recorded
  1v1 scores; otherwise these fields are null.
- `time: {raw, seconds, status}` with the states defined above.

### Winner-picks-next and alternation

Each transition is:
`{seriesId, date, session, previousRound, nextRound, prevWinner, inferredPicker,
previousChallenge, nextChallenge, nextWinner, retained}`.

`inferredPicker = prevWinner`. It is **not** a measured choice-maker. The house
rule is winner-picks-next, not mandatory alternation of player turns. A retention
means consecutive winners match; a switch means they differ. Plot these observed
switches, retentions, and trajectories to describe alternation dynamically.

Only adjacent rounds **within the same series** contribute. Round one has no
picker, and the clinching winner does not acquire a hypothetical next choice.
There is never a last-round-to-next-series transition. The total is therefore
`challengeCount - seriesCount`, also the sum of the 7×7 matrix counts.

In `byPicker`, `countPicks = denominator = holds + losses`; rates divide by
that denominator. In `conditionalNextChallenge`, for each player/challenge:

- `countPicks`: transitions with that inferred picker and next challenge.
- `countWins`: those transitions in which the picker also won the next round.
- `countLosses = countPicks - countWins`.
- `pickerTotal`: all transitions attributed to that picker, across challenges.
- `choiceShare = countPicks / pickerTotal`; `winRate = countWins / countPicks`.

These answer different questions: choice frequency versus observed retention.
Neither is an ability estimate, a causal selection effect, or evidence for a
best decision. Even a 100% cell can have denominator one. There are no p-values,
statistical-significance claims, implied 50% random null, or speculative future
win projections. Unequal player skill and first-to-four stopping/selection make
that random-null interpretation unjustified. The sample is small and descriptive.

### Timing object

`timing` contains `entries`, `validEntries`, `missingEntries`, `notPlayedEntries`,
`played`, `validCount`, `missingCount`, `notPlayedCount`, `statusCounts`,
`bestOverall`, `bestByPlayer`, `byPlayer`.

Each entry has `{seriesId, date, session, sequenceIndex, round, winner, played,
raw, seconds, status, note}`. There is one entry for each played 3 Point round,
even if repeated, plus one `not-played` row for each series with no such round.
The latter has null `round`, `winner`, `raw`, `seconds`, and `note`.

- `validEntries` contains only valid numeric times.
- `missingEntries` contains played rounds with pending, not-recorded or missing
  time; **never** not-played rows. `played = validCount + missingCount`.
- `statusCounts` has all five keys: `valid`, `pending`, `not-recorded`, `missing`,
  `not-played`, including zeros.
- `bestOverall` is a full valid entry or null.
- `bestByPlayer` is `{L: entry|null, O: entry|null}`.
- Bests minimize seconds. On a tie the first chronological entry is the
  representative; all tied entries remain available in `validEntries`.
- `byPlayer` has `{player, played, validCount, missingCount}` for L and O.

There are no attempted-shot counts, losing-player times, inferred times, or
adjustments for rebounding assistance. Missing is not zero and unplayed is not
a timing failure. The current court metadata is only the two August dates:
Left Court, 114 inches (9 ft 6 in). Everything else stays null. No mercy totals
or dinner obligations are inferred from scores, streaks, or notes.

## CSV table contract

Every cell is `str`, `int`, `float`, `bool`, or `None`. Rows in each nonempty
table have consistent keys. Counts below are the **current fixture**, never
limits or constants used by the analysis. Empty tables return `[]`.

| Table key | Current rows | Columns / flattening |
|---|---:|---|
| `summary` | 1 | Scalar summary fields; player maps expand to `seriesWinsL/O`, `challengeWinsL/O`, `seriesWinRatesL/O`, `challengeWinRatesL/O`, `sweepWinsL/O`, `deciderWinsL/O`; `streakPlayer`, `streakLength`; `transitionsTotal`, `transitionsSwitches`, `transitionsRetentions`, `transitionsSwitchRate`, `transitionsRetentionRate` |
| `series` | 13 | `seriesId`, `date`, `sourceDate`, `session`, `sourceIndex`, `sequenceIndex`, `order`, `roundCount`, `winner`, `loser`, `finalScore`, `sweep`, `decider`, `openingWinner`, `openingWinnerWonSeries`, `winnerMaxDeficit`, `comeback`, `court`, `rimHeightInches`, `transitionCount`, `retentions`, `switches`, `retentionRate`, `switchRate`, `winsL`, `winsO`, `duplicateChallenges`, `note` |
| `rounds` | 73 | Same six series context fields; `round`, `challenge`, `winner`, `loser`, `note`, `court`, `rimHeightInches`, `cumulativeL`, `cumulativeO`, `margin`, `inferredPicker`, `previousWinner`, `retained`, `scoreRaw`, `scoreNormalized`, `scoreStatus`, `winnerPoints`, `loserPoints`, `timeRaw`, `timeSeconds`, `timeStatus` |
| `challenges` | 7 | Challenge row scalars plus `winsL`, `winsO`, `winRateL`, `winRateO` instead of nested player maps |
| `transitions` | 60 | Exact scalar transition shape above |
| `byPicker` | 2 | Exact scalar picker shape above |
| `conditionalNextChallenge` | 14 | Exact scalar conditional shape above, including unpicked challenge cells |
| `transitionMatrix` | 49 | `previousChallenge`, `nextChallenge`, `count`; includes zero cells |
| `trajectories` | 86 | Exact scalar trajectory shape above; 73 played rounds + 13 origins |
| `seriesLengths` | 4 | `roundCount`, `seriesCount`, `seriesRate`, `seriesWinsL`, `seriesWinsO` |
| `comebacks` | 4 | `winnerMaxDeficit`, `seriesCount`, `seriesWinsL`, `seriesWinsO` |
| `timing` | 13 | All timing entries, including missing/unplayed states; exact scalar entry shape above |

Series CSV `duplicateChallenges` joins `challenge:count` pairs with semicolons;
the JSON retains structured objects. Nulls are deliberately not converted to
zero or the text “N/A”; keep the accompanying status columns during CSV writing.

## Independent baseline and tests

The supplied log currently contains **13 series across 7 distinct dates**, not
13 unique dates. All 13 winner orderstrings are checked against their raw games.

- Challenge wins: **73 = 50 L + 23 O**; series wins: **13 = 12 L + 1 O**.
- Trailing series streak: **11 L**, equivalently 11 supplied series losses for O.
- Length bins: **4 → 2, 5 → 2, 6 → 8, 7 → 1**; 2 sweeps, 1 decider.
- Eventual winner was behind in **6** series; opening winner won **8/13**.
- Within-series transitions: **60 = 35 retentions + 25 switches**.
- Inferred L picks: **38 = 28 holds + 10 losses**; O: **22 = 7 + 15**.
- 3 Point: **12 played, 10 valid times**, 1 pending, 1 not-recorded, 1 series
  not played; current absent-played-time count is 0.
- Best overall / Liam: **82 seconds (1:22), 2026-09-07 session 2**.
  Best Owen: **193 seconds (3:13), 2026-08-08 session 1**.

The unittest module `site_content.tests.test_basketball` independently counts
raw data, checks all 240 four-to-seven-round binary winner strings (70 valid
completions), malformed field types, date/session/ID errors, score/time states,
same-day chronology, synthetic later logged results, ties, repeats, all-zero
denominators, deep nonmutation, byte-preserving loading, and scalar CSV contracts.
Golden assertions describe the supplied snapshot; legitimate source additions
will require independently updating those expectations. The engine itself has
no fixed data counts, date cutoff, as-of clock, or hardcoded streaks.

## Proposed logging template — documentation only

These are placeholder **rows to fill**, not recorded observations. No template
data is appended to the authored log. Record observations after a series is
complete; leave incomplete sessions outside this schema until a deliberate
versioned extension supports them.

| JSON path | Placeholder / instruction |
|---|---|
| `$.series[i].date` | `<YYYY-MM-DD>` |
| `$.series[i].sourceDate` | `<M/D/YYYY matching date>` |
| `$.series[i].session` | `<1-based entry number for that date>` |
| `$.series[i].id` | `<date>-<session>` |
| `$.series[i].court` | `<recorded court name>` or null; never copy a prior location by assumption |
| `$.series[i].rimHeightInches` | `<measured/explicitly reported height>` or null |
| `$.series[i].note` | `<verbatim optional series note>` |
| `$.series[i].order` | `<exact L/O winners from all 4–7 completed rounds>` |
| `$.series[i].games[j].challenge` | `<one of the seven canonical IDs>` |
| `$.series[i].games[j].winner` | `<L or O>` |
| `$.series[i].games[j].scoreRaw` | `<verbatim supported score>`; omit if not logged/applicable |
| `$.series[i].games[j].timeRaw` | `<M:SS, MM:SS, TBD or N/A for 3 Point>`; omit if absent, never substitute 0 |
| `$.series[i].games[j].note` | `<verbatim optional round note>` |

Potential **future, explicitly versioned** logging fields: actual picker and
selection options, agreed repeat policy, agreed HORSE/Bump score orientation,
measured start time, both players' attempts/completion times, and rebounding
assistance. These are not present observations and are not accepted as extra
schema-1 fields. Do not infer them, mercy events, or multiplayer behavior from
the current winner strings.