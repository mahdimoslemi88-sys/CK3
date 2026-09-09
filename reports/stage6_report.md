# گزارش مرحلهٔ ۶ — ساختمان‌ها، نظرها و موقعیت ارتش‌ها

**پروژه:** vizier-counsel · **سیو:** `autosave.ck3`، تاریخ بازی **1010.1.1** · **وضعیت:** کامل — منتظر تأیید انسانی

هدف این مرحله، سه دادهٔ باقی‌مانده از فهرست پیشنهاد ۴ (`docs/ACTIONABILITY_PROPOSAL.md`) بود:
سطح ساختمان‌ها و سازه‌های در حال ساخت، نظرهای عددی بازیکن، و rally pointها/موقعیت ارتش‌ها.
پیش از هر تغییر، ساختارهای واقعی روی `reports/melted.txt` (تک‌پارس، ۶۷ ثانیه) کاوش شد و
سه فرضِ خام رد یا تأیید شد. هیچ Regex سراسری استفاده نشد؛ همه‌چیز مسیر ساختاری.

## اصلاح شواهد قدیمی (گزارش‌های مرحلهٔ ۴ و ۵ قبلی)

- گزارش مرحلهٔ ۴ می‌گفت rally pointها «قابل‌اتصال قابل‌اثبات نیست» — **نادرست بود**.
  کاوش این مرحله نشان داد `played_character.rally_points` یک list از بلوک‌های
  `{province, color}` است؛ الان استخراج و در همین گزارش ثبت شده.
- فراخوانی ساختمان‌های در حال ساخت قبلاً کلید `construction` را در سطح province
  می‌خواند؛ در سیو واقعی این داده داخل `holding.constructions` است (get_all برای
  چند سازهٔ هم‌زمان). فرم قدیمی province به‌عنوان fallback حفظ شد.

## استخراج API (شاهد file:line — همه در extract_save.py)

| قابلیت | file:line | توضیح |
|---|---|---|
| سطح ساختمان از پسوند نوع | `extract_save.py:662` (`_BLEVEL_RE`)، اعمال در `:721` | `castle_01` → سطح ۱؛ قابل‌اثبات از دادهٔ سیو، بدون حدس |
| اسلات خالی `{ }` | `:717-724` | نوع None و سطح None — هرگز رشتهٔ "unknown" یا حدس |
| سازهٔ در حال ساخت (شکل واقعی سیو) | `:727-739` (`h.get_all("constructions")`) | building/index/start_time/days/cost.gold/cost.prestige/character |
| fallback سازگاری فرم قدیمی | `:740-744` (`pn.children.get("construction")`) | فقط وقتی holding هیچ سازه‌ای ندارد |
| rally points بازیکن | `:1474-1480` (`played_character.rally_points`) | list از `{province, color}` |
| موقعیت ارتش (join ساختاری) | `:1482-1529` | `armies.armies.<id>` با `unit=<ref>` به `units.<ref>` (location/path/arrival_date)؛ فیلتر بازیکن: `name.owner` یا `commander` == player_id |
| `extract_opinions` | `:1570-1649` | `opinions.active_opinions`؛ فقط ردیف‌های درگیر بازیکن؛ `direction` = held_by_player/about_player/both |
| سیم‌کشی cmd_extract | `:2271-2274` | opinions_data به گزارش متنی و JSON |
| شمارنده‌های quality.counts | `:1820-1823` | player_armies / rally_points / player_opinions / opinions_total |
| منبع JSON | `:1844` | `opinions.active_opinions (rows where player is owner or target)` |

## یافته‌های ساختاری (ثبت‌شده، نه حدس)

1. **armies.armies و gathering_armies هر دو فرزند بلوک outer armies هستند** —
   نه فرزند یکدیگر. اولین پیاده‌سازی فرزند را می‌خواند و صفر می‌گرفت؛ تست فیکسچر
   (`test_6b`) این را قبل از اجرای واقعی گرفت.
2. **مکانیزم same_name پارسر:** هر نام تکرارشونده در یک block وارد `same_name` می‌شود؛
   چند `temporary_opinion` هم‌نام در یک ردیف فقط با `get_all` خوانده می‌شوند (نه اولین).
3. **صفرِ واقعی ارتش:** همهٔ ۵۱۰ بلوک army بررسی شد؛ هیچ‌کدام `name.owner`،
   `commander` یا `unit.owner` برابر بازیکن ندارند → `player_armies: 0` صفرِ
   واقعی است (پادشاه در صلح، ارتش جمع‌نشده) — نه missing و نه باگ.
   ۵۷ ارتش دارای `name.owner` صریح‌اند؛ کلید `unit.owner` (شناسهٔ کاراکتر) هم بررسی شد.
4. **holdingهای بدون نوع:** سه province دامنهٔ بازیکن (5659، 6125، 6342) بلوک holding
   با buildings خالی (`{ }`) و بدون `type` دارند — همان ۳ مورد missing قبلی
   (`quality.missing_fields`)؛ الان با ساختارِ قابل‌فهم (buildings=باسلات‌های خالی) گزارش می‌شوند.
5. **opinions.active_opinions:** ردیف‌های بی‌نام `{owner, target, temporary_opinion*,
   scripted_relations?}`؛ ۱۴۴٬۹۴۹ ردیف کل. scripted_relations کلیدِ نوع رابطه در
   سطح اول block است (`friend={flags, reason}`).

## آمار اجرای واقعی (Exit Code 0 — مذکور در ادامه)

| سنجه | مقدار |
|---|---|
| تاریخ بازی | 1010.1.1 (اسنپ‌شات: `snapshot_1010_1_1.json`) |
| جنگ‌های فعال | 97 |
| رکوردهای MAA بازیکن | 6 |
| شوالیه‌ها | 16 |
| ارتش جمع‌شدهٔ بازیکن | **0** (صفرِ واقعی — یافتهٔ ۳) |
| rally points | **10** (استان‌های 4394، 4397، 4421، 7138، 4460، 4461، 1431، 4244، 7964، 4223) |
| نظرهای درگیر بازیکن | **220** از 144,949 ردیف (خروجی JSON فقط این‌ها) |
| holdings دامنهٔ بازیکن | 5 |
| ساختمان‌های این ۵ holding | 18 نمونه؛ سطحِ 9 عدد حل شد (holdingهای واقعی) — 9 اسلات خالی None ماند |
| سازهٔ در حال ساخت (دامنه) | 0 (هیچ holding دامنه‌ای در حال ساخت نیست) |
| کیفیت JSON | valid؛ 15 section؛ `quality.counts` با گزارش متنی یکی |

## تست‌ها

```text
python -m pytest tests/ -q
→ 119 passed, Exit Code 0 (65.5s)
```

شکسته‌بندی جدید این مرحله:

- `tests/test_economy_extract.py:482` — سطح از پسوند (castle_01→1, wall_02→2)
- `tests/test_economy_extract.py:502` — سازهٔ واقعی holding با دو سازهٔ هم‌زمان + هزینهٔ gold/prestige
- `tests/test_economy_extract.py:519` — fallback فرم قدیمی province همچنان کار می‌کند
- `tests/test_economy_extract.py:525` — سطح هرگز رشتهٔ "unknown" نیست (int یا None)
- `tests/test_war_military_extract.py:307` — rally points با شکل واقعی سیو + join ارتش‌ها
  (شامل: ارتشِ رعیت با owner=900 نباید بازیکن شمرده شود)
- `tests/test_war_military_extract.py:326` — opinion: جمع temporary، جهت، scripted بدون عدد = None
- فیکسچر واقعی‌شده: rally_points (بلوک province/color)، armies.armies + units + gathering_armies،
  opinions با ۴ ردیف (سه جهت + ردیف بی‌ربط)

تست‌های قبلی که به‌روزرسانی اجباری داشتند: `test_4` (rally "unavailable" → ساختار واقعی)،
`test_6`/`test_9` (خروجی متنی جدید)، `test_8` (شمارنده‌های جدید JSON).

## فایل‌های تغییرکرده

| فایل | تغییر |
|---|---|
| `extract_save.py` | سطح ساختمان، سازه‌های holding، rally points، join ارتش، `extract_opinions`، سیم‌کشی و شمارنده‌ها (جدول بالا) |
| `tests/test_war_military_extract.py` | فیکسچر واقعی‌شده + تست‌های 6b/6c + به‌روزرسانی 4/6/8/9 |
| `tests/test_economy_extract.py` | فیکسچر (اسلات خالی + سازهٔ واقعی) + ۲ کلاس تست مرحلهٔ ۶ |
| `.agents/rules/vizier-workflow.md` | ثبت `opinions[]` در قرارداد `vizier_diplomacy` + قاعدهٔ تفسیر (null ≠ صفر) |
| `reports/state_report.txt/.json` | خروجی واقعی با بخش‌های جدید |

## فایل‌های خارج از Scope که تغییر نکردند

`AGENTS.md`، `parsed_docs.txt`، `docs/ACTIONABILITY_PROPOSAL.md`، `docs/CK3_STRATEGY_GUIDE.md`،
همهٔ اسکیل‌ها، `tools/rakaly.exe`، `reports/melted.txt`، اسنپ‌شات‌های قبلی تاریخچه.

## محدودیت‌های صادقانه (برای مرحلهٔ بعد)

- شمارش opinionها برای «اعتماد به رعیت» هنوز روی ۱۳٬۸۴۶ کاراکترِ `living` سربار دارد؛
  فعلاً فقط نظرهای بازیکن خروجی می‌شوند. اگر وزیر دیپلماسی به opinion بین دو رعیت
  نیاز داشت، باید فیلتر بر اساس ست هدف تعریف شود — نه پویش کامل.
- سطح ساختمان برای اسلات‌های خالی و holdingهای بدون نوع، None است (داده در سیو نیست).
- رکوردهای MAA بازیکن (`armies.regiments` با owner) جدا از «ارتش جمع‌شده» هستند —
  در صلح، رکورد هست ولی ارتش 0 است؛ این دو نباید در تحلیل یکی شوند.

## READY FOR HUMAN VERIFY
