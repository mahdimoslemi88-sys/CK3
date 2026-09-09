# -*- coding: utf-8 -*-
import os, sys, re

text = open('reports/melted.txt', 'r', encoding='utf-8').read()
pid = '8975'

print("=== SEARCHING REGIMENTS ===")
for m in re.finditer(r'regiments=\{\s*\n(.*?)(?=\n\t*\})', text, re.DOTALL):
    print("Found regiments block:", m.group(1)[:200])
    break

# Let's find "regiment=" or "type=" in player's military
m_pid = re.search(r'\n' + pid + r'=\{\s*\n\t*first_name=.*?(?=\n\t[0-9]+\=\{)', text, re.DOTALL)
if m_pid:
    block = m_pid.group(0)
    print("\n=== PLAYER MILITARY & DOMAIN KEYS ===")
    for k in set(re.findall(r'([a-zA-Z_]+)=', block)):
        print(k, end=", ")
    print()

print("\n=== SPOUSES DETAILS ===")
spouses = re.findall(r'spouse=(\d+)', block)
for sid in set(spouses):
    sm = re.search(r'\n' + sid + r'=\{\s*\n\t*first_name="?([^\s\"\n]+)"?.*?\n\tskill=\{\s*([^\}]+)\}', text, re.DOTALL)
    if sm:
        skills = [int(x) for x in sm.group(2).split()]
        print(f"Spouse {sid} ({sm.group(1)}): Stewardship={skills[2] if len(skills)>2 else '?'}, Skills={skills}")

print("\n=== CHILDREN DETAILS ===")
children_match = re.search(r'child=\{\s*([^\}]+)\}', block)
if children_match:
    for cid in children_match.group(1).split():
        cm = re.search(r'\n' + cid + r'=\{\s*\n\t*first_name="?([^\s\"\n]+)"?.*?\n\tbirth=([0-9.]+)', text, re.DOTALL)
        if cm:
            print(f"Child {cid} ({cm.group(1)}): Born {cm.group(2)}")

print("\n=== COURT POSITIONS ===")
court_pos = re.search(r'court_positions=\{\s*([^\}]+)\}', block)
if court_pos:
    for cpid in court_pos.group(1).split():
        cpm = re.search(r'\n' + cpid + r'=\{\s*\n\t*type="?([^\s\"\n]+)"?.*?\n\tholder=(\d+)', text, re.DOTALL)
        if cpm:
            print(f"Court Position {cpid}: {cpm.group(1)} (Holder: {cpm.group(2)})")
