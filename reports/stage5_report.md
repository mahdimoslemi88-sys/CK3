# گزارش مرحلهٔ ۵ — دسیسه، روابط، دودمان و اشیاء (تأیید‌شده)

**VERIFY: PASS** — human verification received. All findings below re-verified against the
final code and the live save (game date **947.1.1**, `autosave.ck3`).

## Extraction API (final anchors, current file)

- `extract_schemes`: `extract_save.py:2056` — `schemes.active`; sentinel `4294967295` filtered;
  missing type counted **globally** (not related-only); honest `None` defaults
- `extract_secrets`: `extract_save.py:2137` — `secrets.secrets`; participants parsed from
  list **or** numbered-block containers; sentinel/None dropped
- `extract_relations`: `extract_save.py:2174` — `relations.active_relations` flattened via
  `as_list()` (anonymous list-children — the stage-3 `vassal_contracts` trap); nested
  `alliances` list-of-blocks (`allied_through_*`) and `active_hook_1` (`type`,
  `expiration_date`) read; alliance IDs included in relevance
- `extract_dynasties`: `extract_save.py:2235` — direct dynasty lookup **plus** house→dynasty
  resolution via `dynasties.dynasty_house.<id>.dynasty`; resolved IDs emitted as
  `house_id`/`id` separately (never conflated)
- `extract_artifacts`: `extract_save.py:2273` — join on `artifacts.artifacts[].owner`
  vs family set; `is_equipped` explicitly `"missing"` (inventory absent from character
  blocks — proven by scan of 60,997 blocks); `missing_owner` counted
- Wiring: `extract_save.py:1956` (`p_dyn_id = player.get("dynasty_house")`,
  character-row fallback), `:1977` (text report append), `:1981` (snapshot)
- Quality: `missing_counts` (`schemes_missing_type`, `artifacts_missing_owner`) +
  provenance (`save_file_name`, `extraction_time`) at `:1476–1479`

## Structural facts discovered (recorded, not guessed)

1. **No `character`/`character_entries` root block exists** — characters live in
   `root.living` / `dead_unprunable`. The original artifacts extractor's path was dead code
   (first audit).
2. **`relations.active_relations.children` is a list** of 18,061+ anonymous rows — the
   original `.items()` iteration silently inspected zero rows (first audit).
3. **House ≠ dynasty**: on save 947.1.1 the player (Togmath, ID 16817309) heads a **newly
   founded house 50342506** (found_date 946.4.20, parent house 5269) whose `dynasty` link
   points to **dynasty 2657**. Direct `dynasties.dynasties` lookup fails; the chain resolves it.
4. Character-level `inventory`/lifestyle data is absent from this save format — reported
   missing, never zero-filled.
5. `player.id` was never added to `character_ids` — the character-row lookup could never
   find the player (fixed wiring).

## Real-save certified numbers (947.1.1, single melt→parse, exit 0)

```text
schemes:    6 related / 1528 total / 108 missing-type (global, in quality.missing_counts)
secrets:    5 related / 3709 total
relations: 25 related (16 with alliances, 4 with hooks) / 18530 total
dynasty:   {id: 2657, prestige: 1593.86, dynasty_head: 16817309 (player),
            perks: [fp3_khvarenah_legacy_1..4], house_id: 50342506}
artifacts:  4 related / 4414 total / 61 missing-owner (quality.missing_counts)
snapshots:  snapshot_945_1_1.json, snapshot_946_1_1.json, snapshot_947_1_1.json
            (trend analyst now has a real series)
```

JSON and `state_report.txt` numbers identical (pinned by test); text section:
`-- [5. Intrigue, Relations, Dynasty & Artifacts] --`.

## Tests

```text
python -m pytest tests/ -q   →  88 passed, Exit Code 0
```

Breakdown: 32 stage-1 + 22 stage-2 + 12 stage-3 + 11 stage-4 + 5 snapshot + 6 stage-5
(`tests/test_intrigue_diplomacy_extract.py` — incl. `test_relations_nested` modelling the
list-of-blocks alliances shape, global missing-type counter, honest `None` defaults,
list-perk parsing, participant containers, no-`character`-dependency for artifacts).
Count history 88→87→89→88 explained by the relations-fixture rework across fix passes;
final state re-collected and re-run three times, stable.

## Fix-pass history (both audits)

- **Audit 1** (VERIFY: FAIL): dead artifacts path, silent-zero relations iteration,
  dynasty wiring false excuse + int/str key bug, fabricated `'None'` strings, silent
  0-defaults, missing text section, stale shipped stats.
- **Audit 2**: relations payload (nested blocks) + relevance; `missing_counts`; provenance
  restore after quality-block rewrite; house→dynasty chain; player-id wiring. Final two
  edits applied by the auditing agent with exact-match patches, compile check, and full
  suite re-run (7/7 certification checks green).

## Honest limits

- Player lifestyle/perks/inventory: not stored on the player block in this format — missing.
- `is_equipped` per artifact: `"missing"` (no per-character inventory to join).
- Hook `type` semantics (e.g. `favor_hook`) kept raw — no game-data mapping applied.
- Scheme `missing_type` rows are counted globally; only related schemes are detailed.
