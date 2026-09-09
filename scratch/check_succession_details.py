# -*- coding: utf-8 -*-
import sys, re

text = open('reports/melted.txt', 'r', encoding='utf-8').read()
pid = '16817309'

# Find player block
m_p = re.search(r'\n(\t*)' + pid + r'=\{\s*\n\t*first_name=.*?(?=\n\1\d+=\{\s*\n\t*first_name=|\Z)', text, re.DOTALL)
block = m_p.group(0) if m_p else ""

print("=== 1. PLAYER DETAILS ===")
traits = re.search(r'traits=\{\s*([^\}]+)\}', block)
print("Traits IDs:", traits.group(1).split() if traits else "None")

# Primary spouse
spouse_m = re.findall(r'spouse=(\d+)', block)
print("Spouses:", spouse_m)
for sid in spouse_m:
    sm = re.search(r'\n(\t*)' + sid + r'=\{\s*\n\t*first_name="?([^"\s\n]+)"?.*?\n\tskill=\{\s*([^\}]+)\}', text, re.DOTALL)
    if sm:
        print(f"Spouse {sid} ({sm.group(2)}): Skills = {sm.group(3)}")

# Brother Gushtasb (47280) and other siblings
m_fam = re.search(r'family_data=\{\s*\n(.*?)(?=\n\t*\w+_data=\{|\n\})', block, re.DOTALL)
if m_fam:
    print("Family data:\n", m_fam.group(1))

# Who holds c_firabr and c_uzgend?
for ckey in ["c_firabr", "c_uzgend_KARA", "c_samarkand", "c_bukhara", "c_khojand"]:
    tm = re.search(r'\n(\d+)=\{\s*\n\t*key="' + ckey + r'"\s*\n\t*holder=(\d+)', text)
    if not tm:
        tm = re.search(r'\n(\d+)=\{\s*\n\t*key=' + ckey + r'\b.*?\n\t*holder=(\d+)', text)
    if tm:
        tid, hid = tm.group(1), tm.group(2)
        hm = re.search(r'\n' + hid + r'=\{\s*\n\t*first_name="?([^"\s\n]+)"?', text)
        print(f"Title {ckey} ({tid}): Holder = {hm.group(1) if hm else '?'} (ID: {hid})")
