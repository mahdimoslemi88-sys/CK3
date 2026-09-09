import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('reports/state_report.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

p = d['player']
print("=== PLAYER OVERVIEW (1053.05.01) ===")
print(f"Name: {p.get('name')} | Age: {p.get('age')} | Health: {p.get('health')}")
print(f"Gold: {p.get('gold'):,.2f} | Income: +{p.get('income'):,.2f}/month")
print(f"Prestige: {p.get('prestige'):,.1f} | Piety: {p.get('piety'):,.1f} | Legitimacy: {p.get('legitimacy')}")
print(f"Skills: Dip={p.get('skills')[0]}, Mar={p.get('skills')[1]}, Ste={p.get('skills')[2]}, Int={p.get('skills')[3]}, Lea={p.get('skills')[4]}, Pro={p.get('skills')[5]}")
print(f"Domain Limit: {p.get('domain_limit')}")
print(f"Culture ID: {p.get('culture')}")

print("\n=== DOMAIN COUNTIES & HOLDINGS ===")
print(f"Total counties tracked: {len(d.get('counties', []))}")
for c in d.get('counties', []):
    print(f"  County: {c.get('key')} | Dev: {c.get('development')} | Control: {c.get('county_control')} | Culture: {c.get('culture')}")

print(f"\nTotal holdings: {len(d.get('holdings', []))}")
for h in d.get('holdings', []):
    print(f"  Holding: {h.get('key')} | Type: {h.get('holding_type')} | Income: {h.get('income')} | Buildings: {len(h.get('buildings', []))}")

print("\n=== MILITARY ===")
mil = d.get('military', {})
print(f"Strength: {mil.get('current_strength')} / {mil.get('total_strength')} (Levy: {mil.get('levy')})")
print(f"Knights: {len(mil.get('knights', []))}")
for r in mil.get('regiments', []):
    print(f"  Regiment: {r.get('type')}")

print("\n=== SUCCESSION & FAMILY ===")
succ = d.get('succession', {})
print(f"First in line: {succ.get('first_in_line')}")
print(f"Laws: {succ.get('laws')}")
print(f"Spouses: {len(p.get('family', {}).get('spouses', []))}")
print(f"Children: {len(p.get('family', {}).get('children', []))}")

print("\n=== FACTIONS AGAINST PLAYER ===")
# factions where target is player (16888178)
player_id = p.get('id')
factions_against_player = [f for f in d.get('factions', []) if f.get('target') == player_id]
print(f"Factions targeting player: {len(factions_against_player)}")
for f in factions_against_player:
    print(f"  Faction ID: {f.get('faction_id')} | Type: {f.get('type')} | Power: {f.get('power')} | Leader: {f.get('leader')}")

print("\n=== WARS INVOLVING PLAYER ===")
wars_player = [w for w in d.get('wars', []) if player_id in [w.get('cb_attacker'), w.get('cb_defender')]]
print(f"Wars directly involving player: {len(wars_player)}")
for w in wars_player:
    print(f"  War ID: {w.get('war_id')} | CB: {w.get('casus_belli')} | Attacker: {w.get('cb_attacker')} | Defender: {w.get('cb_defender')}")
