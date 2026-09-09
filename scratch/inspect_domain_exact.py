# -*- coding: utf-8 -*-
import sys, re

text = open('reports/melted.txt', 'r', encoding='utf-8').read()
pid = '16817309'

# Find player block
m_p = re.search(r'\n(\t*)' + pid + r'=\{\s*\n\t*first_name=.*?(?=\n\1\d+=\{\s*\n\t*first_name=|\Z)', text, re.DOTALL)
block = m_p.group(0) if m_p else ""

landed_m = re.search(r'landed_data=\{\s*\n(.*?)(?=\n\t*\w+_data=\{|\n\})', block, re.DOTALL)
landed_text = landed_m.group(1) if landed_m else ""

dm = re.search(r'domain=\{\s*([^\}]+)\}', landed_text)
domain_ids = dm.group(1).split() if dm else []

print(f"Total IDs inside player's domain block ({len(domain_ids)}):", domain_ids)

print("\n--- Detailed Title Inspection for each domain ID ---")
counties = []
baronies = []
other = []

for tid in domain_ids:
    # Find title block
    tm = re.search(r'\n(\t*)' + tid + r'=\{\s*\n(.*?)(?=\n\1\d+=\{|\Z)', text, re.DOTALL)
    if tm:
        tbody = tm.group(2)
        tkey_m = re.search(r'key="?([^"\s\n]+)"?', tbody)
        tkey = tkey_m.group(1) if tkey_m else "?"
        holder_m = re.search(r'holder=(\d+)', tbody)
        holder = holder_m.group(1) if holder_m else "none"
        de_facto_m = re.search(r'de_facto_liege=(\d+)', tbody)
        liege = de_facto_m.group(1) if de_facto_m else "none"
        
        # Check if leased
        is_leased = "leased_to=" in tbody or "lessee=" in tbody
        
        print(f"Title {tid:<6} | Key: {tkey:<15} | Holder: {holder:<8} | IsPlayer: {holder == pid} | Leased: {is_leased}")
        if tkey.startswith("c_"):
            counties.append((tid, tkey))
        elif tkey.startswith("b_"):
            baronies.append((tid, tkey, holder))
        else:
            other.append((tid, tkey))

print(f"\nTotal COUNTIES (c_...): {len(counties)}")
for cid, ckey in counties:
    print(f" - {cid}: {ckey}")

print(f"\nTotal BARONIES where holder == player: {len([b for b in baronies if b[2] == pid])}")
