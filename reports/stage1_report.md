# Stage 1 Report — Structural Parser & Input Hardening

## Modified files
- `extract_save.py` (470 → 1,940 lines after stages 1–4; stage-1 portion ≈ lines 87–518)
- `tests/test_extract_save.py` (new, 32 tests)
- `reports/stage1_report.md` (this report only)

*(Line refs below re-verified against the final post-stage-4 file during the closing audit.)*

## Summary of changes

### 1. Structural Parser (`extract_save.py:102–391`)
- `Node` class (`extract_save.py:102`): kind = scalar | list | block; holds value, children (dict for block / list for object-list), and `same_name` for repeated blocks.
- `SaveParser` (`extract_save.py:185`): brace-counting recursive descent, indentation-independent, quote/escape-aware (`extract_save.py:182` `_ESCAPES`, `_read_quoted` `:219`). The new parser uses no global regex over the save body; the legacy `extract_state` regex paths remain temporarily and are migrated in stages 2–4.
- `parse_save(text)` entry point (`extract_save.py:384`).

### 2. Internal API (`extract_save.py:384–391`, `:445–489`)
- `find_root` (`:445`), `find_child` (`:450`), `find_child_by_id` (`:455`), `read_scalar` (`:472`), `read_list` (`:481`), `read_object_list` (`:489`).
- Missing field = `None` everywhere; empty list = `[]` — never conflated.

### 3. Input hardening (`extract_save.py:393–434`)
- `SavePathError` (`:393`), `resolve_save_path` (`:397`): canonical containment vs `SAVE_DIR`, `.ck3`-only, symlink/junction containment, regular-file check.
- `cmd_extract` (`extract_save.py:1796`) and `cmd_melt` (`extract_save.py:1905`) route through `resolve_save_path` / `_auto_pick_save` — no raw path usage.

### 4. autosave_exit (`extract_save.py:436–441`, `:1769–1788`, `:1888`)
- `_autosave_filtered` (`:436`), `get_latest_save` (`:1769`), `_auto_pick_save` (`:1888`), `cmd_list` annotation (`:1779`).

### 5. Behavior preserved
- `list` / `extract` / `melt` output preserved; `reports/state_report.txt` + `reports/melted.txt` still produced.

## Real-save smoke test
- The original smoke test (`1.79 s, 468,828 nodes`) ran against a **truncated tree** — see the supplementary correction below. The corrected full-file parse: **185,383,072 chars, parser consumed position = file length (FULL), 67 unique root names, ~67 s**, exit 0.

## Tests executed
- `python -m pytest tests/test_extract_save.py -q` → **32 passed** (Exit Code 0)
- Covered: nested blocks, scalars, lists, object lists, repeated blocks, quotes/escapes, missing field, real zero, path traversal, extension rejection, autosave exclusion, `extract_state` behavior preservation.

## Supplementary correction (registered during stage-2 audit, 2026-09-02)
The stage-1 smoke test was insufficient: the parser **terminated early** on `color=rgb { 181 87 216 }` — after reading the bare scalar `rgb`, the parser hit `{` at field-name position, mangled the triplet, and the stray `}` ended the root loop at char 7.26M of 185M. Only 18 of 67 unique root names were parsed; `county_manager`, `wars`, `dynasties`, `character_lookup` and most of `landed_titles` were missing. Exit Code 0 proved only "no crash", not correctness.

**Fix** (`extract_save.py:350–354`, in `_parse_block_body`): `{` following a bare scalar value is now parsed as that field's list value (stored as `__anon__`), so parsing continues past such constructs. Proof: parser consumed position = full file length; all required root blocks present; regression tests `TestParserRgbBug.test_rgb_value_consumed_and_parsing_continues` (`tests/test_economy_extract.py:295`) and `TestRealSaveRootBlocks.test_parse_consumes_entire_file` (`tests/test_economy_extract.py:360`).

## Files outside scope — unchanged
- `AGENTS.md`, `docs/*`, `tools/rakaly.exe`, all skill files.

## Remaining for stage 2
- Structural extraction of domain / counties / provinces / holdings / buildings
- Real-save statistics on `reports/melted.txt`

*(Stage-1 verification passed; the supplementary correction above was audited and accepted during the stage-2 review.)*
