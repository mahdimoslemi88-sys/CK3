# -*- coding: utf-8 -*-
import sys, re

text = open('reports/melted.txt', 'r', encoding='utf-8').read()

for tid in ['5658', '5659', '5673', '5688', '5757', '5683', '5660', '5674', '5689', '5758', '5684']:
    # Search for \ntid={
    p = text.find(f'\n{tid}={{')
    if p < 0:
        p = text.find(f'\n\t{tid}={{')
    if p < 0:
        p = text.find(f'\n\t\t{tid}={{')
    if p >= 0:
        chunk = text[p:p+600]
        # check if it's title
        if 'key=' in chunk or 'holding=' in chunk:
            k = re.search(r'key="?([^"\s\n]+)"?', chunk)
            h = re.search(r'holder=(\d+)', chunk)
            ht = re.search(r'type="?([^"\s\n]+)"?', chunk)
            print(f"ID {tid}: Key={k.group(1) if k else 'no-key'} | Holder={h.group(1) if h else 'no-holder'} | HoldingType={ht.group(1) if ht else 'no-ht'}")
            print("  Snippet:", chunk.replace('\n', ' ')[:150])
            print("-----------------")
