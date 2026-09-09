# -*- coding: utf-8 -*-
import sys, re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

text = open('reports/melted.txt', 'r', encoding='utf-8').read()

print("Finding player character 8975 in 897.1.1...")
pos = text.find('\n8975={')
if pos < 0:
    pos = text.find('8975={')
print("Position:", pos)

if pos >= 0:
    # grab 10,000 chars from pos
    block = text[pos:pos+12000]
    # find where block ends
    # print first 500 chars
    print("Block start:\n", block[:500])
    
    # Children
    cm = re.search(r'child=\{\s*([^\}]+)\}', block)
    if cm:
        cids = cm.group(1).split()
        print(f"\nFound {len(cids)} children:", cids)
        for cid in cids:
            cpos = text.find(f'\n{cid}={{')
            if cpos >= 0:
                cblock = text[cpos:cpos+1500]
                cname = re.search(r'first_name="?([^"\s\n]+)"?', cblock)
                cbirth = re.search(r'birth=([0-9.]+)', cblock)
                # check female
                is_fem = bool(re.search(r'\bfemale=yes\b', cblock))
                print(f" - ID {cid}: {cname.group(1) if cname else '?'} | Born: {cbirth.group(1) if cbirth else '?'} | Gender: {'دختر (Female)' if is_fem else '👑 پسر (MALE / SON!) 👦'}")

    # Buildings search: find where player has holdings
    landed_m = re.search(r'landed_data=\{\s*\n(.*?)(?=\n\t*\w+_data=\{|\n\})', block, re.DOTALL)
    if landed_m:
        ltext = landed_m.group(1)
        dm = re.search(r'domain=\{\s*([^\}]+)\}', ltext)
        print("\nDomain holdings IDs:", dm.group(1).split() if dm else "None")
        if dm:
            for did in dm.group(1).split():
                dpos = text.find(f'\n{did}={{')
                if dpos >= 0:
                    dblock = text[dpos:dpos+1000]
                    dkey = re.search(r'key="?([^"\s\n]+)"?', dblock)
                    dbuildings = re.search(r'buildings=\{\s*([^\}]+)\}', dblock)
                    dholding = re.search(r'holding_type="?([^"\s\n]+)"?', dblock)
                    print(f" -> Holding {did} ({dkey.group(1) if dkey else '?'}): Type={dholding.group(1) if dholding else '?'} | Buildings={dbuildings.group(1) if dbuildings else 'خالی'}")

    # Search for how buildings are named in CK3
    print("\n--- Searching for any building names in whole save ---")
    bld_keys = re.findall(r'buildings=\{\s*([^\}]+)\}', text)
    print(f"Total building blocks in save: {len(bld_keys)}")
    if bld_keys:
        sample_blds = set()
        for bk in bld_keys[:50]:
            sample_blds.update(bk.split())
        print("Sample building names:", list(sample_blds)[:15])
