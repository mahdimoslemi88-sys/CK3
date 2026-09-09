# -*- coding: utf-8 -*-
import re, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

text = open('reports/melted.txt', 'r', encoding='utf-8').read()

held_counties = ["c_bukhara", "c_samarkand", "c_firabr", "c_uzgend_KARA"]

print("=== وضعیت اقلیم و ساختمان‌های ولایات در دست ===")

for ckey in held_counties:
    # find county title
    cm = re.search(r'\n(\d+)=\{\s*\n\t*key="' + ckey + r'"\s*\n(.*?)(?=\n\d+=\{)', text, re.DOTALL)
    if not cm:
        cm = re.search(r'\n(\d+)=\{\s*\n\t*key=' + ckey + r'\b\s*\n(.*?)(?=\n\d+=\{)', text, re.DOTALL)
    if cm:
        cid, cbody = cm.group(1), cm.group(2)
        dev = re.search(r'development=([\d.]+)', cbody)
        ctrl = re.search(r'control=([\d.]+)', cbody)
        vassals = re.search(r'de_jure_vassals=\{\s*([^\}]+)\}', cbody)
        barony_ids = vassals.group(1).split() if vassals else []
        
        print(f"\n🏰 ولایت: {ckey} (شناسه: {cid}) | توسعه: {dev.group(1) if dev else '0'} | کنترل: {ctrl.group(1) if ctrl else '100'}%")
        print(f"   بارونی‌های دوژور ({len(barony_ids)} بارونی):")
        
        for bid in barony_ids:
            bm = re.search(r'\n' + bid + r'=\{\s*\n(.*?)(?=\n\d+=\{)', text, re.DOTALL)
            if bm:
                bbody = bm.group(1)
                bkey = re.search(r'key="?([^"\s\n]+)"?', bbody)
                btype = re.search(r'holding_type="?([^"\s\n]+)"?', bbody)
                bholder = re.search(r'holder=(\d+)', bbody)
                b_buildings = re.search(r'buildings=\{\s*([^\}]+)\}', bbody)
                
                holder_str = "مالکیت مستقیم شما" if (bholder and bholder.group(1) == '8975') else f"دارنده: {bholder.group(1) if bholder else 'خالی'}"
                b_list = b_buildings.group(1).split() if b_buildings else []
                
                print(f"     - بارونی {bkey.group(1) if bkey else bid} ({btype.group(1) if btype else 'castle'}): {holder_str} | ساختمان‌ها: {b_list if b_list else 'خالی'}")
