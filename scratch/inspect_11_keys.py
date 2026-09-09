# -*- coding: utf-8 -*-
import sys, re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

text = open('reports/melted.txt', 'r', encoding='utf-8').read()

# Let's inspect the 11 domain IDs:
domain_ids = ['5658', '5659', '5673', '5688', '5757', '5683', '5660', '5674', '5689', '5758', '5684']

print("=== INSPECTING THE 11 DOMAIN IDs ===")
for did in domain_ids:
    # search for \ndid={
    p = text.find(f'\n{did}={{')
    if p >= 0:
        chunk = text[p:p+400]
        m_key = re.search(r'key=([^\s\n]+)', chunk)
        m_name = re.search(r'name="([^"]+)"', chunk)
        m_liege = re.search(r'de_facto_liege=(\d+)', chunk)
        print(f"ID {did:<6}: Key = {m_key.group(1) if m_key else 'None':<18} | Name = {m_name.group(1) if m_name else 'None'} | Liege = {m_liege.group(1) if m_liege else 'None'}")
