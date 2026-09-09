import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

# Let's find all counties that have culture=91
# In CK3 save, landed_titles has:
# c_something={
#   ...
#   culture=91 (or in province/county history)
# Actually in CK3, county culture is stored in:
# 1) provinces: province_id={ culture=91 ... } OR
# 2) landed_titles: c_xxx={ ... } (sometimes culture is at county title level or county capital barony)
# Let's check how extract_save.py finds county culture!

with open('extract_save.py', 'r', encoding='utf-8') as f:
    for line in f:
        if 'culture' in line and ('county' in line or 'counties' in line or 'province' in line):
            print(line.rstrip()[:100])
