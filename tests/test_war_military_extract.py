# -*- coding: utf-8 -*-
"""Stage-4 fixture tests — active wars vs history, Men-at-Arms, knights,
rally points, council tasks, decision flags, missing military fields, JSON output.

Run: python -m pytest tests/test_war_military_extract.py -q
Real-save tests skip cleanly when reports/melted.txt is not present.
"""

import json
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
  important_decisions={
    hunt_decision=no
    feast_decision=yes
    hold_court_decision=no
  }
  active_court_tasks={
    physician_court_position=physician_task_1
  }
  rally_points={
    {
      province=20
      color=0
    }
    {
      province=21
      color=1
    }
  }
}
living={
  100={
    first_name="Bahram"
    birth=1050.3.10
    female=no
    alive_data={ stress=10 health=4.0 }
    landed_data={
      domain={ 20 }
      current_strength=1200
      strength=1500
      levy=900
      laws={ male_only_law }
      succession={ 301 }
    }
    playable_data={
      knights={ 401 402 }
    }
  }
  301={
    first_name="Kourash"
    birth=1075.5.5
    female=no
  }
  401={ first_name="Knight1" birth=1060.1.1 female=no }
  402={ first_name="Knight2" birth=1061.1.1 female=no }
}
wars={
  active_wars={
    7001={
      attacker={
        participants={ { character=100 date=1099.1.1 contribution={ 500 10 5 } } }
        ticking_war_score=2.5
      }
      defender={
        participants={ { character=900 date=1099.1.1 contribution={ 300 5 2 } } }
        ticking_war_score=-1.0
      }
      start_date=1099.1.1
      casus_belli={
        type=conquest_war
        attacker=100
        defender=900
        claimant=100
      }
      battle_results={
        { province=20 war_score=3.5 attacker_won=yes }
        { province=21 war_score=-0.8 attacker_won=no }
      }
      name=CONQUEST_WAR_NAME
    }
    7002={
      attacker={
        participants={ { character=901 date=1099.2.1 contribution={ 100 1 1 } } }
        ticking_war_score=0.0
      }
      defender={
        participants={ { character=902 date=1099.2.1 contribution={ 100 1 1 } } }
        ticking_war_score=0.0
      }
      start_date=1099.2.1
      casus_belli={ type=independence_war attacker=901 defender=902 }
      name=LIBERTY_WAR_NAME
    }
    7003=none
    7004={
      attacker={ participants={ { character=903 date=1099.3.1 } } }
      defender={ participants={ { character=904 date=1099.3.1 } } }
      start_date=1099.3.1
      casus_belli={ type=raid_war attacker=903 defender=904 }
      name=RAID_WAR_NAME
    }
  }
  names={ 1=HUNGARIAN_INVASION_WAR_NAME_BASE }
}
opinions={
  active_opinions={
    {
      owner=900
      target=100
      temporary_opinion={
        modifier="paid_tribute"
        expiration_date=1101.1.1
        value=10
      }
      temporary_opinion={
        modifier="rival_insult"
        expiration_date=1102.1.1
        value=-3
      }
      temporary_opinion={
        modifier="gift_opinion"
        expiration_date=1103.1.1
        value=8
      }
    }
    {
      owner=100
      target=301
      temporary_opinion={
        modifier="friend_opinion"
        expiration_date=1101.1.1
        value=25
      }
    }
    {
      owner=402
      target=100
      scripted_relations={
        friend={
          flags="AA=="
          reason="friend_saved_as_children_corresponding"
        }
      }
    }
    {
      owner=500
      target=501
      temporary_opinion={
        modifier="impressed_opinion"
        expiration_date=1101.1.1
        value=12
      }
    }
  }
}
armies={
  regiments={
    1={ type=ayyar origin=20 size=300 owner=100 }
    2={ type=light_horsemen origin=21 size=200 owner=100 max=200 }
    3={ type=onager origin=22 size=20 owner=100 }
    4={ type=spearmen origin=30 size=100 owner=900 }
    5={ type=bowmen origin=31 size=100 }
  }
  armies={
    9001={
      regiments={ 1 2 }
      commander=700
      unit=90001
      name={ id=0 owner=100 province=20 }
      supply=95
    }
    9002={
      regiments={ 3 }
      commander=100
      unit=90002
      supply=40
    }
    9003={
      regiments={ 4 }
      commander=800
      unit=90003
      name={ id=0 owner=900 province=30 }
    }
  }
  gathering_armies={ 9001 }
}
units={
  90001={ type=army location=25 owner=100 army=90001 arrival_date=1099.5.1 }
  90002={ type=army location=30 owner=100 army=90002 path={ 28 29 } arrival_date=1100.7.1 }
  90003={ type=army location=31 owner=900 army=90003 }
}
council_task_manager={
  active={
    5001={ type=task_conversion owner=601 court_owner=100 progress=50.2 }
    5002={ type=task_spouse_default owner=602 court_owner=900 }
    5003={ type=task_martial owner=603 court_owner=100 }
  }
}
court_positions={
  database={
    8001={ court_position=court_physician_court_position task_type=physician_improve_self employee=701 employer=100 hire_date=1090.1.1 }
    8002={ court_position=court_tutor_court_position task_type=tutor_task employee=702 employer=900 }
  }
}
"""


def _build(root):
    wars = es.extract_wars(root)
    player = es.extract_player_and_family(root)
    pid = player.get("id")
    military = es.extract_military(root, pid)
    military["player_id"] = pid
    council = es.extract_council_court(root, pid)
    opinions = es.extract_opinions(root, pid)
    # minimal stage-2/3 data for JSON builder
    domain = [{"key": "c_capital", "is_county": True, "mapped": True}]
    counties = [{"county_key": "c_capital", "development": None,
                 "county_control": 100, "culture": 95, "faith": None}]
    provinces = [{"province_id": "20", "holding_type": None, "income": None,
                  "buildings": [], "county_key": "c_capital"}]
    characters = {"100": {"id": 100, "mapped": True, "alive": True, "name": "Bahram"},
                  "301": {"id": 301, "mapped": True, "alive": True, "name": "Kourash"}}
    vassals, factions = [], []
    faith_culture = {"player_faith": None, "player_faith_available": False,
                     "player_culture": 95, "player_culture_name": "tajik",
                     "county_faith_culture": [], "mismatches": []}
    succession = {"laws": ["male_only_law"], "gender_law": "male_only_law",
                  "succession_line": [], "first_in_line": None,
                  "algorithm_recomputed": False}
    state = es.build_state_json(
        root, player, characters, vassals, factions, faith_culture, succession,
        domain, counties, provinces, wars, military, council,
            {}, {}, {}, {}, {}, opinions,
            meta={"save_file": "/x/y/test.ck3", "game_date": "1100.6.15"})
    return wars, military, council, opinions, state


class TestStage4Extraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = es.parse_save(FIXTURE)
        (cls.wars, cls.military, cls.council, cls.opinions,
         cls.state) = _build(cls.root)

    # 1) جنگ فعال در برابر war history — فقط active_wars؛ ورودی none نادیده؛
    #    alive_data.wars (شمارندهٔ تاریخچه) هرگز خوانده نمی‌شود
    def test_1_active_wars_vs_history(self):
        ids = {w["war_id"] for w in self.wars}
        self.assertEqual(ids, {"7001", "7002", "7004"})  # 7003=none excluded
        self.assertEqual(len(self.wars), 3)
        # no fabricated war from the counter block
        self.assertNotIn(5, ids)
        self.assertNotIn(2, ids)

    # 2) Men-at-Arms چند regiment — فقط owner==player
    def test_2_multiple_maa_regiments_by_owner(self):
        regs = self.military["regiments"]
        self.assertEqual(len(regs), 3)
        types = {r["type"] for r in regs}
        self.assertEqual(types, {"ayyar", "light_horsemen", "onager"})
        by_type = {r["type"]: r for r in regs}
        self.assertEqual(by_type["light_horsemen"]["max"], 200)
        self.assertIsNone(by_type["ayyar"]["max"])  # missing ≠ 0

    # 3) knight list با شناسه‌های واقعی (نه شمردن اعداد داخل block)
    def test_3_knights_from_real_id_list(self):
        self.assertEqual(self.military["knights"], [401, 402])
        self.assertEqual(len(self.military["knights"]), 2)

    # 4) rally points — از played_character.rally_points (province/color) قابل‌اثبات
    def test_4_rally_points_from_played_character(self):
        self.assertEqual(self.military["rally_points"],
                         [{"province": 20, "color": 0}, {"province": 21, "color": 1}])
        self.assertNotIn("unavailable", self.military["rally_points"])

    # 5) council tasks — فقط دربار بازیکن (court_owner==100)
    def test_5_council_tasks_only_player_court(self):
        tasks = self.council["council_tasks"]
        self.assertEqual(len(tasks), 2)
        types = {t["type"] for t in tasks}
        self.assertEqual(types, {"task_conversion", "task_martial"})
        prog = next(t["progress"] for t in tasks if t["type"] == "task_conversion")
        self.assertEqual(prog, 50.2)

    # 6) decision flags — وضعیت خام؛ no هرگز «قابل اجرا» گزارش نمی‌شود
    def test_6_decisions_raw_flags(self):
        dec = self.council["decisions"]
        self.assertEqual(dec["feast_decision"], True)
        self.assertEqual(dec["hunt_decision"], False)
        self.assertEqual(dec["hold_court_decision"], False)
        # raw storage: booleans as saved, no reinterpretation
        self.assertEqual(len(dec), 3)

    # 6b) army positions — join armies.armies → units؛ فقط ارتش‌های بازیکن
    def test_6b_player_armies_positions(self):
        armies = self.military["armies"]
        by_id = {a["army_id"]: a for a in armies}
        # 9001: name.owner=100 → بازیکن؛ موقعیت از units[90001].location
        a1 = by_id["9001"]
        self.assertEqual(a1["location"], 25)
        self.assertEqual(a1["commander"], 700)
        self.assertTrue(a1["gathering"])  # در gathering_armies بود
        self.assertIs(a1["unit_location_missing"], False)
        # 9002: بدون name اما commander=100 → بازیکن؛ path و arrival از unit
        a2 = by_id["9002"]
        self.assertEqual(a2["movement_path"], [28, 29])
        self.assertEqual(a2["arrival_date"], "1100.7.1")
        self.assertFalse(a2["gathering"])
        # 9003: name.owner=900 و commander=800 → ارتش بازیکن نیست
        self.assertNotIn("9003", by_id)
        self.assertEqual(len(armies), 2)

    # 6c) opinion — جمع temporary، جهت، رابطهٔ scripted، و جداسازی missing از صفر
    def test_6c_opinions_sum_and_direction(self):
        ops = self.opinions["opinions"]
        # ردیف‌های about_player: صاحبِ نظر (owner) «دیگری» است
        by_owner = {o["owner"]: o for o in ops if o["direction"] == "about_player"}
        o900 = by_owner[900]
        self.assertEqual(o900["target"], 100)
        self.assertEqual(o900["total"], 15)  # 10 + (-3) + 8
        self.assertEqual(len(o900["temporary"]), 3)
        self.assertEqual(o900["temporary"][1]["modifier"], "rival_insult")
        # نظر بازیکن دربارهٔ دیگری
        held = [o for o in ops if o["direction"] == "held_by_player"]
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]["owner"], 100)
        # scripted relation بدون هیچ temporary → total None (missing ≠ 0)
        scripted = [o for o in ops if o.get("scripted_relations")]
        self.assertEqual(len(scripted), 1)
        self.assertIsNone(scripted[0]["total"])
        self.assertEqual(scripted[0]["scripted_relations"][0]["kind"], "friend")
        # ردیف‌های بی‌ربط به بازیکن شمرده شدند ولی جزئیات ندارند
        self.assertEqual(self.opinions["total"], 4)
        self.assertEqual(len(ops), 3)

    # 7) missing military fields — از صفر تفکیک می‌شوند
    def test_7_missing_military_fields_none_not_zero(self):
        self.assertEqual(self.military["current_strength"], 1200)
        self.assertEqual(self.military["total_strength"], 1500)
        self.assertEqual(self.military["levy"], 900)

    # 8) JSON معتبر با ساختار الزامی
    def test_8_json_valid_and_complete(self):
        blob = json.dumps(self.state, ensure_ascii=False)
        reparsed = json.loads(blob)
        for key in ("meta", "player", "domain", "counties", "holdings",
                    "characters", "vassals", "factions", "succession",
                    "wars", "military", "court", "quality"):
            self.assertIn(key, reparsed)
        self.assertEqual(reparsed["meta"]["save_file"], "test.ck3")  # basename only
        self.assertEqual(reparsed["quality"]["counts"]["maa_regiments"], 3)
        self.assertEqual(reparsed["quality"]["counts"]["active_wars"], 3)
        self.assertEqual(reparsed["quality"]["counts"]["knights"], 2)
        self.assertEqual(reparsed["quality"]["counts"]["player_armies"], 2)
        self.assertEqual(reparsed["quality"]["counts"]["rally_points"], 2)
        self.assertEqual(reparsed["quality"]["counts"]["player_opinions"], 3)
        self.assertEqual(reparsed["quality"]["counts"]["opinions_total"], 4)
        self.assertEqual(len(reparsed["opinions"]), 3)
        self.assertIn("player.faith", reparsed["quality"]["missing_fields"])
        self.assertTrue(any("county.development:c_capital" == m
                            for m in reparsed["quality"]["missing_fields"]))

    # 9) سازگاری گزارش متنی و JSON — آمارها یکسان
    def test_9_text_json_consistency(self):
        report = es.build_war_military_report(self.wars, self.military, self.council, self.opinions)
        self.assertIn("Active Wars (3)", report)
        self.assertIn("Men-at-Arms regiments: 3", report)
        self.assertIn("knights (real id list): 2", report)
        self.assertIn("involves player", report)  # war 7001: cb_attacker=100
        self.assertIn("hunt_decision = False", report)  # raw flag shown as saved
        self.assertIn("rally points: 2", report)
        self.assertIn("player armies (armies.armies join units): 2", report)
        self.assertIn("army 9001: commander=700 location=25 [gathering]", report)
        self.assertIn("moving via: 28 -> 29 (arrival 1100.7.1)", report)
        self.assertIn("Opinions involving player (of 4 opinion rows)", report)
        self.assertIn("total=15", report)
        self.assertIn("rival_insult: -3", report)

    # 10) امتیاز جنگ فقط از دادهٔ قابل اثبات: ticking + battle sum
    def test_10_war_score_from_provable_data(self):
        w7001 = next(w for w in self.wars if w["war_id"] == "7001")
        self.assertEqual(w7001["casus_belli"], "conquest_war")
        self.assertEqual(w7001["cb_claimant"], 100)
        self.assertEqual(w7001["war_score_sum"], 2.7)  # 3.5 + (-0.8)
        att = w7001["attacker"]
        self.assertEqual(att["ticking_war_score"], 2.5)
        self.assertEqual(att["participants"][0]["character"], 100)
        self.assertEqual(att["participants"][0]["contribution"], [500, 10, 5])
        self.assertEqual(len(w7001["battles"]), 2)
        # war 7004: battle_results/casus_belli.claimant missing → None
        w7004 = next(w for w in self.wars if w["war_id"] == "7004")
        self.assertIsNone(w7004["war_score_sum"])
        self.assertIsNone(w7004["cb_claimant"])


class TestRealSaveStage4(unittest.TestCase):
    """Real-save stage-4 statistics (skipped without reports/melted.txt)."""

    def setUp(self):
        from test_economy_extract import _load_real_save
        loaded = _load_real_save()
        if loaded is None:
            self.skipTest("reports/melted.txt not found")
            return
        self.root = loaded[0]

    def test_real_stage4_stats(self):
        root = self.root
        wars = es.extract_wars(root)
        player = es.extract_player_and_family(root)
        pid = player.get("id")
        military = es.extract_military(root, pid)
        council = es.extract_council_court(root, pid)
        print("\nReal-save stage-4 stats:")
        print(f"  active wars: {len(wars)}")
        mine = [w for w in wars if pid in (w.get("cb_attacker"), w.get("cb_defender"))]
        print(f"  wars involving player (cb attacker/defender): {len(mine)}")
        for w in wars:
            if pid in (w.get("cb_attacker"), w.get("cb_defender")):
                print(f"    war {w['war_id']}: cb={w['casus_belli']} att={w['cb_attacker']} def={w['cb_defender']} start={w['start_date']}")
        print(f"  maa regiments (player): {len(military['regiments'])} "
              f"-> {[(r['type'], r['size']) for r in military['regiments']]}")
        print(f"  knights: {len(military['knights'])}")
        print(f"  levy={military['levy']} current={military['current_strength']} total={military['total_strength']}")
        print(f"  council tasks (player court): {len(council['council_tasks'])}")
        print(f"  court positions (player court): {len(council['court_positions'])}")
        print(f"  decisions: {len(council['decisions'])}")
        self.assertIsInstance(wars, list)


if __name__ == "__main__":
    unittest.main()
