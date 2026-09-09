# -*- coding: utf-8 -*-
import re, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

text = open('reports/melted.txt', 'r', encoding='utf-8').read()
pid = '8975'

m_pid = re.search(r'\n' + pid + r'=\{\s*\n\t*first_name=.*?(?=\n\d+=\{\s*\n\t*first_name=)', text, re.DOTALL)
block = m_pid.group(0) if m_pid else ""

print("=== 1. CHILDREN BREAKDOWN ===")
children_match = re.search(r'child=\{\s*([^\}]+)\}', block)
if children_match:
    for cid in children_match.group(1).split():
        cm = re.search(r'\n' + cid + r'=\{\s*\n\t*first_name="?([^"\s\n]+)"?.*?\n\tbirth=([0-9.]+)', text, re.DOTALL)
        is_female = bool(re.search(r'\n' + cid + r'=\{.*?\n\tfemale=yes', text, re.DOTALL))
        if cm:
            print(f"Child {cid}: {cm.group(1)} ({'دختر / Female' if is_female else 'پسر / MALE WARRIOR! 👑'}) born {cm.group(2)}")

print("\n=== 2. BUILDINGS IN HELD COUNTIES ===")
for bid, bname in [(5660, "بخارا"), (5688, "سمرقند"), (5678, "فرابر"), (5604, "اوزگند"), (5767, "نخشب")]:
    bm = re.search(r'\n' + str(bid) + r'=\{\s*\n(.*?)(?=\n\d+=\{)', text, re.DOTALL)
    if bm:
        b_buildings = re.search(r'buildings=\{\s*([^\}]+)\}', bm.group(1))
        print(f"Holding {bname} ({bid}): Buildings = {b_buildings.group(1) if b_buildings else 'خالی'}")

print("\n=== 3. VASSALS & FACTIONS ===")
vassal_m = re.search(r'vassal_contracts=\{\s*([^\}]+)\}', block)
if vassal_m:
    print("Vassals count:", len(vassal_m.group(1).split()))
