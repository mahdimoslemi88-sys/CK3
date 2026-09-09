# -*- coding: utf-8 -*-
import sys, re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

text = open('reports/melted.txt', 'r', encoding='utf-8').read()
pid = '8975'

out_lines = []
out_lines.append("=== بررسی فیلدهای استخراج‌نشده در سیو ===")

m_pid = re.search(r'\n' + pid + r'=\{\s*\n\t*first_name=.*?(?=\n\d+=\{\s*\n\t*first_name=)', text, re.DOTALL)
block = m_pid.group(0) if m_pid else ""

# 1. Culture
m_cul = re.search(r'\n95=\{\s*\n(.*?)(?=\n\d+=\{)', text, re.DOTALL)
if m_cul:
    cul_text = m_cul.group(1)
    cul_name = re.search(r'name="?([^"\s\n]+)"?', cul_text)
    cul_head = re.search(r'head=(\d+)', cul_text)
    out_lines.append(f"1. فرهنگ: {cul_name.group(1) if cul_name else '95'} | رهبر فرهنگ: ID {cul_head.group(1) if cul_head else '؟'}")

# 2. House & Dynasty Renown
m_house = re.search(r'\ndynasty_house=\{\s*(\d+)', block)
m_house_id = re.search(r'dynasty_house=(\d+)', block)
if m_house_id:
    hid = m_house_id.group(1)
    # Search house block
    hm = re.search(r'\n' + hid + r'=\{\s*\n(.*?)(?=\n\d+=\{)', text, re.DOTALL)
    if hm:
        htext = hm.group(1)
        h_name = re.search(r'name="?([^"\s\n]+)"?', htext)
        dyn_id = re.search(r'dynasty=(\d+)', htext)
        h_head = re.search(r'head=(\d+)', htext)
        out_lines.append(f"2. خاندان: {h_name.group(1) if h_name else hid} | رئیس خاندان: ID {h_head.group(1) if h_head else '؟'} | شناسه سلسله: {dyn_id.group(1) if dyn_id else '؟'}")
        if dyn_id:
            dm = re.search(r'\n' + dyn_id.group(1) + r'=\{\s*\n(.*?)(?=\n\d+=\{)', text, re.DOTALL)
            if dm:
                dtext = dm.group(1)
                prestige_val = re.search(r'currency=([\d.]+)', dtext)
                dynast = re.search(r'dynast=(\d+)', dtext)
                out_lines.append(f"   👑 شهرت سلسله (Renown): {prestige_val.group(1) if prestige_val else '0'} | سرسلسله: ID {dynast.group(1) if dynast else '؟'}")

# 3. Council Members & Tasks
m_council = re.search(r'council=\{\s*([^\}]+)\}', block)
if m_council:
    c_ids = m_council.group(1).split()
    out_lines.append(f"3. اعضای شورا ({len(c_ids)} نفر):")
    for cid in c_ids:
        cm = re.search(r'\n' + cid + r'=\{\s*\n\t*first_name="?([^"\s\n]+)"?.*?\n\tskill=\{\s*([^\}]+)\}', text, re.DOTALL)
        # Check task in court_data
        ctask_m = re.search(r'\n' + cid + r'=\{.*?\n\tcourt_data=\{.*?\n\t\tcouncil_task=(\d+)', text, re.DOTALL)
        task_str = f"Task ID {ctask_m.group(1)}" if ctask_m else "بدون مأموریت"
        if cm:
            skills = cm.group(2).strip().split()
            out_lines.append(f"   - عضو ID {cid} ({cm.group(1)}): مهارت‌ها={skills} | مأموریت فعلی={task_str}")

# 4. Vassals & Opinion
vassal_contracts = re.findall(r'vassal_contracts=\{\s*([^\}]+)\}', block)
if vassal_contracts:
    out_lines.append(f"4. قراردادهای رعایا ({len(vassal_contracts[0].split())} مورد): {vassal_contracts[0].strip()}")

# 5. Court Positions
cpos_m = re.search(r'court_positions=\{\s*([^\}]+)\}', block)
if cpos_m:
    cpos_ids = cpos_m.group(1).split()
    out_lines.append(f"5. مناصب درباری فعال ({len(cpos_ids)} منصب):")
    for cpid in cpos_ids:
        cpm = re.search(r'\n' + cpid + r'=\{\s*\n\t*type="?([^"\s\n]+)"?.*?\n\t*holder=(\d+)', text, re.DOTALL)
        if cpm:
            out_lines.append(f"   - منصب: {cpm.group(1)} (دارنده: ID {cpm.group(2)})")

# 6. Holdings & Buildings in Domain
out_lines.append("6. بررسی ساختمان‌ها و توسعه ولایات مستقیم:")
# Bukhara province/holding: 5660 (barony b_bukhara)
for bid in [5660, 5604, 5678]: # baronies
    bm = re.search(r'\n' + str(bid) + r'=\{\s*\n(.*?)(?=\n\d+=\{)', text, re.DOTALL)
    if bm:
        btext = bm.group(1)
        b_key = re.search(r'key="?([^"\s\n]+)"?', btext)
        b_buildings = re.search(r'buildings=\{\s*([^\}]+)\}', btext)
        b_type = re.search(r'holding_type="?([^"\s\n]+)"?', btext)
        out_lines.append(f"   - بارونی {bid} ({b_key.group(1) if b_key else '?'}): نوع={b_type.group(1) if b_type else 'castle'} | ساختمان‌ها={b_buildings.group(1) if b_buildings else 'ندارد'}")

# 7. Tax Slots in Clan Government
tax_slots = re.findall(r'tax_slot=\{\s*([^\}]+)\}', block)
if tax_slots:
    out_lines.append(f"7. حوزه‌های مالیاتی Clan (Tax Jurisdictions): {tax_slots[0].strip()}")

report_text = "\n".join(out_lines)
with open('scratch/untapped_report.txt', 'w', encoding='utf-8') as f:
    f.write(report_text)
print(report_text)
