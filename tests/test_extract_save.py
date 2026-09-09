# -*- coding: utf-8 -*-
"""تست‌های مرحلهٔ ۱ — Parser ساختاری، ایمن‌سازی ورودی، فیلتر autosave_exit.

اجرا:
    python -m pytest tests/test_extract_save.py -q
یا:
    python -m unittest tests.test_extract_save
"""

import io
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import extract_save as es  # noqa: E402


# ----------------------------------------------------------
# 1) block تو‌در‌تو
# ----------------------------------------------------------
class TestNestedBlocks(unittest.TestCase):
    def test_deeply_nested_blocks(self):
        text = "a={ b={ c={ d=1 } e=2 } f=3 }"
        root = es.parse_save(text)
        self.assertEqual(root.get("a").get("b").get("c").get("d").as_int(), 1)
        self.assertEqual(root.get("a").get("b").get("e").as_int(), 2)
        self.assertEqual(root.get("a").get("f").as_int(), 3)

    def test_indentation_independent(self):
        one = es.parse_save("a={b=1\nc=2}")
        two = es.parse_save("a={\n\t\tb=1\n\t\t\tc=2\n}")
        self.assertEqual(one.get("a").get("b").as_int(), two.get("a").get("b").as_int())
        self.assertEqual(one.get("a").get("c").as_int(), two.get("a").get("c").as_int())


# ----------------------------------------------------------
# 2) scalar رشته‌ای، عددی و yes/no
# ----------------------------------------------------------
class TestScalars(unittest.TestCase):
    def test_string_int_float_yesno(self):
        root = es.parse_save(
            'name="Bukhara" count=42 ratio=1.5 flag=yes off=no quoted="a=\\"x\\" n=1"'
        )
        self.assertEqual(root.get("name").as_str(), "Bukhara")
        self.assertEqual(root.get("count").as_int(), 42)
        self.assertEqual(root.get("ratio").as_float(), 1.5)
        self.assertIs(root.get("flag").as_bool(), True)
        self.assertIs(root.get("off").as_bool(), False)
        # escape حفظ مقدار شد
        self.assertEqual(root.get("quoted").as_str(), 'a="x" n=1')

    def test_bare_key_string(self):
        root = es.parse_save("key=c_bukhara")
        self.assertEqual(root.get("key").as_str(), "c_bukhara")


# ----------------------------------------------------------
# 3) list ساده
# ----------------------------------------------------------
class TestSimpleLists(unittest.TestCase):
    def test_simple_list(self):
        root = es.parse_save("ids={ 10 20 30 }")
        self.assertEqual(es.read_list(root, "ids"), [10, 20, 30])

    def test_empty_list_vs_missing(self):
        root = es.parse_save("empty={} missing_not_present=1")
        self.assertEqual(es.read_list(root, "empty"), [])
        self.assertIsNone(es.read_list(root, "nope"))  # نبودن فیلد


# ----------------------------------------------------------
# 4) object list
# ----------------------------------------------------------
class TestObjectLists(unittest.TestCase):
    def test_object_list_members(self):
        text = "members={ { character=123 faction=456 } { character=789 faction=111 } }"
        root = es.parse_save(text)
        members = es.read_object_list(root, "members")
        self.assertEqual(len(members), 2)
        self.assertEqual(members[0].get("character").as_int(), 123)
        self.assertEqual(members[0].get("faction").as_int(), 456)
        self.assertEqual(members[1].get("character").as_int(), 789)


# ----------------------------------------------------------
# 5) blockهای تکرارشونده با شناسه
# ----------------------------------------------------------
class TestRepeatedBlocks(unittest.TestCase):
    def test_repeated_same_name_kept_in_order(self):
        text = "army={ id=1 } army={ id=2 } army={ id=3 }"
        root = es.parse_save(text)
        armies = root.get_all("army")
        self.assertEqual([a.get("id").as_int() for a in armies], [1, 2, 3])

    def test_find_child_by_id(self):
        text = "char={ id=7 name=one } char={ id=9 name=two }"
        root = es.parse_save(text)
        hit = es.find_child_by_id(root, "char", 9)
        self.assertEqual(hit.get("name").as_str(), "two")
        self.assertIsNone(es.find_child_by_id(root, "char", 8))


# ----------------------------------------------------------
# 6) quote و escape
# ----------------------------------------------------------
class TestQuotesEscapes(unittest.TestCase):
    def test_quotes_and_escapes_preserve_value(self):
        root = es.parse_save(r'a="line1\nline2" b="tab\there" c="back\\slash" d="q\"uote"')
        self.assertEqual(root.get("a").as_str(), "line1\nline2")
        self.assertEqual(root.get("b").as_str(), "tab\there")
        self.assertEqual(root.get("c").as_str(), "back\\slash")
        self.assertEqual(root.get("d").as_str(), 'q"uote')

    def test_quoted_name_field(self):
        root = es.parse_save('"weird name"=5')
        self.assertEqual(root.get("weird name").as_int(), 5)


# ----------------------------------------------------------
# 7) نبودن فیلد (نه مقدار مبهم)
# ----------------------------------------------------------
class TestMissingFields(unittest.TestCase):
    def test_missing_is_detectable(self):
        root = es.parse_save("a=1")
        self.assertIsNone(root.get("nope"))
        self.assertIsNone(es.read_scalar(root, "nope"))
        self.assertIsNone(es.read_list(root, "nope"))
        self.assertIsNone(es.read_object_list(root, "nope"))

    def test_zero_is_not_missing(self):
        root = es.parse_save("gold=0 empty_list={ }")
        self.assertEqual(root.get("gold").as_int(), 0)
        self.assertEqual(es.read_list(root, "empty_list"), [])


# ----------------------------------------------------------
# 8) مقدار صفر واقعی
# ----------------------------------------------------------
class TestRealZero(unittest.TestCase):
    def test_zero_and_negative(self):
        root = es.parse_save("gold=0 debt=-12.5 stress=0.0")
        self.assertEqual(root.get("gold").as_int(), 0)
        self.assertEqual(root.get("debt").as_float(), -12.5)
        self.assertEqual(root.get("stress").as_float(), 0.0)


# ----------------------------------------------------------
# 9) ردکردن ../outside.ck3 (path traversal)
# ----------------------------------------------------------
class TestPathTraversal(unittest.TestCase):
    def test_reject_parent_traversal(self):
        with self.assertRaises(es.SavePathError):
            es.resolve_save_path("../outside.ck3")

    def test_reject_deep_traversal(self):
        with self.assertRaises(es.SavePathError):
            es.resolve_save_path("sub/../../../evil.ck3")

    def test_reject_absolute_outside(self):
        with self.assertRaises(es.SavePathError):
            es.resolve_save_path("C:/evil.ck3" if os.name == "nt" else "/evil.ck3")


# ----------------------------------------------------------
# 10) ردکردن پسوند غیر .ck3
# ----------------------------------------------------------
class TestExtension(unittest.TestCase):
    def test_reject_non_ck3(self):
        with self.assertRaises(es.SavePathError):
            es.resolve_save_path("save.txt")
        with self.assertRaises(es.SavePathError):
            es.resolve_save_path("save.ck3.exe")

    def test_traversal_without_extension_rejected(self):
        with self.assertRaises(es.SavePathError):
            es.resolve_save_path("../outside")


# ----------------------------------------------------------
# 11) حذف autosave_exit از انتخاب خودکار
# ----------------------------------------------------------
class TestAutosaveFilter(unittest.TestCase):
    def test_latest_skips_autosave_exit(self):
        with mock.patch.object(es.os, "path") as p:
            p.isdir.return_value = True
            with mock.patch.object(es.os, "listdir", return_value=[
                "autosave_exit.ck3", "ironman.ck3",
            ]):
                with mock.patch.object(es.os.path, "getmtime", side_effect=[1, 2]):
                    self.assertEqual(es.get_latest_save(), "ironman.ck3")

    def test_only_autosave_returns_empty(self):
        with mock.patch.object(es.os, "path") as p:
            p.isdir.return_value = True
            with mock.patch.object(es.os, "listdir", return_value=["autosave_exit.ck3"]):
                with mock.patch.object(es.os.path, "getmtime", return_value=1):
                    self.assertEqual(es.get_latest_save(), "")

    def test_autosave_picks_newest_non_autosave(self):
        with mock.patch.object(es.os, "path") as p:
            p.isdir.return_value = True
            # autosave جدیدتر است ولی نباید انتخاب شود
            with mock.patch.object(es.os, "listdir", return_value=[
                "autosave_exit.ck3", "old_save.ck3",
            ]):
                with mock.patch.object(es.os.path, "getmtime", side_effect=[10, 5]):
                    self.assertEqual(es._auto_pick_save(), os.path.join(es.SAVE_DIR, "old_save.ck3"))

    def test_list_marks_autosave_excluded(self):
        with mock.patch.object(es.os, "path") as p:
            p.isdir.return_value = True
            with mock.patch.object(es.os, "listdir", return_value=["autosave_exit.ck3"]):
                with mock.patch.object(es.os.path, "getmtime", return_value=1):
                    with mock.patch.object(es.os.path, "getsize", return_value=1024):
                        buf = io.StringIO()
                        with mock.patch.object(sys, "stdout", buf):
                            rc = es.cmd_list()
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("autosave_exit", out)
        self.assertIn("حذف‌شده از انتخاب خودکار", out)


# ----------------------------------------------------------
# 12) حفظ رفتار extract_state فعلی روی fixture کوچک
# ----------------------------------------------------------
MINI_SAVE = (
    'meta_date=1069.2.15\n'
    'meta_player_name="Bahram"\n'
    'meta_title_name="Count of Bukhara"\n'
    'meta_house_name="Bukhara Khuda"\n'
    'meta_player_tier=1\n'
    'played_character={ name="Bahram" character=1010 }\n'
    'traits_lookup={ cruel brave }\n'
    '1010={\n'
    '\tfirst_name="Bahram"\n'
    '\tbirth=1030.5.4\n'
    '\tfemale=no\n'
    '\tskill={ 8 6 5 4 3 7 }\n'
    '\ttraits={ 0 1 }\n'
    '\tspouse=2020\n'
    '\tchild={ 3030 3040 }\n'
    '\talive_data={\n'
    '\t\tstress=12.5\n'
    '\t\thealth=4.2\n'
    '\t\tgold={\n\t\t\tvalue=250.0\n\t\t}\n'
    '\t\tpiety={ currency=100.0 }\n'
    '\t\tprestige={ currency=75.0 }\n'
    '\t}\n'
    '\tlanded_data={\n'
    '\t\tdomain={ 5001 5002 }\n'
    '\t\tdomain_limit=6\n'
    '\t\tlaws={ feudal_government_male_only }\n'
    '\t\tcurrent_strength=1200\n'
    '\t\tstrength=1500\n'
    '\t\tlevy=900\n'
    '\t\tbalance=1.75\n'
    '\t\tvassal_contracts={ 6001 6002 }\n'
    '\t\twars={ 7001 }\n'
    '\t}\n'
    '\tplayable_data={\n'
    '\t\tknights={ 4040 4041 4042 }\n'
    '\t\tlegitimacy=88.5\n'
    '\t}\n'
    '}\n'
    '3030={\n'
    '\tfirst_name="Hormizd"\n'
    '\tbirth=1035.2.1\n'
    '\tfemale=no\n'
    '}\n'
    '3040={\n'
    '\tfirst_name="Buran"\n'
    '\tbirth=1040.7.11\n'
    '\tfemale=yes\n'
    '}\n'
    '5001={\n'
    '\tkey=c_bukhara\n'
    '}\n'
    '5002={\n'
    '\tkey=c_samarkand\n'
    '}\n'
)


class TestExtractStateBehaviorPreserved(unittest.TestCase):
    def setUp(self):
        self.st = es.extract_state(MINI_SAVE)

    def test_meta(self):
        self.assertEqual(self.st["date"], "1069.2.15")
        self.assertEqual(self.st["player_name"], "Bahram")
        self.assertEqual(self.st["player_id"], "1010")
        self.assertEqual(self.st["tier"], 1)

    def test_age_computed(self):
        self.assertEqual(self.st["age"], 38)  # 1069 - 1030، هنوز به 5 می نرسیده

    def test_family(self):
        self.assertEqual(self.st["spouse_count"], 1)
        self.assertEqual(self.st["children_count"], 2)
        self.assertEqual(self.st["sons_count"], 1)
        self.assertEqual(self.st["daughters_count"], 1)
        genders = {c["id"]: c["is_female"] for c in self.st["children"]}
        self.assertFalse(genders["3030"])
        self.assertTrue(genders["3040"])

    def test_domain_only_counties(self):
        # domain شامل فقط c_... ها می‌شود؛ barony (b_) شمرده نمی‌شود
        self.assertEqual(self.st["domain_count"], 2)
        keys = [k for k, _ in self.st["counties"]]
        self.assertEqual(keys, ["c_bukhara", "c_samarkand"])
        self.assertEqual(self.st["counties"][0][1], "بخارا")

    def test_military_and_wars(self):
        self.assertEqual(self.st["current_strength"], "1200")
        self.assertEqual(self.st["levy"], "900")
        self.assertEqual(self.st["knights_count"], 3)
        self.assertEqual(self.st["active_wars"], [7001])

    def test_report_generated(self):
        report = es.build_report(self.st)
        self.assertIn("بخارا", report)
        self.assertIn("ولایات مستقیم: 2 از 6", report)
        self.assertIn("جنگ فعال: بله (1 نبرد)", report)
        self.assertIn("2 فرزند پسر" if False else "1 فرزند پسر", report)

    def test_parser_agrees_with_regex_on_fixture(self):
        # Parser ساختاری همان domain_ids را می‌بیند (رفتار فعلی حفظ شده)
        root = es.parse_save(MINI_SAVE)
        landed = root.get("1010").get("landed_data")
        self.assertEqual(
            es.read_list(landed, "domain"),
            self.st["domain_ids"],
        )


# ----------------------------------------------------------
# Parser API داخلی — root/child/scalar
# ----------------------------------------------------------
class TestInternalAPI(unittest.TestCase):
    def test_find_root_and_child(self):
        root = es.parse_save("a={ b=1 }")
        self.assertIs(es.find_root(root), root)
        self.assertEqual(es.find_child(root, "a").get("b").as_int(), 1)
        self.assertIsNone(es.find_child(root, "zzz"))

    def test_read_scalar_default(self):
        root = es.parse_save("a=5")
        self.assertEqual(es.read_scalar(root, "a"), 5)  # scalar تبدیل‌شده (int)
        self.assertEqual(es.read_scalar(root, "nope", default="dflt"), "dflt")


if __name__ == "__main__":
    unittest.main()
