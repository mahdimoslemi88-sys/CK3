# گزارش مرحلهٔ ۳ — عملیاتی‌سازی (Actionability)

**پروژه:** vizier-counsel · **تاریخ:** 970.1.1 (سیو `autosave.ck3`) · **وضعیت:** کامل — منتظر تأیید انسانی

این مرحله، پیشنهادهای `docs/ACTIONABILITY_PROPOSAL.md` را پیاده کرد: پاک‌سازی نام جنگ‌ها،
فیلتر sentinel، اتصال قابل‌اثبات فکشن‌ها، بلوک منابع بازیکن، فیلتر دامنهٔ `counties` با
تجمیع جهانی، و ثبت قواعد «کارت فرمان» در workflow و راهنما.

## فایل‌های تغییرکرده (این مرحله)

| فایل | تغییر |
|---|---|
| `extract_save.py` | `_no_sentinel` (خط ۱۳۰۰)، `_clean_war_name` (خط ۱۳۰۷)، `extract_wars` → `name_raw/name/name_refs/cb_claimant` (خطوط ۱۳۹۱–۱۳۹۵)، اتصال‌های فکشن `target_kind/target_is_player/is_civil_war` (خطوط ۱۰۵۸–۱۰۷۵)، `_resources_block` (خط ۸۹۱) و `player["resources"]` (خط ۹۳۶)، `extract_counties(root, domain_title_ids)` + `world_total/world_dev_avg/world_ctrl_avg` (خطوط ۵۸۷–۶۵۷)، سیم‌کشی در `cmd_extract` (خطوط ۲۰۳۳–۲۰۳۵)، تجمیع جهانی در `meta` (خطوط ۱۶۱۶–۱۶۱۸) |
| `tests/test_actionability.py` | ۲۵ تست fixture-محور برای هر پنج اصلاح (طبقات: CleanWarName، NoSentinel، FactionJoins، ResourcesBlock، CountiesScope، WarsOutput) |
| `.agents/rules/vizier-workflow.md` | اصل ۵ → کارت فرمان ۷ فیلدی + الزامات عملیاتی ۳گانهٔ ساب‌ایجنت‌ها (توان پرداخت از `player.resources`، سطر «برای سیو بعدی چه عددی باید تغییر کند») |
| `docs/CK3_STRATEGY_GUIDE.md` | فصل ۹ «هزینه‌ها و توان پرداخت» + جدول هزینه‌ها با برچسب منبع |
| `reports/state_report.json` | خروجی واقعی با همهٔ اصلاحات (تولیدشده توسط اجرای سیو) |

## نتایج اجرای سیو واقعی (قبل → بعد)

| سنجه | قبل | بعد |
|---|---|---|
| نام‌های جنگِ خوانا | ۸ از ۱۰۹ (۷۱٪ آلوده به مارک‌آپ) | **۱۰۹ از ۱۰۹** — صفر مارک‌آپ باقی‌مانده |
| مراجع قابل‌اثبات نام جنگ | ۰ | **۹۵ جنگ** با `name_refs` (title/character ID از خود مارک‌آپ) |
| CBهای دارای sentinel خام | ۵۶ مورد `4294967295` | **۰** — همه → `null` |
| فکتون‌هایی که بازیکن را هدف می‌گیرند | ۰ قابل‌شناسایی | **۲۰ رابطهٔ اثبات‌شدهٔ جنگ داخلی** (`is_civil_war=true`) + `target_kind` روی همهٔ ۲۰۹ فکتون |
| `player.vassal_power_value` | null | null (واقعاً در سیو نیست — صفر گزارش نشد) |
| `counties` در JSON | ۲۶۵۲ ردیف (۵۴۹KB) | **۴ ردیف دامنهٔ بازیکن** + تجمیع جهانی در `meta` |
| فصل ۸ راهنما: ستون `vassal_power_value` | خالی | هنوز null — داده در سیو موجود نیست، ادعایی نشد |

`player.resources` واقعی (سیو 970.1.1): `gold: 85094.51, piety: 191.61 (accumulated 1821.35), prestige: 3629.06 (accumulated 5061.50)`.

## تست‌ها

فرمان: `python -m pytest tests/ -q`  ·  Exit Code: **0**  ·  **111 passed** (57.4s)

شکسته‌بندی مرتبط با این مرحله: `tests/test_actionability.py` — ۲۵ تست شامل ۷ حالت
پاک‌سازی نام، ۳ تست sentinel، ۵ تست اتصال فکشن (شامل «war ناموجود ≠ جنگ داخلی»)،
۴ تست بلوک منابع (شامل «صفر واقعی ≠ missing»)، ۴ تست فیلتر دامنهٔ counties
(شامل «حذف فیلتر = رفتار قدیمی»)، ۴ تست خروجی جنگ.

## شاهدهای file:line

- پاک‌سازی نام جنگ و استخراج مراجع: `extract_save.py:1307-1329`
- sentinel → null: `extract_save.py:1298-1305`
- اتصال فکشن: `extract_save.py:1058-1075`
- بلوک منابع: `extract_save.py:891-905`، سیم‌کشی: `extract_save.py:936`
- فیلتر دامنهٔ counties: `extract_save.py:587-657`، سیم‌کشی: `extract_save.py:2033-2035`
- تجمیع جهانی در meta: `extract_save.py:1616-1618`
- اصل کارت فرمان در workflow: `.agents/rules/vizier-workflow.md:42-65`
- الزامات ۳گانهٔ ساب‌ایجنت: `.agents/rules/vizier-workflow.md:73-81`
- فصل ۹ راهنما: `docs/CK3_STRATEGY_GUIDE.md:139-165`
- تست‌ها: `tests/test_actionability.py:1-277`

## فایل‌های خارج از Scope که تغییر نکردند

`extract_save.py` خارج از توابع مذکور، `AGENTS.md`، `parsed_docs.txt`،
`docs/GEMINI_EXTRACTION_PROMPT.md`، `docs/ACTIONABILITY_PROPOSAL.md`،
`reports/melted.txt`، `tools/rakaly.exe`، همهٔ اسکیل‌ها (`.agents/skills/`)،
اسنپ‌شات‌های تاریخچه (`reports/history/*`).

## باقی‌مانده برای مرحلهٔ بعد (پیشنهاد ۴ سند proposal)

- `vassal_power_value`: در سیو 970.1.1 وجود ندارد؛ اگر در سیوهای بعدی ظاهر شد، join آن به `vassals[]` باید اضافه شود.
- شمارش building/درآمد per-holding: خالی است؛ نیاز به بررسی ساختار `building` در holdingهای واقعی دارد.
- opinion بین شخصیت‌ها (اگر در سیو باشد) برای کارت‌های دیپلماسی.
- موقعیت ارتش/rally points برای کارت‌های نظامی.
- مصرف‌کنندگان کارت فرمان: ۶ وزیر الان قواعد را دارند؛ اولین اجرای واقعی همهٔ وزیرها با گزارش 970.1.1 باید ممیزی شود.

## READY FOR HUMAN VERIFY
