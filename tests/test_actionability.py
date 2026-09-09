# -*- coding: utf-8 -*-
"""Fixture tests — actionability phase: war-name cleanup, sentinel filter,
faction joins, player.resources, counties scope filter + world aggregates.

Run: python -m pytest tests/test_actionability.py -q
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import extract_save as es  # noqa: E402


def block(children=None):
    n = es.Node("block")
    n.children = {}
    for k, v in (children or {}).items():
        n.children[k] = v
    return n


def scalar(value, name=None):
    n = es.Node("scalar")
    n.value = value
    return n


def build_root(tree):
    """tree: nested dict of {name: node-or-dict} -> root block node."""
    root = es.Node("block")
    root.children = {}
    for k, v in tree.items():
        if isinstance(v, dict):
            root.children[k] = build_root(v)
        else:
            root.children[k] = v
    return root


class TestCleanWarName(unittest.TestCase):
    def test_strips_markup_and_extracts_refs(self):
        raw = "\x15ONCLICK:TITLE,6990 \x15TOOLTIP:LANDED_TITLE,6990 \x15L; name part \x15!\x15!"
        name, refs = es._clean_war_name(raw)
        self.assertIn("name part", name)
        self.assertNotIn("ONCLICK", name)
        self.assertNotIn("TOOLTIP", name)
        self.assertNotIn("\x15", name)
        self.assertEqual(refs, [{"kind": "title", "id": 6990}])

    def test_concept_tooltip_and_l_e_markers_removed(self):
        raw = "\x15ONCLICK:TITLE,9029 \x15L; abc \x15E; \x15TOOLTIP:GAME_CONCEPT,holy_war def"
        name, refs = es._clean_war_name(raw)
        self.assertNotIn("TOOLTIP", name)
        self.assertNotIn("GAME_CONCEPT", name)
        for token in name.split():
            self.assertNotIn(token, ("L", "E"), name)
        self.assertEqual(refs, [{"kind": "title", "id": 9029}])

    def test_character_refs_and_dedupe(self):
        raw = "a \x15ONCLICK:CHARACTER,5 \x15TOOLTIP:CHARACTER,5 \x15ONCLICK:CHARACTER,6"
        name, refs = es._clean_war_name(raw)
        self.assertEqual(refs, [{"kind": "character", "id": 5}, {"kind": "character", "id": 6}])

    def test_none(self):
        self.assertEqual(es._clean_war_name(None), (None, []))


class TestNoSentinel(unittest.TestCase):
    def test_sentinel_becomes_none(self):
        self.assertIsNone(es._no_sentinel(4294967295))

    def test_normal_value_passes(self):
        self.assertEqual(es._no_sentinel(42), 42)
        self.assertEqual(es._no_sentinel(0), 0)
        self.assertIsNone(es._no_sentinel(None))


class TestFactionJoins(unittest.TestCase):
    def _root(self, target_id, war_id=None, player_id=100):
        living = block()
        living.children[str(player_id)] = block()
        living.children[str(target_id)] = block()
        lt = block()
        lt.children["landed_titles"] = block({"555": block({"key": scalar("c_x")})})
        wars = block()
        aw = block()
        if war_id is not None:
            aw.children[str(war_id)] = block({"name": scalar("w")})
        wars.children["active_wars"] = aw
        f = block({
            "type": scalar("independence_faction"),
            "target": scalar(target_id),
            "power": scalar(50),
            "power_threshold": scalar(100),
        })
        if war_id is not None:
            f.children["war"] = scalar(war_id)
        factions = block({str(1): f})
        return build_root({
            "played_character": {"character": scalar(player_id)},
            "living": living,
            "landed_titles": {"landed_titles": lt},
            "faction_manager": {"factions": factions},
            "wars": wars,
        })

    def test_target_kind_character_and_player_flag(self):
        root = self._root(target_id=200)
        out = es.extract_factions(root)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["target_kind"], "character")
        self.assertFalse(out[0]["target_is_player"])

    def test_target_is_player_true(self):
        root = self._root(target_id=100)  # target == player id
        out = es.extract_factions(root)
        self.assertTrue(out[0]["target_is_player"])
        self.assertEqual(out[0]["target_kind"], "character")

    def test_civil_war_join(self):
        root = self._root(target_id=200, war_id=777)
        out = es.extract_factions(root)
        self.assertTrue(out[0]["is_civil_war"])

    def test_war_field_absent_means_false_not_none(self):
        root = self._root(target_id=200, war_id=None)
        out = es.extract_factions(root)
        self.assertIs(out[0]["is_civil_war"], False)

    def test_stale_war_id_is_not_civil_war(self):
        # faction references war 999, but only war 777 is active
        root = self._root(target_id=200, war_id=777)
        f = root.children["faction_manager"].children["factions"].children["1"]
        f.children["war"].value = 999
        out = es.extract_factions(root)
        self.assertFalse(out[0]["is_civil_war"])
        self.assertEqual(out[0]["war"], 999)


class TestResourcesBlock(unittest.TestCase):
    def _ad(self, gold=None, piety=None, prestige=None):
        ad = block()
        if gold is not None:
            ad.children["gold"] = block({"value": scalar(gold)})
        if piety is not None:
            ad.children["piety"] = block({
                "currency": scalar(piety), "accumulated": scalar(piety + 100),
            })
        if prestige is not None:
            ad.children["prestige"] = block({
                "currency": scalar(prestige), "accumulated": scalar(prestige + 200),
            })
        return ad

    def test_full_resources(self):
        r = es._resources_block(self._ad(gold=-49.7, piety=999.7, prestige=1081.7))
        self.assertEqual(r["gold"], -49.7)
        self.assertEqual(r["piety"], 999.7)
        self.assertEqual(r["piety_accumulated"], 1099.7)
        self.assertEqual(r["prestige"], 1081.7)
        self.assertEqual(r["prestige_accumulated"], 1281.7)

    def test_missing_resource_is_none_not_zero(self):
        r = es._resources_block(self._ad(gold=10.0))  # no piety/prestige blocks
        self.assertEqual(r["gold"], 10.0)
        self.assertIsNone(r["piety"])
        self.assertIsNone(r["prestige_accumulated"])

    def test_zero_is_preserved_as_zero(self):
        r = es._resources_block(self._ad(gold=0))
        self.assertEqual(r["gold"], 0)  # real zero must not become missing

    def test_empty_alive_data(self):
        self.assertEqual(es._resources_block(None), {})


class TestCountiesScope(unittest.TestCase):
    def _root(self, dom_ids=("5659",)):
        lt = block()
        lt.children["5659"] = block({
            "key": scalar("c_bukhara"),
            "holder": scalar(7),
            "capital": scalar(5659),
            "de_jure_liege": scalar(5658),
        })
        lt.children["600"] = block({"key": scalar("c_other"), "holder": scalar(8)})
        lt.children["700"] = block({"key": scalar("k_big"), "holder": scalar(9)})  # not a county
        cm = block()
        cm.children["c_bukhara"] = block({
            "development": scalar(15), "county_control": scalar(100.0),
            "culture": scalar(1), "faith": scalar(2),
        })
        cm.children["c_other"] = block({"development": scalar(5), "county_control": scalar(60.0)})
        return build_root({
            "county_manager": {"counties": cm},
            "landed_titles": {"landed_titles": lt},
        })

    def setUp(self):
        # reset module-level aggregates before each use
        if hasattr(es.extract_counties, "world_total"):
            del es.extract_counties.world_total

    def test_domain_filter_returns_only_domain_rows(self):
        root = self._root()
        rows = es.extract_counties(root, ["5659"])
        self.assertEqual([r["county_key"] for r in rows], ["c_bukhara"])
        self.assertEqual(rows[0]["title_id"], "5659")
        self.assertEqual(rows[0]["holder"], 7)
        self.assertTrue(rows[0]["mapped"])

    def test_world_aggregates_count_all_counties(self):
        root = self._root()
        es.extract_counties(root, ["5659"])
        self.assertEqual(es.extract_counties.world_total, 2)  # both c_ counties, not k_big
        self.assertEqual(es.extract_counties.world_dev_avg, 10.0)  # (15+5)/2
        self.assertAlmostEqual(es.extract_counties.world_ctrl_avg, 80.0)

    def test_no_filter_returns_all_rows(self):
        root = self._root()
        rows = es.extract_counties(root)  # legacy behavior
        self.assertEqual(len(rows), 2)

    def test_unmapped_county_row_is_honest(self):
        root = self._root()
        cm = root.children["county_manager"].children["counties"]
        cm.children["c_orphan"] = block({"development": scalar(3)})
        rows = es.extract_counties(root, [])  # empty domain filter = everything
        orphan = [r for r in rows if r["county_key"] == "c_orphan"][0]
        self.assertFalse(orphan["mapped"])
        self.assertIsNone(orphan["title_id"])


class TestWarsOutput(unittest.TestCase):
    def _root(self, name_raw, claimant=4294967295):
        aw = block({
            "1": block({
                "name": scalar(name_raw),
                "start_date": scalar("960.1.1"),
                "casus_belli": block({
                    "type": scalar("war"),
                    "attacker": scalar(10),
                    "defender": scalar(20),
                    "claimant": scalar(claimant),
                }),
                "attacker": block({"ticking_war_score": scalar(10)}),
                "defender": block({"ticking_war_score": scalar(-5)}),
            }),
        })
        return build_root({"wars": {"active_wars": aw}})

    def test_war_name_cleaned_and_refs_kept(self):
        out = es.extract_wars(self._root(
            "\x15ONCLICK:TITLE,9 \x15L; war name \x15!"))
        w = out[0]
        self.assertEqual(w["name"], "war name")
        self.assertEqual(w["name_refs"], [{"kind": "title", "id": 9}])

    def test_name_raw_preserved_for_audit(self):
        raw = "\x15ONCLICK:TITLE,9 \x15L; war name"
        out = es.extract_wars(self._root(raw))
        self.assertEqual(out[0]["name_raw"], raw)

    def test_cb_claimant_sentinel_is_none(self):
        out = es.extract_wars(self._root("plain name", claimant=4294967295))
        self.assertIsNone(out[0]["cb_claimant"])

    def test_cb_claimant_real_id_passes(self):
        out = es.extract_wars(self._root("plain name", claimant=12345))
        self.assertEqual(out[0]["cb_claimant"], 12345)


if __name__ == "__main__":
    unittest.main()
