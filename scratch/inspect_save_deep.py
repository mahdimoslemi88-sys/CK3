# -*- coding: utf-8 -*-
import os, sys, re

text = open('reports/melted.txt', 'r', encoding='utf-8').read()
pid = '8975'

print("=== 1. PLAYER INFO ===")
m_pid = re.search(r'\n' + pid + r'=\{\s*\n\t*first_name=.*?(?=\n\t[0-9]+\=\{)', text, re.DOTALL)
if m_pid:
    block = m_pid.group(0)
    print("Found player block, length:", len(block))
    
    # Spouses
    spouses = re.findall(r'spouse=(\d+)', block)
    print("Spouse IDs:", spouses)
    
    # Children
    children_match = re.search(r'child=\{\s*([^\}]+)\}', block)
    if children_match:
        c_ids = children_match.group(1).split()
        print("Child IDs:", c_ids)
    
    # Perks
    perks_m = re.search(r'perk=\{\s*([^\}]+)\}', block)
    if perks_m:
        print("Perks:", perks_m.group(1).split())
        
    # Claims
    claims = re.findall(r'title=(\d+)\s*\n\t*pressed=(yes|no)', block)
    print("Claims (id, pressed):", claims[:10])

    # MaA / Regiments
    regiments = re.findall(r'regiment=(\d+)', block)
    print("Regiments in player block:", regiments)

print("\n=== 2. TITLE NAMES LOOKUP ===")
# Lookup titles
if m_pid and claims:
    for tid, pressed in claims[:8]:
        tm = re.search(r'\n' + tid + r'=\{\s*\n\t*key="?([^\s\"\n]+)"?', text)
        print(f"Claim Title {tid} ({'Pressed' if pressed=='yes' else 'Unpressed'}):", tm.group(1) if tm else "Unknown")

print("\n=== 3. NEIGHBORS / REGIMENTS IN SAVE ===")
# Find regiments belonging to player
reg_matches = re.findall(r'(\d+)=\{\s*\n\t*type="?([^\s\"\n]+)"?\s*\n\t*owner=' + pid, text)
print("Regiments with owner=8975:", reg_matches)

print("\n=== 4. DYNASTY & RENOWN ===")
m_dyn_id = re.search(r'\ndynasties=\{\s*\n(.*?)(?=\n\t*dynasty_houses=\{)', text, re.DOTALL)
m_house = re.search(r'\n5269=\{\s*\n(.*?)(?=\n\t*\d+=\{)', text, re.DOTALL)
if m_house:
    print("House 5269 data:\n", m_house.group(1)[:300])

print("\n=== 5. STRUGGLE DATA ===")
m_struggle = re.search(r'\nstruggles=\{\s*\n(.*?)(?=\n\t*\})', text, re.DOTALL)
if m_struggle:
    print("Struggles:\n", m_struggle.group(1)[:400])

print("\n=== 6. FACTIONS ===")
m_factions = re.search(r'\nfactions=\{\s*\n(.*?)(?=\n\t*factions_manager=\{)', text, re.DOTALL)
if m_factions:
    print("Factions block sample:\n", m_factions.group(1)[:400])

print("\n=== 7. COUNCIL TASKS & OPINION ===")
m_council = re.search(r'council=\{\s*([^\}]+)\}', block)
if m_council:
    c_ids = m_council.group(1).split()
    print("Council member IDs:", c_ids)
    for cid in c_ids:
        cm = re.search(r'\n' + cid + r'=\{\s*\n\t*first_name="?([^\s\"\n]+)"?.*?\n\tskill=\{\s*([^\}]+)\}', text, re.DOTALL)
        if cm:
            print(f"Councillor {cid} ({cm.group(1)}): Skills = {cm.group(2)}")
