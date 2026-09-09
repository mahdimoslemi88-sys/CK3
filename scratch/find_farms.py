# -*- coding: utf-8 -*-
import sys, re

text = open('reports/melted.txt', 'r', encoding='utf-8').read()

# Let's inspect b_bukhara (5660) and b_samarkand (5689)
for tid in ["5660", "5689", "5679", "5674"]:
    tm = re.search(r'\n(\t*)' + tid + r'=\{\s*\n(.*?)(?=\n\1\d+=\{|\Z)', text, re.DOTALL)
    if tm:
        print(f"Title {tid} content:\n", tm.group(2)[:300])
        print("-------------------")

# Let's search for "farms_and_fields" in all province blocks
farms_provs = re.findall(r'\n(\d+)=\{\s*\n\t*holding=\{\s*\n\t*buildings=\{\s*\n[^\}]*?farms_and_fields[^\}]*?\}', text)
print("Provinces with farms_and_fields in the world:", farms_provs[:10])

# For each prov with farms, let's see who holds it
if farms_provs:
    for p in farms_provs[:5]:
        pm = re.search(r'\n' + p + r'=\{\s*\n\t*holding=\{\s*\n(.*?)(?=\n\d+=\{|\Z)', text, re.DOTALL)
        if pm:
            print(f"Prov {p} holding:\n", pm.group(1)[:250])
