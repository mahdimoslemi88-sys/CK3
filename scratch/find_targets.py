# -*- coding: utf-8 -*-
import re

text = open('reports/melted.txt', 'r', encoding='utf-8').read()

# Let's find nearby titles / rulers in Central Asia (Transoxiana / Steppe)
# c_farab, c_otrar, c_taraz, c_chach, c_khiva, c_gurgan, d_oghuz, d_karluk, d_kimak, k_transoxiana
target_titles = [
    "c_farab", "c_otrar", "c_taraz", "c_chach", "c_khiva", "c_gurgan", "c_amul",
    "c_merv", "c_kath", "c_urgend", "d_khwarazm", "d_ferghana", "d_chach"
]

print("=== TARGET TITLES & HOLDERS ===")
for title_key in target_titles:
    tm = re.search(r'\n(\d+)=\{\s*\n\t*key="' + title_key + r'"\s*\n\t*holder=(\d+)', text)
    if tm:
        tid, holder_id = tm.group(1), tm.group(2)
        # Look up holder
        hm = re.search(r'\n' + holder_id + r'=\{\s*\n\t*first_name="?([^\s\"\n]+)"?.*?\n\t*faith=(\d+).*?\n\t*landed_data=\{\s*\n\t*domain=.*?current_strength=(\d+)', text, re.DOTALL)
        if hm:
            hname, hfaith, hstrength = hm.group(1), hm.group(2), hm.group(3)
            # lookup faith name
            fm = re.search(r'\n' + hfaith + r'=\{\s*\n\t*tag="?([^\s\"\n]+)"?', text)
            fname = fm.group(1) if fm else f"Faith_{hfaith}"
            print(f"Title: {title_key:<12} | Holder: {hname:<12} (ID:{holder_id}) | Faith: {fname:<15} | Army: {hstrength}")
        else:
            print(f"Title: {title_key:<12} | Holder ID: {holder_id}")
