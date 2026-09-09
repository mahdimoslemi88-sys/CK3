# -*- coding: utf-8 -*-
"""Stage-2 fixture tests — domain, county, province, holding, building extraction.

Run: python -m pytest tests/test_economy_extract.py -q
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import extract_save as es  # noqa: E402

# ------------------------------------------------------------------
# Real-save cache: the 185 MB melted save is parsed ONCE per suite run
# and shared by all real-save test classes (path+mtime+size keyed).
# ------------------------------------------------------------------
_REAL_ROOT_CACHE = {}


def _load_real_save():
    """Return (root, consumed_chars, total_chars) for reports/melted.txt,
    or None if the file does not exist (callers skipTest)."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'reports', 'melted.txt',
    )
    if not os.path.isfile(path):
        return None
    st = os.stat(path)
    key = (path, st.st_mtime_ns, st.st_size)
    if key not in _REAL_ROOT_CACHE:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        parser = es.SaveParser(text)
        root = parser.parse()
        _REAL_ROOT_CACHE[key] = (root, parser._i, len(text))
    return _REAL_ROOT_CACHE[key]


FIXTURE = """
meta_date=1100.3.15
meta_player_name="TestPlayer"
played_character={
  name="TestPlayer"
  character=100
}
landed_titles={
  landed_titles={
    1={
      key=k_test
      holder=100
      name="Kingdom Test"
      capital=10
    }
    10={
      key=d_test
      holder=100
      name="Duchy Test"
      de_jure_liege=1
      capital=10
    }
    20={
      key=c_alpha
      holder=100
      name="County Alpha"
      de_jure_liege=10
      capital=20
    }
    21={
      key=c_beta
      holder=100
      name="County Beta"
      de_jure_liege=10
      capital=21
    }
    30={
      key=b_alpha_church
      holder=200
      name="Barony Church"
      de_jure_liege=20
    }
    40={
      key=c_gamma
      holder=300
      name="County Gamma"
      de_jure_liege=10
      capital=40
    }
  }
}
living={
  100={
    landed_data={
      domain={ 20 21 30 10 1 }
      domain_limit=3
      government=feudal_government
      realm_capital=20
    }
  }
}
county_manager={
  counties={
    c_alpha={
      development=15
      development_progress=0.5
      county_control=100
      culture=98
      faith=50
    }
    c_beta={
      development=8
      county_control=45.2
      culture=98
      faith=50
    }
    c_gamma={
      county_control=50
    }
  }
}
provinces={
  20={
    holding={
      type=castle_holding
      owner=100
      income=2.5
      levy=500
      garrison=750
      buildings={
        { type=castle_01 }
        { type=wall_02 }
      }
    }
    fort_level=3
    winter_severity=0
  }
  21={
    holding={
      type=city_holding
      owner=100
      income=1.8
      levy=300
      garrison=400
      buildings={
        { type=city_01 }
        { type=guild_halls_01 }
        { }
      }
    }
    construction={
      type=city_02
      completion_date=1101.1.1
    }
    fort_level=2
    winter_severity=0.2
    next_winter_target_date=1100.11.1
  }
  23={
    holding={
      type=castle_holding
      owner=100
      income=2.4
      buildings={
        { type=castle_01 }
        { type=pastures_01 }
      }
      constructions={
        building="pastures_02"
        index=2
        start_time=944.6.4
        days=519
        cost={
          gold=250
        }
        character=67123228
      }
      constructions={
        building="castle_02"
        index=0
        start_time=944.9.1
        days=400
        cost={
          gold=190
          prestige=485
        }
        character=33574163
      }
    }
    fort_level=6
  }
  40={
    holding={
      type=church_holding
      owner=300
      income=0.5
    }
  }
  99={
    holding={
      type=castle_holding
      owner=999
      income=9.9
    }
  }
}
"""


class TestEconomyExtraction(unittest.TestCase):
    """Mandatory stage-2 fixture tests."""

    @classmethod
    def setUpClass(cls):
        cls.root = es.parse_save(FIXTURE)
        cls.domain = es.extract_domain(cls.root)
        cls.counties = es.extract_counties(cls.root)
        domain_c_keys = [
            d['key'] for d in cls.domain
            if d.get('is_county') and d.get('mapped')
        ]
        cls.provinces = es.extract_provinces(cls.root, domain_c_keys)

    def test_1_multiple_tiers(self):
        """Titles with different tiers exist (k_, d_, c_, b_)."""
        lt = self.root.children['landed_titles'].children['landed_titles']
        keys = set()
        for t in lt.children.values():
            if t.kind == 'block':
                kn = t.children.get('key')
                if kn and kn.value:
                    keys.add(kn.value)
        self.assertIn('k_test', keys)
        self.assertIn('d_test', keys)
        self.assertIn('c_alpha', keys)
        self.assertIn('b_alpha_church', keys)

    def test_2_domain_county_and_barony(self):
        """Domain contains both county and barony IDs."""
        keys = [d.get('key') for d in self.domain if d.get('mapped')]
        self.assertIn('c_alpha', keys)
        self.assertIn('b_alpha_church', keys)

    def test_3_county_manager_development_control(self):
        """county_manager provides development and county_control."""
        alpha = next(c for c in self.counties if c['county_key'] == 'c_alpha')
        self.assertEqual(alpha['development'], 15)
        self.assertEqual(alpha['county_control'], 100)
        beta = next(c for c in self.counties if c['county_key'] == 'c_beta')
        self.assertEqual(beta['development'], 8)
        self.assertAlmostEqual(beta['county_control'], 45.2)

    def test_4_province_holding_buildings(self):
        """Province has a holding with multiple buildings."""
        p = next(p for p in self.provinces if p['province_id'] == '20')
        self.assertEqual(p['holding_type'], 'castle_holding')
        self.assertEqual(p['income'], 2.5)
        self.assertEqual(p['levy'], 500)
        self.assertEqual(p['garrison'], 750)
        self.assertEqual(len(p['buildings']), 2)
        types = [b['type'] for b in p['buildings']]
        self.assertIn('castle_01', types)
        self.assertIn('wall_02', types)

    def test_5_construction_in_progress(self):
        """Province 21 has a construction block (separate from completed buildings)."""
        root = self.root
        provs = root.children['provinces']
        p = provs.children['21']
        self.assertIsNotNone(p.children.get('construction'))
        constr = p.children['construction']
        self.assertEqual(constr.children.get('type').value, 'city_02')

    def test_6_county_without_development(self):
        """A county with no development field reports None (not 0)."""
        gamma = next((c for c in self.counties if c['county_key'] == 'c_gamma'), None)
        self.assertIsNotNone(gamma)
        self.assertIsNone(gamma['development'])  # missing, not 0

    def test_7_similar_provinces_not_confused(self):
        """Provinces 20 and 21 have distinct data (no cross-contamination)."""
        p20 = next(p for p in self.provinces if p['province_id'] == '20')
        p21 = next(p for p in self.provinces if p['province_id'] == '21')
        self.assertNotEqual(p20['holding_type'], p21['holding_type'])
        self.assertNotEqual(p20['income'], p21['income'])

    def test_8_no_first_match_wrong(self):
        """c_alpha maps to province 20 (its capital), not province 21."""
        lt = self.root.children['landed_titles'].children['landed_titles']
        for tk, tn in lt.children.items():
            if tn.kind != 'block':
                continue
            kn = tn.children.get('key')
            if kn and kn.value == 'c_alpha':
                cap = tn.children.get('capital')
                self.assertEqual(cap.value, 20)
                break

    def test_9_domain_count_only_counties(self):
        """domain_count counts only c_ titles, not baronies or duchies."""
        c_titles = [d for d in self.domain if d.get('is_county')]
        self.assertEqual(len(c_titles), 2)  # c_alpha + c_beta, not b_alpha_church
        baronies = [d for d in self.domain if d.get('key', '').startswith('b_')]
        self.assertEqual(len(baronies), 1)
        self.assertFalse(baronies[0]['is_county'])

    def test_10_report_generation(self):
        """build_economy_report produces a non-empty string with expected sections."""
        report = es.build_economy_report(self.domain, self.counties, self.provinces)
        self.assertIn('ECONOMY & DOMAIN', report)
        self.assertIn('Domain Summary', report)
        self.assertIn('Counties', report)
        self.assertIn('Holdings & Provinces', report)
        self.assertIn('Missing / Unknown', report)
        self.assertIn('c_alpha', report)
        self.assertIn('c_beta', report)
        self.assertIn('domain_count (c_ only): 2', report)

    def test_11_domain_province_filtering(self):
        """extract_provinces only returns provinces whose ID is a domain county capital."""
        pids = [p['province_id'] for p in self.provinces]
        self.assertIn('20', pids)  # c_alpha capital
        self.assertIn('21', pids)  # c_beta capital
        self.assertNotIn('99', pids)  # non-domain province
        self.assertNotIn('40', pids)  # c_gamma is not in domain


class TestParserRgbBug(unittest.TestCase):
    """Verify the parser handles bare-word value followed by list block
    (color=rgb { 181 87 216 }) without truncating the tree."""

    RGB_FIXTURE = """
meta_date=1100.3.15
landed_titles={
  landed_titles={
    99={
      key=c_test
      holder=100
      color=rgb {
        181 87 216
      }
      coat_of_arms_id=42
    }
  }
}
next_block={
  value=yes
}
after_that={
  value=no
}
"""

    def test_rgb_value_consumed_and_parsing_continues(self):
        """After color=rgb { ... }, subsequent blocks at root still parse correctly."""
        parser = es.SaveParser(self.RGB_FIXTURE)
        root = parser.parse()
        # The parser must consume the ENTIRE fixture (no early stop, no stray brace kill)
        self.assertEqual(
            parser._i, parser.n,
            'parser stopped at %d of %d chars — tree truncated after rgb' % (parser._i, parser.n),
        )
        # rgb value should be consumed (scalar 'rgb')
        lt = root.children.get('landed_titles')
        self.assertIsNotNone(lt, 'landed_titles must be present after rgb fix')
        inner = lt.children.get('landed_titles')
        self.assertIsNotNone(inner, 'landed_titles inner block must be present')
        t99 = inner.children.get('99')
        self.assertIsNotNone(t99, 'title 99 must be present after rgb fix')
        key = t99.children.get('key')
        self.assertEqual(key.value, 'c_test')
        # next_block and after_that must still be accessible at root level
        nb = root.children.get('next_block')
        self.assertIsNotNone(nb, 'next_block must be present after rgb fix')
        val = nb.children.get('value')
        self.assertIs(val.value, True)  # yes → True (parser converts scalars)
        at = root.children.get('after_that')
        self.assertIsNotNone(at, 'after_that must be present after rgb fix')
        val2 = at.children.get('value')
        self.assertIs(val2.value, False)  # no → False


class TestRealSaveRootBlocks(unittest.TestCase):
    """Verify the real save parses to end of file with all expected root blocks."""

    def setUp(self):
        loaded = _load_real_save()
        if loaded is None:
            self.skipTest('reports/melted.txt not found')
            return
        self.root, self.consumed, self.total = loaded

    def test_parse_consumes_entire_file(self):
        """Parser consumed the whole 185 MB file: final position == length
        (braces balanced at EOF — proves no early termination)."""
        self.assertEqual(
            self.consumed, self.total,
            'parser stopped at %d of %d chars — tree truncated' % (self.consumed, self.total),
        )

    def test_required_root_blocks_present(self):
        """All expected root-level blocks are present after full parse."""
        required = [
            'played_character', 'characters', 'landed_titles', 'provinces',
            'county_manager', 'holdings', 'faction_manager', 'wars',
            'religion', 'culture_manager', 'succession',
            'character_memory_manager', 'dynasties', 'living',
            'character_lookup', 'units', 'armies', 'sieges',
        ]
        missing = [k for k in required if k not in self.root.children]
        self.assertEqual(missing, [], f'Missing root blocks: {missing}')

    def test_last_root_block_parsed(self):
        """The parser reaches the end of the file (confederation_manager is the last block)."""
        self.assertIn('confederation_manager', self.root.children)

    def test_root_block_count(self):
        """The real save produces >60 root blocks (not truncated to ~18)."""
        self.assertGreater(len(self.root.children), 60,
            f'Root has only {len(self.root.children)} children — parser may be truncating')


class TestRealSaveMappingAssertions(unittest.TestCase):
    """Verify real title→province mappings are correct, not just counts."""

    def setUp(self):
        loaded = _load_real_save()
        if loaded is None:
            self.skipTest('reports/melted.txt not found')
            return
        self.root = loaded[0]
        self.domain = es.extract_domain(self.root)
        self.domain_c_keys = [
            d['key'] for d in self.domain
            if d.get('is_county') and d.get('mapped')
        ]
        self.provinces = es.extract_provinces(self.root, self.domain_c_keys)

    def test_c_nakhshab_maps_to_province_5673(self):
        """Real mapping: c_nakhshab → province 5673."""
        p = next((p for p in self.provinces if p.get('county_key') == 'c_nakhshab'), None)
        self.assertIsNotNone(p, 'c_nakhshab not found in extracted provinces')
        self.assertEqual(p['province_id'], '5673')
        self.assertEqual(p['holding_type'], 'city_holding')

    def test_c_dabusiya_maps_to_province_5683(self):
        """Real mapping: c_dabusiya → province 5683."""
        p = next((p for p in self.provinces if p.get('county_key') == 'c_dabusiya'), None)
        self.assertIsNotNone(p, 'c_dabusiya not found in extracted provinces')
        self.assertEqual(p['province_id'], '5683')
        self.assertEqual(p['holding_type'], 'church_holding')

    def test_domain_county_count_is_5(self):
        """The real save has exactly 5 c_ domain counties."""
        self.assertEqual(len(self.domain_c_keys), 5)

    def test_domain_province_count_is_5(self):
        """The real save produces exactly 5 domain provinces."""
        self.assertEqual(len(self.provinces), 5)

    def test_holding_type_none_reported_as_missing(self):
        """Provinces with no holding type report None (not string 'None')."""
        for p in self.provinces:
            if p['holding_type'] is None:
                # Prove it's None (Python None), not the string "None"
                self.assertIsNone(p['holding_type'])


class TestStage6BuildingLevels(unittest.TestCase):
    """Stage-6 fixture tests — building levels from suffix, holding-level
    constructions, province-fallback construction, missing ≠ unknown-string."""

    @classmethod
    def setUpClass(cls):
        cls.root = es.parse_save(FIXTURE)
        cls.provinces = es.extract_provinces(cls.root, [])  # بدون فیلتر = همهٔ provinceها

    def _prov(self, pid):
        return next(p for p in self.provinces if p['province_id'] == pid)

    def test_1_level_from_suffix(self):
        """Level از پسوند نوع (_01/_02) خوانده می‌شود — از دادهٔ سیو، بدون حدس."""
        p20 = self._prov('20')
        levels = {b['type']: b['level'] for b in p20['buildings']}
        self.assertEqual(levels['castle_01'], 1)
        self.assertEqual(levels['wall_02'], 2)
        p21 = self._prov('21')
        levels21 = {b['type']: b['level'] for b in p21['buildings']}
        self.assertEqual(levels21['city_01'], 1)
        self.assertEqual(levels21['guild_halls_01'], 1)

    def test_2_empty_building_is_honest_missing(self):
        """{ } building block: type None و level None — هرگز 'unknown' رشته‌ای یا حدس."""
        p21 = self._prov('21')
        empty = [b for b in p21['buildings'] if b['type'] is None]
        self.assertEqual(len(empty), 1)
        self.assertIsNone(empty[0]['level'])
        for b in p21['buildings']:
            self.assertIn(b['level'], (1, None))

    def test_3_holding_construction_real_shape(self):
        """ساخت‌وساز واقعی داخل holding: building/index/start_time/days/cost/character."""
        p23 = self._prov('23')
        self.assertEqual(len(p23['constructions']), 2)  # دو سازهٔ هم‌زمان (get_all)
        c0, c1 = p23['constructions']
        self.assertEqual(c0['building'], 'pastures_02')
        self.assertEqual(c0['index'], 2)
        self.assertEqual(c0['start_time'], '944.6.4')
        self.assertEqual(c0['days'], 519)
        self.assertEqual(c0['cost_gold'], 250)
        self.assertIsNone(c0['cost_prestige'])
        self.assertEqual(c0['character'], 67123228)
        self.assertEqual(c1['building'], 'castle_02')
        self.assertEqual(c1['cost_gold'], 190)
        self.assertEqual(c1['cost_prestige'], 485)

    def test_4_province_construction_fallback_kept(self):
        """سازگاری: construction سطح province (فرم قدیمی) همچنان خوانده می‌شود."""
        p21 = self._prov('21')
        self.assertEqual(len(p21['constructions']), 1)
        self.assertEqual(p21['constructions'][0]['building'], 'city_02')
        self.assertEqual(p21['constructions'][0]['completion_date'], '1101.1.1')

    def test_5_level_never_unknown_string(self):
        """سطح ساختمان هرگز رشتهٔ 'unknown' نیست — int قابل‌اثبات یا None."""
        for p in self.provinces:
            for b in p['buildings']:
                self.assertNotEqual(b['level'], 'unknown')
                self.assertTrue(b['level'] is None or isinstance(b['level'], int))


class TestRealSaveStage6(unittest.TestCase):
    """Real-save stage-6 statistics (shared cached parse; skips without melted.txt)."""

    def setUp(self):
        loaded = _load_real_save()
        if loaded is None:
            self.skipTest('reports/melted.txt not found')
            return
        self.root = loaded[0]

    def test_real_stage6_stats(self):
        root = self.root
        player = es.extract_player_and_family(root)
        pid = player.get('id')
        military = es.extract_military(root, pid)
        opinions = es.extract_opinions(root, pid)
        provinces = es.extract_provinces(root, [])
        n_buildings = sum(len(p['buildings']) for p in provinces)
        n_leveled = sum(1 for p in provinces for b in p['buildings'] if b['level'] is not None)
        n_constr = sum(len(p['constructions']) for p in provinces)
        print('\nReal-save stage-6 stats:')
        print(f'  provinces (all): {len(provinces)}')
        print(f'  buildings: {n_buildings} — level resolved: {n_leveled}')
        print(f'  holding-level constructions: {n_constr}')
        print(f'  rally points: {len(military["rally_points"])}')
        print(f'  player armies: {len(military["armies"])}')
        for a in military['armies']:
            print(f"    army {a['army_id']}: loc={a['location']} gathering={a['gathering']} "
                  f"missing_unit={a['unit_location_missing']}")
        print(f'  opinions involving player: {len(opinions["opinions"])} of {opinions["total"]}')
        self.assertGreater(n_buildings, 0)
        self.assertGreater(n_leveled, 0)
        self.assertGreaterEqual(len(military['rally_points']), 0)
        self.assertIsInstance(opinions['opinions'], list)


class TestRealSaveIntegration(unittest.TestCase):
    """Real-save integration (skipped if melted.txt not present; shared cached parse)."""

    def setUp(self):
        loaded = _load_real_save()
        if loaded is None:
            self.skipTest('reports/melted.txt not found')
            return
        self.root = loaded[0]

    def test_real_save_parse_and_extract(self):
        root = self.root
        domain = es.extract_domain(root)
        counties = es.extract_counties(root)
        domain_c_keys = [
            d['key'] for d in domain
            if d.get('is_county') and d.get('mapped')
        ]
        provinces = es.extract_provinces(root, domain_c_keys)
        print(f'\nReal-save stats:')
        print(f'  domain IDs: {len(domain)}')
        print(f'  mapped domain titles: {len([d for d in domain if d.get("mapped")])}')
        print(f'  c_ domain counties: {len(domain_c_keys)}')
        print(f'  county_manager entries: {len(counties)}')
        print(f'  provinces with holdings (domain): {len(provinces)}')
        print(f'  total buildings: {sum(len(p["buildings"]) for p in provinces)}')
        self.assertIsInstance(domain, list)
        self.assertIsInstance(counties, list)
        self.assertIsInstance(provinces, list)


if __name__ == '__main__':
    unittest.main()
