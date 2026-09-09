# Stage 4 Report — Wars, Military, Council/Court & Final JSON Output

## Precondition check
- Stage-3 suite re-verified before any change: 66 tests collected, all green; user's staged files intact.

## Structural probe of the real save (before implementation, per rules)
- **Active wars**: `wars.active_wars.<war_id>` blocks (`attacker`/`defender` = blocks with `participants{ {character, contribution} }` + `ticking_war_score`; `casus_belli{type, attacker, defender, claimant}`; `start_date`; `name`; `battle_results{ {province, war_score, attacker_won} }`). Some entries are scalar `'none'` = deleted wars, not active. `wars.names` is a name-template table. **Key finding**: player `alive_data.wars = [5, 2, 0, 0]` is a history *counter*, not war IDs — never used as such.
- **Military**: player Men-at-Arms live in `armies.regiments.<id>{type, size, max, origin, owner}` (filter owner == player); knights = `playable_data.knights` real ID list (10); levies/strength = `landed_data.current_strength/strength/levy`. `armies.armies` (collections) and `army_regiments` (mercenary/knight-led) exist but are not player MAA.
- **Council/court**: `council_task_manager.active.<tid>{type, owner, court_owner, progress}` filtered by `court_owner == player`; `court_positions.database.{position}{court_position, task_type, employee, employer}` filtered by `employer == player`; decisions = `played_character.important_decisions` raw True/False flags; `played_character.rally_points` exists but parser-provable content is not exposed → reported `unavailable` rather than guessed.

## Extractor API (file:line — all in `extract_save.py`, structural parser only, zero regex)
| Extractor | file:line | Notes |
|---|---|---|
| `extract_wars` | `extract_save.py:1194` | `wars.active_wars` only; `'none'` entries skipped; per-side participants + `ticking_war_score`; `war_score_sum` only from provable battle scores (`None` when no battle data — never fabricated 0) |
| `extract_military` | `:1261` | levies from `landed_data`; MAA by exact `owner`; knights **only** from the real knight ID list (no counting numbers inside blocks) |
| `extract_council_court` | `:1301` | council tasks by `court_owner`; court positions by `employer`; decisions stored as **raw flags** (`no` never reported as "available") |
| `build_war_military_report` | `:1343` | additive text section `WARS, MILITARY & COURT (Stage 4)` |
| `build_state_json` | `:1388` | machine-readable output with full `quality` block |
| `cmd_extract` hooks | `:1846–1873` | same single parsed tree; legacy + Stage 2 + 3 + 4 sections; JSON written to `reports/state_report.json` |

## Bugs the fixtures caught (fixed before real-run)
1. Orphaned `side()` helper references from drafting → `KeyError: 'primary'`; primary attacker/defender taken from `casus_belli` (as the save actually stores them).
2. `owner`/`court_owner`/`employer` int-vs-string mismatch in filters (player id string vs saved int) → player's 3 regiments and 6 council tasks were silently dropped. Fixed with `str()` normalization; caught by fixture tests 2 and 5.
3. Empty/absent `battle_results` summed to `0` (fabricated) → now `None` (missing ≠ 0), caught by test 10.
4. JSON `meta.save_file` leaked the full path → now basename only, caught by test 8.
5. Report header `"="` typo; `import os` used before definition in `build_state_json`.

## Tests executed
```text
python -m pytest tests/ -q --no-header
→ 77 passed in 73.44s   Exit Code: 0
```
Breakdown: `test_extract_save.py` 32 + `test_economy_extract.py` 22 + `test_politics_extract.py` 12 + `test_war_military_extract.py` **11** (10 mandatory fixture cases `tests/test_war_military_extract.py:163–263` + real-save stage-4 stats `:265`). All fixture tests portable (real-save classes skip with `reports/melted.txt not found`).

Mandatory fixture cases (file:line):
1. Active war vs war history (history counter never becomes a war; `'none'` entries excluded) — `:172`
2. Multiple MAA regiments, player-owned only; `max` missing ≠ 0 — `:181`
3. Knights from the real ID list (2 IDs, not counted numbers) — `:191`
4. Rally points honestly labeled `unavailable` — `:196`
5. Council tasks only for the player's court — `:200`
6. Decision raw flags (`False` stays `False`, never "available") — `:209`
7. Military fields present vs missing — `:218`
8. Valid JSON with all 13 required sections + quality counts — `:224`
9. Text/JSON consistency (same counts in both) — `:240`
10. War score from provable data only (ticking + battle sum; missing → None) — `:249`

## Real-save statistics (`reports/melted.txt`, compose path 84.5 s, single parse)
| Metric | Value |
|---|---|
| Active wars | **94** |
| Wars involving player (cb attacker/defender) | 0 |
| Men-at-Arms regiments (player) | **3** — ayyar(300), light_horsemen(200), onager(20) |
| Knights | **10** (real ID list) |
| Levy / current / total strength | 1032 / 1562 / 1562 |
| Council tasks (player court) | 6 |
| Court positions (player court) | 12 |
| Decisions (raw flags) | 11 |
| Factions | 208 (35 over threshold) |
| Characters mapped | 230/230 |
| Vassal contracts | 10/10 |
| Counties / holdings | 2652 / 5 |
| Full report (legacy + S2 + S3 + S4) | 230,748 chars |

## JSON output — `reports/state_report.json` (valid JSON, re-parsed; 50,192 lines / ~1.0 MB)
```json
{"meta": {"save_file": "…", "game_date": "937.1.25"}, "player": {}, "domain": [], "counties": [],
 "holdings": [], "characters": [], "vassals": [], "factions": [], "succession": {}, "wars": [],
 "military": {}, "court": {}, "quality": {"missing_fields": [], "unmapped_ids": [], "warnings": []}}
```
- All 13 required keys present; quality counts match text report exactly (test 9 consistency).
- `quality.missing_fields`: 4 (3× `holding.holding_type` for c_bukhara/c_samarkand/c_khojand, `player.faith`).
- `quality.unmapped_ids`: 0. `quality.warnings`: player-faith incomputable + faction-threshold-missing sample.
- `quality.sources`: provenance per section; `extraction_time` recorded; `save_file_name` basename only.
- Generated through the exact `cmd_extract` compose path on the already-melted text (no re-melt; `reports/state_report.txt` untouched).

## Final acceptance criteria — status
- Historical wars reported as active: **no** (only `wars.active_wars`; counter block never used).
- Knight count exact: **yes** (10, from the ID list only).
- Military section filled from real save numbers: **yes** (levies 1032/1562/1562, 3 regiments with types/sizes).
- JSON valid and consumable: **yes** (re-parsed; provenance + quality included).
- Legacy text report still works: **yes** (77 tests pin it; state_report.txt untouched).
- Missing/unmapped transparent: **yes** (explicit quality block; missing ≠ 0 everywhere).
- No fabricated information: **yes** (rally points `unavailable`; war scores `None` without battle data; decisions raw flags).
- All tests green: **77 passed, exit 0**. No files outside scope changed (function-body diff vs staged: stage-4 additions only; removed vs staged still just `_title_keys`).

## Closing-audit addendum (final review)
- A genuine end-to-end run (`python extract_save.py extract`, auto-picked save, full melt → parse → report + JSON) completed with **Exit Code 0**: `reports/state_report.txt` (235,499 bytes) contains legacy + Stage-2 + Stage-3 + Stage-4 sections; `reports/state_report.json` (1,011,442 bytes) re-parsed valid with all 13 sections.
- The run used the **newly melted save on disk** (199,680,999 chars, game date `943.7.25`, later than the stage-probe file at `937.1.25`): counts moved accordingly (86 active wars, 220 factions, 238 characters mapped/0 unmapped, 11 contracts, 10 court positions; player age 55) and **all 5 domain counties and their province mappings held**. The full suite was then re-run against the new save: **77 passed, Exit Code 0** — including the value-pinned real-save assertions (c_nakhshab→5673, c_dabusiya→5683, 5 domain counties), which are stable structural facts of the campaign.
- Stage-1/2 report line refs re-verified against the final file; stale refs in those two reports were corrected there.

## Remaining limitations (honest)
- War `war_score` is provable only as `ticking_war_score` per side + sum of `battle_results` scores; a single authoritative total score is not stored in the save.
- Rally points, siege details, and per-regiment maintenance are present in the save but not provably mappable to the player at the required confidence → labeled unavailable/raw rather than guessed.
- Player faith (from stage 3) and 3 holding types remain missing — structural property of this save format.
- The final JSON is produced by `cmd_extract` runs; the checked-in artifact was composed through the identical code path.

READY FOR HUMAN VERIFY
