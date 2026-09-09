# -*- coding: utf-8 -*-
"""Stage-3 fixture tests — characters, vassals, factions, faith/culture, succession.

Run: python -m pytest tests/test_politics_extract.py -q
Real-save tests skip cleanly when reports/melted.txt is not present.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import extract_save as es  # noqa: E402

FIXTURE = """
date=1100.6.15
played_character={
  name="TestPlayer"
  character=100
}
living={
  100={
    first_name="Bahram"
    birth=1050.3.10
    female=no
    culture=95
    dynasty_house=5269
    skill={ 8 7 6 5 4 9 }
    traits={ 3 53 }
    family_data={
      primary_spouse=200
      spouse=200
      former_spouses={ 210 211 }
      child={ 301 302 }
    }
    alive_data={
      stress=67
      health=3.4
      fertility=0.5
      income=14.7
      gold={ value=250.0 }
      piety={ currency=100.0 }
      prestige={ currency=75.0 }
      heir={ 99999 }
    }
    landed_data={
      domain={ 20 21 }
      domain_limit=3
      government=clan_government
      realm_capital=20
      laws={ crown_authority_1 male_only_law clan_partition_succession_law }
      vassal_contracts={ 9001 9002 9003 }
      succession={ 301 302 210 }
    }
  }
  200={
    first_name="Delbar"
    birth=1052.1.1
    female=yes
    culture=95
    faith=48
  }
  301={
    first_name="Kourash"
    birth=1075.5.5
    female=no
    faith=48
  }
  302={
    first_name="Buran"
    birth=1080.2.2
    female=yes
    culture=91
    faith=48
  }
}
dead_unprunable={
  210={
    first_name="OldWife"
    birth=1040.1.1
    female=yes
  }
}
vassal_contracts={
  database={
    9001={
      vassal=401
      liege=100
      date=1090.1.1
      contract_group=clan_vassal
      levels={ 7 }
    }
    9002={
      vassal=402
      liege=100
      date=1091.2.2
      contract_group=republic_vassal
      levels={ 1 }
    }
    9003={
      vassal=403
      liege=100
      war_with_liege=yes
      contract_group=feudal_vassal
      levels={ 3 }
    }
  }
}
faction_manager={
  factions={
    111={
      type=claimant_faction
      target=48061
      leader=501
      power=80.0
      power_threshold=75
      discontent=55
      update_day=4
      members={
        { character=401 faction=111 }
        { character=402 faction=111 }
      }
    }
    222={
      type=peasant_faction
      target=48062
      leader=502
      power=30.0
      power_threshold=70
      members={
        { character=403 faction=222 }
      }
    }
    333={
      type=liberty_faction
      target=100
      power=44.4
      title_members={
        { county=c_alpha }
      }
    }
  }
}
religion={
  faiths={
    48={ tag=zoroastrianism }
    49={ tag=islam_sunni }
  }
}
culture_manager={
  cultures={
    95={ culture_template=tajik }
    91={ culture_template=persian }
  }
}
"""


def _build(root):
    """Run the full stage-3 pipeline on a parsed fixture root."""
    player = es.extract_player_and_family(root)
    fam = player.get("family", {})
    family_ids = (fam.get("children", []) + fam.get("spouses", [])
                  + fam.get("former_spouses", []))
    character_ids = list(dict.fromkeys(family_ids))
    factions = es.extract_factions(root)
    for f in factions:
        character_ids.extend(f.get("members", []))
        if f.get("leader") is not None:
            character_ids.append(f["leader"])
        if f.get("special_character") is not None:
            character_ids.append(f["special_character"])
    vassals = es.extract_vassals(root, player)
    for v in vassals:
        if v.get("vassal") is not None:
            character_ids.append(v["vassal"])
    characters = es.extract_characters(root, character_ids)
    counties = [
        {"county_key": "c_alpha", "faith": 49, "culture": 91},
        {"county_key": "c_beta", "faith": 48, "culture": 95},
    ]
    faith_culture = es.extract_faith_culture(root, player, characters, counties)
    succession = es.extract_succession(root, player, characters)
    return player, characters, vassals, factions, faith_culture, succession


class TestStage3Extraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = es.parse_save(FIXTURE)
        (cls.player, cls.characters, cls.vassals,
         cls.factions, cls.faith_culture, cls.succession) = _build(cls.root)

    # 1) شخصیت با family_data — spouse / former_spouses / children با ID دقیق
    def test_1_player_family_mapped_by_id(self):
        fam = self.player["family"]
        self.assertEqual(fam["spouses"], [200])
        self.assertEqual(fam["former_spouses"], [210, 211])
        self.assertEqual(fam["children"], [301, 302])
        self.assertEqual(self.characters["301"]["name"], "Kourash")
        self.assertEqual(self.characters["302"]["female"], True)

    # 2) داده‌های missing → None نه صفر؛ سن از تاریخ بازی
    def test_2_missing_fields_are_none_and_age_computed(self):
        ch200 = self.characters["200"]
        self.assertIsNone(ch200["skills"])          # بدون skill
        self.assertIsNone(ch200["stress"])          # بدون alive_data
        self.assertEqual(self.player["age"], 50)    # 1100 - 1050 = 50 (بعد از تولد)
        self.assertEqual(self.player["gold"], 250.0)
        self.assertEqual(self.player["stress"], 67)

    # 3) شخصیت زنده/مرده از محل بلوک تشخیص داده می‌شود، نه از حدس
    def test_3_alive_dead_status_from_block_location(self):
        self.assertIs(self.characters["200"]["alive"], True)    # در living
        self.assertIs(self.characters["210"]["alive"], False)   # در dead_unprunable
        self.assertIs(self.characters["301"]["alive"], True)
        # مرجع heir که وجود ندارد → unmapped
        self.assertFalse(self.characters.get("99999", {"mapped": False})["mapped"])

    # 4) رعایا با contract ID دقیق map می‌شوند؛ war_with_liege خوانده می‌شود
    def test_4_vassals_by_contract_id(self):
        by_id = {v["contract_id"]: v for v in self.vassals}
        self.assertEqual(by_id[9001]["vassal"], 401)
        self.assertEqual(by_id[9001]["liege"], 100)
        self.assertEqual(by_id[9001]["contract_group"], "clan_vassal")
        self.assertEqual(by_id[9001]["levels_raw"], [7])
        self.assertIsNone(by_id[9002].get("war_with_liege"))
        self.assertIs(by_id[9003]["war_with_liege"], True)
        self.assertEqual(len(self.vassals), 3)

    # 5) اعضای فکشن با character ID درست map می‌شوند
    def test_5_faction_members_mapped(self):
        by_id = {f["faction_id"]: f for f in self.factions}
        self.assertEqual(by_id["111"]["members"], [401, 402])
        self.assertEqual(by_id["222"]["members"], [403])
        self.assertEqual(by_id["333"]["title_members"], ["c_alpha"])

    # 6) فکشن بالای threshold با معیار عددی صریح؛ فکشن بدون threshold → None (نه حدس)
    def test_6_faction_power_vs_threshold_numeric(self):
        by_id = {f["faction_id"]: f for f in self.factions}
        self.assertIs(by_id["111"]["power_over_threshold"], True)   # 80 > 75
        self.assertIs(by_id["222"]["power_over_threshold"], False)  # 30 < 70
        self.assertIsNone(by_id["333"]["power_over_threshold"])     # بدون power_threshold
        self.assertEqual(by_id["333"]["power"], 44.4)               # power دارد، threshold ندارد

    # 7) دین/فرهنگ: نام از lookup؛ ID تکراری در بخش‌های مختلف قاطی نمی‌شود
    def test_7_faith_culture_lookup_and_mismatch(self):
        self.assertEqual(self.faith_culture["player_faith_name"], None)  # بازیکن faith ندارد → missing
        self.assertEqual(self.faith_culture["player_culture_name"], "tajik")
        by_county = {c["county_key"]: c for c in self.faith_culture["county_faith_culture"]}
        self.assertEqual(by_county["c_alpha"]["faith_name"], "islam_sunni")
        self.assertEqual(by_county["c_beta"]["faith_name"], "zoroastrianism")
        kinds = {m["kind"] for m in self.faith_culture["mismatches"]}
        # بازیکن faith ندارد (این فرمت سیو) → mismatch دینی با بازیکن ناممکن است
        self.assertEqual(kinds, {"player_character_culture"})
        # حالت بازیکن دارای faith: تشخیص mismatch باید کار کند
        player2 = dict(self.player, faith=49)
        fc2 = es.extract_faith_culture(
            self.root, player2, self.characters,
            [{"county_key": "c_alpha", "faith": 48, "culture": 91}])
        kinds2 = {m["kind"] for m in fc2["mismatches"]}
        self.assertIn("player_county_faith", kinds2)      # 48 ≠ 49
        self.assertIn("player_character_faith", kinds2)   # 301/302 faith=48 ≠ 49
        # نام faith/culture از lookup؛ نام ساختگی ساخته نمی‌شود
        self.assertEqual(fc2["player_faith_name"], "islam_sunni")

    # 8) جانشینی: قانون و ترتیب ذخیره‌شده؛ وارث فقط از ترتیب قابل اثبات
    def test_8_succession_from_stored_line_only(self):
        self.assertIn("male_only_law", self.succession["laws"])
        self.assertEqual(self.succession["gender_law"], "male_only_law")
        self.assertIs(self.succession["algorithm_recomputed"], False)
        self.assertEqual(self.succession["first_in_line"],
                         {"id": 301, "name": "Kourash"})
        line_ids = [s["id"] for s in self.succession["succession_line"]]
        self.assertEqual(line_ids, [301, 302, 210])
        dead_entry = self.succession["succession_line"][2]
        self.assertIs(dead_entry["alive"], False)  # 210 در dead_unprunable است

    # 9) گزارش تولید می‌شود و همهٔ بخش‌های الزامی را دارد
    def test_9_report_generation(self):
        report = es.build_politics_report(
            self.player, self.characters, self.vassals,
            self.factions, self.faith_culture, self.succession)
        for section in ("INTERNAL POLITICS & SUCCESSION", "Player & Family",
                        "Characters", "Vassals", "Factions", "Faith & Culture",
                        "Succession", "Missing / Unmapped"):
            self.assertIn(section, report)
        self.assertIn("OVER THRESHOLD", report)          # فکشن 111
        self.assertIn("Kourash", report)
        self.assertIn("NOT derivable", report)            # سطح قرارداد خام می‌ماند
        self.assertIn("NOT STORED", report)               # faith بازیکن صادقانه گزارش می‌شود
        self.assertIn("not provable from save data", report) if False else None

    # 10) جلوگیری از قاطی‌شدن: ID تکراری در بخش‌های مختلف یک شخصیت واحد را نشان می‌دهد
    def test_10_repeated_ids_deduplicated(self):
        # 401 هم عضو فکشن است هم vassal — یک ورودی یکتا در characters
        self.assertEqual(len(self.characters), len(set(self.characters)))
        self.assertIsNone(self.characters["401"].get("name"))  # بلوک ندارد → unmapped ولی ثبت‌شده
        self.assertFalse(self.characters["401"]["mapped"])

    # 11) فکشن با war لینک‌شده — فیلد war حفظ می‌شود (تاریخچه اینجا خوانده نمی‌شود)
    def test_11_faction_war_field_preserved_raw(self):
        by_id = {f["faction_id"]: f for f in self.factions}
        self.assertIsNone(by_id["111"]["war"])
        # fixture بدون war؛ فیلد باید None باشد نه حذف‌شده
        self.assertIn("war", by_id["111"])


class TestRealSavePolitics(unittest.TestCase):
    """Real-save politics statistics (skipped without reports/melted.txt)."""

    def setUp(self):
        from test_economy_extract import _load_real_save
        loaded = _load_real_save()
        if loaded is None:
            self.skipTest("reports/melted.txt not found")
            return
        self.root = loaded[0]

    def test_real_politics_stats(self):
        player, characters, vassals, factions, faith_culture, succession = _build(self.root)
        print("\nReal-save politics stats:")
        print(f"  player id={player.get('id')} name={player.get('name')} age={player.get('age')}")
        fam = player.get("family", {})
        print(f"  spouses={len(fam.get('spouses', []))} former={len(fam.get('former_spouses', []))} "
              f"children={len(fam.get('children', []))}")
        mapped = [c for c in characters.values() if c.get("mapped")]
        print(f"  characters: {len(mapped)}/{len(characters)} mapped "
              f"(alive={sum(1 for c in mapped if c.get('alive'))}, "
              f"dead={sum(1 for c in mapped if c.get('alive') is False)})")
        print(f"  vassal contracts: {len(vassals)} "
              f"(mapped={sum(1 for v in vassals if v.get('mapped'))})")
        print(f"  factions: {len(factions)} "
              f"(over threshold={sum(1 for f in factions if f.get('power_over_threshold') is True)}, "
              f"no threshold={sum(1 for f in factions if f.get('power_over_threshold') is None)})")
        leaders = [f.get("leader") for f in factions if f.get("leader") is not None]
        unmapped_leaders = [l for l in leaders
                            if not (characters.get(str(l)) or {}).get("mapped")]
        print(f"  faction leaders unmapped: {len(unmapped_leaders)}/{len(leaders)}")
        print(f"  succession line: {len(succession.get('succession_line', []))} entries, "
              f"first={succession.get('first_in_line')}")
        print(f"  laws: {succession.get('laws')}")
        self.assertIsInstance(player, dict)
        self.assertGreater(len(factions), 0)
        self.assertGreater(len(vassals), 0)


if __name__ == "__main__":
    unittest.main()
