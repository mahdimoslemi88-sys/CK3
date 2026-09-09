# Stage 2 Report — Domain, County, Holding & Building Extraction

## Response to the VERIFY: FAIL — all seven required items addressed

### 1. rgb { … } regression test — exact name and file:line
- **`TestParserRgbBug.test_rgb_value_consumed_and_parsing_continues`** — `tests/test_economy_extract.py:295` (class), `:321` (test).
- The test proves more than "no crash":
  - `parser._i == parser.n` — the parser consumed the **entire fixture** (assertion failure message names the stop position if truncated);
  - `landed_titles` / title `99` / `key=c_test` still parse correctly after the rgb group;
  - `next_block` and `after_that` exist at root level after the rgb construct;
  - their `value=yes` / `value=no` fields read as `True` / `False` (parser scalar conversion).
- Result: **passed**. (It initially failed its own new EOF assertion against the pre-fix expectations of `value == 'yes'` — the parser converts yes/no to booleans; the test was corrected, the parser was not.)

### 2. Real-save root-block presence test — exact name and file:line
- **`TestRealSaveRootBlocks.test_required_root_blocks_present`** — `tests/test_economy_extract.py:368`.
- Asserts these root blocks exist in the real save: `played_character, characters, landed_titles, provinces, county_manager, holdings, faction_manager, wars, religion, culture_manager, succession, character_memory_manager, dynasties, living, character_lookup, units, armies, sieges`.
- **Verified against the file itself** (depth-0 name scan of the raw 185 MB text): all 18 names are genuinely present. The save's real names are `faction_manager` (not `factions`), `religion` (not `faith`), `culture_manager` (not `culture`), `character_memory_manager` (not `memories`) — the test asserts only what the file contains.
- Supporting tests: `test_parse_consumes_entire_file` (`:360`) — parser final position == 185,383,072 (braces balance at EOF, independent scan confirms depth 0); `test_last_root_block_parsed` (`:380`) — `confederation_manager` is the last root block; `test_root_block_count` (`:384`) — >60 root children.

### 3. Real title → province mapping assertions — exact names and file:line
- **`TestRealSaveMappingAssertions.test_c_nakhshab_maps_to_province_5673`** — `tests/test_economy_extract.py:406`
- **`TestRealSaveMappingAssertions.test_c_dabusiya_maps_to_province_5683`** — `tests/test_economy_extract.py:413`
- **`test_domain_county_count_is_5`** (`:420`), **`test_domain_province_count_is_5`** (`:424`), **`test_holding_type_none_reported_as_missing`** (`:428` — proves `holding_type` is Python `None`, not the string `"None"`).
- All passed against the real save: `c_nakhshab → 5673`, `c_dabusiya → 5683`.

### 4. Test count breakdown
| File | Count |
|---|---|
| `tests/test_extract_save.py` (stage 1) | **32** |
| `tests/test_economy_extract.py` (stage 2) | **22** |
| — mandatory fixture cases (`TestEconomyExtraction`) | 11 (`:177`, tests `:191–286`) |
| — rgb regression (`TestParserRgbBug`) | 1 (`:295`) |
| — real-save root blocks + EOF (`TestRealSaveRootBlocks`) | 4 (`:350`) |
| — real-save mapping assertions (`TestRealSaveMappingAssertions`) | 5 (`:390`) |
| — real-save integration (`TestRealSaveIntegration`) | 1 (`:436`) |
| **Total (pytest run)** | **54 passed** |

### 5. Full test command and exit code
```text
python -m pytest tests/ -q --no-header
→ 54 passed in 80.32s   Exit Code: 0
```
(Fixture-only subset: `python -m pytest tests/test_economy_extract.py -k "not Real" -q` → 12 passed, exit 0.)

### 6. Real-save tests skip cleanly when melted.txt is absent
- All three real-save classes gate `setUp` on `_load_real_save()` (`tests/test_economy_extract.py:22`) → `self.skipTest('reports/melted.txt not found')`.
- Verified by simulation (monkeypatched `os.path.isfile`, real file untouched): all three raised `unittest.SkipTest` with the message above. The suite is portable to a machine without the 190 MB file.
- The 185 MB file is parsed **once per suite run** (`_REAL_ROOT_CACHE`, keyed by path+mtime+size at `:19`) — previously three `setUp` parses cost ~235 s; now the whole suite runs in ~80 s.

### 7. Diff scope proof (current file vs your staged `:extract_save.py`, function-body diff)
- **Legacy functions identical to staged**: none changed by stage 2 itself; remaining deltas are all stage-1 mandates, each pinned by tests:
  - `extract_state` (+115/−66) — stage-1 rewrite; behavior pinned by `TestExtractStateBehaviorPreserved` (`tests/test_extract_save.py:262`).
  - `build_report` (+56/−60), `cmd_list` (+3/−2), `cmd_melt` (+5/−6), `main` (+6/−9), `melt_save` (−5 comment lines) — stage-1 autosave/path/report fixes, pinned by the same class + `TestAutosaveFilter`.
- **Stage-2 additions** (all new, nothing removed): `_get_node`, `_scalar_val`, `_list_items`, `extract_domain`, `extract_counties`, `extract_provinces`, `build_economy_report` — plus the additive `cmd_extract` hook (+17 lines, wrapped in try/except so the legacy report can never break).
- **No premature stage-3/4 code**: zero functions matching `extract_war|extract_faction|extract_military|extract_succession|extract_character` (grep count 0; the only "faction" hit is a stage-1 docstring example).
- `_title_keys` (a legacy `text.find`+regex helper) was absorbed into the stage-1 `extract_state` rewrite — not a stage-2 removal.
- One hygiene fix found during this audit: `get_latest_save` was defined twice with identical bodies (`:441` and `:1058`) — duplicate removed; stage-1 suite re-run green (32 passed).

---

## Stage-2 implementation evidence

### Extractor API (file:line)
- `_get_node` / `_scalar_val` / `_list_items`: `extract_save.py:501/511/518` (re-verified post-stage-4)
- `extract_domain`: `extract_save.py:529` — `played_character.character` → `living.<pid>.landed_data.domain` → join against `landed_titles.landed_titles` (title ID → key/tier/name/holder/capital)
- `extract_counties`: `extract_save.py:587` — `county_manager.counties` joined with landed_titles (holder, capital, de_jure_liege)
- `extract_provinces`: `extract_save.py:623` — `provinces` filtered by domain-county capital map; holdings from `holding` blocks; buildings from `holding.buildings` object-list; constructions from `construction` blocks
- `build_economy_report`: `extract_save.py:680` — appended to `state_report.txt` by `cmd_extract` (`extract_save.py:1796`, hook at `:1810–1817`; re-verified post-stage-4)

### Tests executed
```text
python -m pytest tests/ -q --no-header → 54 passed, Exit Code 0
```
All 10 mandatory fixture cases green (`tests/test_economy_extract.py:191–286`): multiple tiers; domain county+barony; county_manager development/control; province holding+buildings; construction in progress; county without development (missing ≠ 0); similar provinces not confused; no first-match error; domain_count counts c_ only; report generation. Plus domain-province filtering (`:286`).

### Real-save run (`reports/melted.txt`, 185,383,072 chars)
```text
parser consumed 185383072/185383072 (FULL)   root unique names=67
domain title IDs=11   mapped=11   domain c_ counties=5
county_manager entries=2652   domain provinces=5
building instances (domain)=6
missing county fields=0   missing holding_type=3
  c_bukhara:   prov=5659 type=None            income=0      buildings=[]
  c_nakhshab:  prov=5673 type=city_holding    income=0      buildings=[city_01, guild_halls_02, quarries_02]
  c_dabusiya:  prov=5683 type=church_holding  income=1.07298 buildings=[temple_01, hunting_grounds_02, monastic_schools_02]
  c_samarkand: prov=5688 type=None            income=0      buildings=[]
  c_khojand:   prov=5757 type=None            income=0      buildings=[]
```
Clarification on "67": that is **unique root names**; total root occurrences (mostly repeated `triggered_event` blocks preserved in `same_name`) is ~20,388.

### Not yet extractable (reported as missing/unknown, never guessed)
- **Building level**: the save stores `{ type=castle_01 }` with no level field → `"unknown"`.
- **Building classification** (economic/military/defensive): requires game-data lookup absent from the save.
- **3 domain provinces** (c_bukhara, c_samarkand, c_khojand) have no holding type/owner/levy/garrison in the save — reported as missing (Python `None`, rendered as `missing` in the report), proven by `test_holding_type_none_reported_as_missing`.

### Files outside scope — unchanged
`AGENTS.md`, `docs/*`, `tools/rakaly.exe`, `.agents/*`, `parsed_docs.txt`, all skill files.

READY FOR HUMAN VERIFY
