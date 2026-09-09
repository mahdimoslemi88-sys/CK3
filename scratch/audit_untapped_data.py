# -*- coding: utf-8 -*-
import re

text = open('reports/melted.txt', 'r', encoding='utf-8').read()
pid = '8975'

print("=== CHECKING UNTAPPED DATA FIELDS ===")

# 1. Player block
m_pid = re.search(r'\n' + pid + r'=\{\s*\n\t*first_name=.*?(?=\n\d+=\{\s*\n\t*first_name=)', text, re.DOTALL)
block = m_pid.group(0) if m_pid else ""

# Artifacts
artifacts = re.findall(r'artifacts=\{\s*([^\}]+)\}', block)
print("1. Artifacts IDs:", artifacts)

# Secrets & Hooks
secrets = re.findall(r'secrets=\{\s*([^\}]+)\}', block)
targeting_secrets = re.findall(r'targeting_secrets=\{\s*([^\}]+)\}', block)
print("2. Secrets known:", secrets, "Targeting secrets:", targeting_secrets)

# Prisoners
prisoners = re.findall(r'prisoners=\{\s*([^\}]+)\}', block)
print("3. Prisoners in dungeon:", prisoners)

# Truces / Diplo
truces = re.findall(r'truce=\{\s*([^\}]+)\}', block)
print("4. Truces:", truces)

# Buildings in Bukhara (c_bukhara=5659, b_bukhara=5660)
m_bukhara = re.search(r'\n5660=\{\s*\n(.*?)(?=\n\d+=\{)', text, re.DOTALL)
if m_bukhara:
    b_text = m_bukhara.group(1)
    buildings = re.findall(r'buildings=\{\s*([^\}]+)\}', b_text)
    holding_type = re.search(r'holding_type="?([^\s\"\n]+)"?', b_text)
    print("5. Bukhara Holding Type:", holding_type.group(1) if holding_type else "?", "Buildings:", buildings)

# County Development & Control (c_bukhara=5659)
m_county = re.search(r'\n5659=\{\s*\n(.*?)(?=\n\d+=\{)', text, re.DOTALL)
if m_county:
    c_text = m_county.group(1)
    dev = re.search(r'development=([\d.]+)', c_text)
    ctrl = re.search(r'control=([\d.]+)', c_text)
    print("6. Bukhara County Development:", dev.group(1) if dev else "0", "Control:", ctrl.group(1) if ctrl else "100")

# Iranian Intermezzo Struggle
m_struggle = re.search(r'persian_struggle=\{\s*\n(.*?)(?=\n\t*[a-zA-Z0-9_]+=\{)', text, re.DOTALL)
if not m_struggle:
    m_struggle = re.search(r'fp3_struggle=\{\s*\n(.*?)(?=\n\t*[a-zA-Z0-9_]+=\{)', text, re.DOTALL)
if m_struggle:
    print("7. Struggle Block:", m_struggle.group(1)[:200])
else:
    # Search for struggle general manager
    sm = re.search(r'struggles=\{\s*\n(.*?)(?=\n\t*\})', text, re.DOTALL)
    print("7. General Struggles:", sm.group(1)[:200] if sm else "None")

# Culture & Innovations (culture=95)
m_cul = re.search(r'\n95=\{\s*\n(.*?)(?=\n\d+=\{)', text, re.DOTALL)
if m_cul:
    cul_text = m_cul.group(1)
    cul_name = re.search(r'name="?([^\s\"\n]+)"?', cul_text)
    cul_head = re.search(r'head=(\d+)', cul_text)
    cul_fasc = re.search(r'fascination="?([^\s\"\n]+)"?', cul_text)
    innovations = re.findall(r'innovations=\{\s*([^\}]+)\}', cul_text)
    print("8. Culture:", cul_name.group(1) if cul_name else "?", "Head ID:", cul_head.group(1) if cul_head else "?", "Fascination:", cul_fasc.group(1) if cul_fasc else "?")

# Vassals Details
vassal_contracts = re.findall(r'vassal_contracts=\{\s*([^\}]+)\}', block)
print("9. Vassal Contract IDs:", vassal_contracts)
