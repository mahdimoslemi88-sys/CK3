# -*- coding: utf-8 -*-
"""تست‌های فاز ۱ — اسنپ‌شات وضعیت (reports/history/).

اجرا:
    python -m pytest tests/test_snapshot.py -q
"""

import os
import sys
import json
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import extract_save as es  # noqa: E402


def _state(game_date="1100.3.15"):
    return {"meta": {"game_date": game_date, "save_file": "x.ck3"},
            "player": {"gold": 100}, "quality": {"counts": {"domain_count": 5}}}


class TestSaveStateSnapshot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_snapshot_written_named_by_game_date(self):
        out = es.save_state_snapshot(_state(), reports_dir=self.tmp)
        self.assertTrue(out)
        name = os.path.basename(out)
        self.assertEqual(name, "snapshot_1100_3_15.json")
        self.assertTrue(os.path.dirname(out).endswith("history"))
        with open(out, encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["player"]["gold"], 100)

    def test_same_game_date_overwrites_not_duplicates(self):
        es.save_state_snapshot(_state(), reports_dir=self.tmp)
        state2 = _state()
        state2["player"]["gold"] = 250
        out2 = es.save_state_snapshot(state2, reports_dir=self.tmp)
        files = os.listdir(os.path.join(self.tmp, "history"))
        self.assertEqual(files, ["snapshot_1100_3_15.json"])
        with open(out2, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["player"]["gold"], 250)

    def test_new_game_date_creates_new_snapshot_file(self):
        es.save_state_snapshot(_state("1100.3.15"), reports_dir=self.tmp)
        es.save_state_snapshot(_state("1101.1.2"), reports_dir=self.tmp)
        files = sorted(os.listdir(os.path.join(self.tmp, "history")))
        self.assertEqual(files,
                         ["snapshot_1100_3_15.json", "snapshot_1101_1_2.json"])

    def test_missing_game_date_writes_nothing(self):
        out = es.save_state_snapshot({"meta": {}}, reports_dir=self.tmp)
        self.assertEqual(out, "")
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "history")))

    def test_never_raises_on_bad_input(self):
        self.assertEqual(es.save_state_snapshot(None, reports_dir=self.tmp), "")
        self.assertEqual(es.save_state_snapshot({"meta": {"game_date": 12345}},
                                                reports_dir=self.tmp), "")


if __name__ == "__main__":
    unittest.main()
