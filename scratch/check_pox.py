# -*- coding: utf-8 -*-
import sys, re

text = open('reports/melted.txt', 'r', encoding='utf-8').read()
pid = '16817309'

# Find player block
m_p = re.search(r'\n(\t*)' + pid + r'=\{\s*\n\t*first_name=.*?(?=\n\1\d+=\{\s*\n\t*first_name=|\Z)', text, re.DOTALL)
if m_p:
    block = m_p.group(0)
    # find traits lookup
    tl_block = text[text.find('traits_lookup='):text.find('traits_lookup=')+5000]
    traits_list = tl_block.strip("{} \n\t").split()
    
    tids = re.findall(r'traits=\{\s*([^\}]+)\}', block)
    if tids:
        player_traits = [int(x) for x in tids[0].split()]
        print("Player traits:")
        for t in player_traits:
            if t < len(traits_list):
                print(f" - {t}: {traits_list[t]}")
