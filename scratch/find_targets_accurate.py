# -*- coding: utf-8 -*-
import re

text = open('reports/melted.txt', 'r', encoding='utf-8').read()

# Let's find all titles starting with c_ or d_ around Central Asia / Steppes / Khorasan
# We'll search for blocks \n\d+={\n\tkey=c_...
title_blocks = re.findall(r'\n(\d+)=\{\s*\n\t*key=(c_[a-zA-Z0-9_]+|d_[a-zA-Z0-9_]+)\s*\n(.*?)(?=\n\d+=\{)', text, re.DOTALL)

print(f"Total titles found: {len(title_blocks)}")

interesting = ["c_farab", "c_otrar", "c_taraz", "c_chach", "c_khiva", "c_urgend", "c_kath", "c_amul", "c_merv", "c_samarkand", "c_ferghana", "c_khojand", "c_balkh", "d_khwarazm", "d_transoxiana", "d_khorasan", "d_ferghana", "d_chach"]

results = []
for tid, tkey, tbody in title_blocks:
    if tkey in interesting or "oghuz" in tkey or "karluk" in tkey or "khiva" in tkey:
        holder_m = re.search(r'\bholder=(\d+)', tbody)
        df_liege_m = re.search(r'\bde_facto_liege=(\d+)', tbody)
        name_m = re.search(r'name="([^"]+)"', tbody)
        
        holder_id = holder_m.group(1) if holder_m else "None"
        df_liege = df_liege_m.group(1) if df_liege_m else "None"
        
        hname, hfaith, hstr, hliege = "Unknown", "?", "?", "Independent"
        if holder_id != "None":
            hm = re.search(r'\n' + holder_id + r'=\{\s*\n\t*first_name="?([^\s\"\n]+)"?.*?\n\t*faith=(\d+)', text, re.DOTALL)
            if hm:
                hname = hm.group(1)
                hfaith = hm.group(2)
                fm = re.search(r'\n' + hfaith + r'=\{\s*\n\t*tag="?([^\s\"\n]+)"?', text)
                hfaith = fm.group(1) if fm else f"Faith_{hfaith}"
                
                sm = re.search(r'\n' + holder_id + r'=\{.*?\n\tlanded_data=\{.*?current_strength=(\d+)', text, re.DOTALL)
                hstr = sm.group(1) if sm else "?"
                
                lm = re.search(r'\n' + holder_id + r'=\{.*?\n\tlanded_data=\{.*?liege=(\d+)', text, re.DOTALL)
                if lm:
                    hliege = f"Vassal of {lm.group(1)}"
        
        results.append(f"{tkey:<15} (ID:{tid:<5}) | Holder: {hname:<12} (ID:{holder_id:<6}) | Army: {hstr:<5} | Faith: {hfaith:<15} | Status: {hliege}")

with open('scratch/target_analysis.txt', 'w', encoding='utf-8') as out:
    out.write("\n".join(results))

print("Results written to scratch/target_analysis.txt")
