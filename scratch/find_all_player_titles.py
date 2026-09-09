# -*- coding: utf-8 -*-
import sys, re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

text = open('reports/melted.txt', 'r', encoding='utf-8').read()

print("Searching for landed_titles section...")
p_lt = text.find('landed_titles={')
if p_lt < 0:
    p_lt = text.find('\nlanded_titles={')
print("landed_titles pos:", p_lt)

# Let's search for c_bukhara
p_buk = text.find('key="c_bukhara"')
if p_buk < 0:
    p_buk = text.find('key=c_bukhara')
print("c_bukhara pos:", p_buk)

if p_buk >= 0:
    print("c_bukhara context:\n", text[p_buk-50:p_buk+200])

# Let's find all titles where holder=16817309
player_held_titles = []
for m in re.finditer(r'\n(\d+)=\{\s*\n\t*key="?([^"\s\n]+)"?.*?\n\t*holder=16817309\b', text):
    player_held_titles.append((m.group(1), m.group(2)))

print(f"\nAll titles held by player (16817309): Total {len(player_held_titles)}")
for tid, tkey in player_held_titles:
    print(f" - ID {tid}: {tkey}")
