# -*- coding: utf-8 -*-
import sys, re

text = open('reports/melted.txt', 'r', encoding='utf-8').read()

holdings = ["5658", "5659", "5673", "5688", "5757", "5683", "5767", "5660", "5674", "5689", "5758", "5684", "5768"]

for hid in holdings:
    tm = re.search(r'\n(\t*)' + hid + r'=\{\s*\n(.*?)(?=\n\1\d+=\{|\Z)', text, re.DOTALL)
    if tm:
        tbody = tm.group(2)
        tkey = re.search(r'key="?([^"\s\n]+)"?', tbody)
        htype = re.search(r'type="?([a-zA-Z0-9_]+_holding)"?', tbody)
        print(f"ID {hid}: Key={tkey.group(1) if tkey else '?'} | Type={htype.group(1) if htype else 'castle'}")
