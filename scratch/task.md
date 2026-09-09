# Stage 5 Plan: Intrigue, Relations, Dynasty & Artifacts

## 1. Parse Logic & Helpers (Data extraction)
- [x] Add `extract_schemes()` inside `extract_save.py`
  - Parse `root.schemes.active`
  - Count all schemes
  - Keep only player/family related (owner/target/agent)
  - Handle missing `type` (52 items)
  - Ignore `4294967295` sentinel for characters
- [x] Add `extract_secrets()`
  - Parse `root.secrets.secrets` and `root.secrets.known_secrets`
  - Flatten `known_secrets` list
  - Keep only player/family related (owner/participants)
- [x] Add `extract_relations()`
  - Parse `root.relations.active_relations`
  - Filter for player/family as `first` or `second`
  - Include alliances (`allied_through_0/1`) and hooks (`active_hook_1`)
  - Keep `9999.1.1` as no-expiration
- [x] Add `extract_dynasties()`
  - Parse `root.dynasties.dynasties` and `root.dynasties.dynasty_house`
  - Count all dynasties
  - Extract player's dynasty fully (prestige, head, perks)
- [x] Add `extract_artifacts()`
  - Parse `root.artifacts.artifacts`
  - Find equipped/owned via character inventory block
- [x] Update character extraction for `lifestyle_xp`
  - Return missing if not present for player

## 2. Integration & Testing
- [x] Add fixtures & unit tests in `tests/test_intrigue_diplomacy_extract.py`
  - 10 required edge cases (sentinel, missing type, 9999 date, flat list, missing xp, player filtering)
- [x] Integrate into `build_state_json()`
  - Append output to `state_report.json`
  - Ensure total JSON size doesn't exceed 2x

## 3. Human Verify Phase
- [x] Stop execution, report paths/counts, and present `READY FOR HUMAN VERIFY`
