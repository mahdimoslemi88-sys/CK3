# -*- coding: utf-8 -*-
import sys, re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

text = open('reports/melted.txt', 'r', encoding='utf-8').read()

print("=== 1. FINDING REAL PLAYER CHARACTER (8975) ===")
# Find character block with first_name
m_char = re.search(r'\n(\t*)8975=\{\s*\n\t*first_name=.*?(?=\n\1\d+=\{\s*\n\t*first_name=)', text, re.DOTALL)
if not m_char:
    m_char = re.search(r'\n8975=\{\s*\n\t*first_name=.*?(?=\n\d+=\{\s*\n\t*first_name=)', text, re.DOTALL)

if m_char:
    block = m_char.group(0)
    print("Found real character block! Length:", len(block))
    
    # Children
    cm = re.search(r'child=\{\s*([^\}]+)\}', block)
    if cm:
        cids = cm.group(1).split()
        print(f"\nChildren list ({len(cids)} total):", cids)
        for cid in cids:
            # Find character block for child
            c_match = re.search(r'\n\t*' + cid + r'=\{\s*\n\t*first_name="?([^"\s\n]+)"?.*?(?=\n\t*\d+=\{\s*\n\t*first_name=|\Z)', text, re.DOTALL)
            if c_match:
                c_block = c_match.group(0)
                cname = re.search(r'first_name="?([^"\s\n]+)"?', c_block)
                cbirth = re.search(r'birth=([0-9.]+)', c_block)
                is_fem = bool(re.search(r'\bfemale=yes\b', c_block[:300]))
                print(f" - ID {cid:<8} | Name: {cname.group(1) if cname else '?':<12} | Born: {cbirth.group(1) if cbirth else '?'} | Gender: {'دختر ♀' if is_fem else '👑 پسر (SON / MALE HEIR!) 👦'}")

    # Domain
    dm = re.search(r'domain=\{\s*([^\}]+)\}', block)
    if dm:
        print("\nDomain title IDs:", dm.group(1).split())
        for tid in dm.group(1).split():
            # Find title block to get its key and capital/province
            tm = re.search(r'\n(\t*)' + tid + r'=\{\s*\n\t*key="?([^"\s\n]+)"?.*?(?=\n\1\d+=\{|\Z)', text, re.DOTALL)
            if tm:
                tbody = tm.group(0)
                tkey = re.search(r'key="?([^"\s\n]+)"?', tbody).group(1)
                tcap = re.search(r'capital=(\d+)', tbody)
                prov_id = tcap.group(1) if tcap else tid
                
                # Look up province block for prov_id
                pm = re.search(r'\n(\t*)' + prov_id + r'=\{\s*\n\t*holding=\{\s*\n(.*?)(?=\n\1\d+=\{|\Z)', text, re.DOTALL)
                bld_names = []
                if pm:
                    pbody = pm.group(0)
                    bld_names = re.findall(r'type="?([^"\s\n]+)"?', pbody)
                print(f" -> Title {tid} ({tkey}) | Prov ID: {prov_id} | Buildings: {bld_names if bld_names else 'خالی'}")

    # Check Gold, Income, Perks
    gold_m = re.search(r'gold=\{\s*\n\s*value=(-?[\d.]+)', block)
    income_m = re.search(r'income=(-?[\d.]+)', block)
    balance_m = re.search(r'balance=(-?[\d.]+)', block)
    prestige_m = re.search(r'prestige=\{\s*\n\s*currency=(-?[\d.]+)', block)
    stress_m = re.search(r'stress=(-?[\d.]+)', block)
    print(f"\nStats: Gold={gold_m.group(1) if gold_m else '?'}, Income={income_m.group(1) if income_m else '?'}, Net Balance={balance_m.group(1) if balance_m else '?'}, Prestige={prestige_m.group(1) if prestige_m else '?'}, Stress={stress_m.group(1) if stress_m else '?'}")
