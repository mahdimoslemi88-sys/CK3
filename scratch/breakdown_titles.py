# -*- coding: utf-8 -*-
import sys, re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

text = open('reports/melted.txt', 'r', encoding='utf-8').read()
pid = '16817309'

# Find player block
m_p = re.search(r'\n(\t*)' + pid + r'=\{\s*\n\t*first_name=.*?(?=\n\1\d+=\{\s*\n\t*first_name=|\Z)', text, re.DOTALL)
block = m_p.group(0) if m_p else ""

landed_m = re.search(r'landed_data=\{\s*\n(.*?)(?=\n\t*\w+_data=\{|\n\})', block, re.DOTALL)
landed_text = landed_m.group(1) if landed_m else ""

dm = re.search(r'domain=\{\s*([^\}]+)\}', landed_text)
domain_ids = dm.group(1).split() if dm else []

print(f"Domain IDs ({len(domain_ids)}):", domain_ids)

counties = []
duchies = []
baronies = []

for tid in domain_ids:
    # search for title block: \ntid={\n\tkey=
    m_t = re.search(r'\n(\t*)' + tid + r'=\{\s*\n\t*key="?([^"\s\n]+)"?.*?\n\t*holder=(\d+)', text)
    if not m_t:
        m_t = re.search(r'\n' + tid + r'=\{\s*\n\t*key="?([^"\s\n]+)"?.*?\n\t*holder=(\d+)', text)
    if m_t:
        tkey = m_t.group(2)
        holder = m_t.group(3)
        print(f"ID {tid:<6} | Key: {tkey:<18} | Holder: {holder:<10} | IsPlayer: {holder == pid}")
        if tkey.startswith("c_"):
            counties.append((tid, tkey))
        elif tkey.startswith("d_") or tkey.startswith("k_") or tkey.startswith("e_"):
            duchies.append((tid, tkey))
        elif tkey.startswith("b_"):
            baronies.append((tid, tkey))
    else:
        # Province holding?
        p_m = re.search(r'\n' + tid + r'=\{\s*\n\t*holding=\{\s*\n\t*type="?([^"\s\n]+)"?', text)
        if p_m:
            print(f"ID {tid:<6} | Province Holding: {p_m.group(1)}")
        else:
            print(f"ID {tid:<6} | Not found")

print("\n==================================")
print(f"👑 DUCHIES/KINGDOMS DIRECTLY HELD ({len(duchies)}):", duchies)
print(f"🏰 COUNTIES DIRECTLY HELD ({len(counties)}):", counties)
print(f"🏛️ BARONIES IN DOMAIN LIST ({len(baronies)}):", baronies)
print("==================================")
