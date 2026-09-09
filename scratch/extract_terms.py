import os, re

mod_path = r"C:\Users\LENOVO LOQ\Documents\Paradox Interactive\Crusader Kings III\mod\PersianCK\localization\english"

keys_to_find = {
    "task_manage_domain": "Manage Domain",
    "golden_obligations_perk_name": "Golden Obligations",
    "stewardship": "Stewardship",
    "martial": "Martial",
    "diplomacy": "Diplomacy",
    "intrigue": "Intrigue",
    "learning": "Learning",
    "prowess": "Prowess",
    "sway": "Sway",
    "holy_war": "Holy War",
    "pressed_claim": "Pressed Claim",
    "unpressed_claim": "Unpressed Claim",
    "tax_collector": "Tax Collector",
    "vizier": "Vizier",
    "house_unity": "House Unity",
    "struggle": "Struggle",
    "concession": "Concession",
    "men_at_arms": "Men-at-Arms",
    "heavy_infantry": "Heavy Infantry",
    "claim_throne": "Claim Throne",
    "manage_domain": "Manage Domain",
    "sway_scheme": "Sway Scheme",
    "casabelli": "Casus Belli",
    "tax_decree": "Tax Decree",
    "iqta": "Iqta",
    "muqata": "Muqata",
    "wealth_focus": "Wealth Focus",
    "domain_limit": "Domain Limit"
}

results = {}

for root, _, files in os.walk(mod_path):
    for f in files:
        if not f.endswith(".yml"): continue
        p = os.path.join(root, f)
        try:
            with open(p, "r", encoding="utf-8-sig") as file:
                for line in file:
                    line = line.strip()
                    if not line: continue
                    match = re.match(r'^([a-zA-Z0-9_\-\.]+):\d*\s*"(.*)"', line)
                    if match:
                        key = match.group(1).lower()
                        for target_key in keys_to_find:
                            if target_key == key or key == f"skill_{target_key}" or target_key in key:
                                if target_key not in results or key == target_key or key == f"skill_{target_key}":
                                    results[target_key] = match.group(2)
        except Exception as e:
            pass

with open(r"C:\Users\LENOVO LOQ\Desktop\projects\vizier-counsel\scratch\terms.txt", "w", encoding="utf-8") as out:
    out.write("=== ترجمه‌های استخراج شده ===\n")
    for k, v in results.items():
        out.write(f"{keys_to_find[k]}: {v}\n")
