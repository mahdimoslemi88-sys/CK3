# پرامپت آماده — استخراج دقیق دانش CK3 توسط Gemini

این متن را **کپی کن** و مستقیم به Gemini (در آنتی‌گراویتی، پروژهٔ vizier-counsel) بده.
خروجی‌اش را در فایل `docs/CK3_STRATEGY_GUIDE.md` بچسبان یا به من بده تا خودم ترکیب کنم.

> **نکتهٔ هماهنگی (به‌روزرسانی بعد از بازطراحی استخراج سیو):** دانشwiki این پرامپت
> مکمل دادهٔ وضعیت است، نه جایگزین آن. دادهٔ واقعی حالت بازی از فایل
> `reports/state_report.json` خوانده می‌شود (قراردادش پایین آمده). فیلدهای تختِ
> گزارش قدیمی (`balance`، `domain_titles`، `war_record`، `claims_pressed`، …)
> منسوخ شده‌اند و نباید در اسکیل‌ها یا تحلیل‌ها استفاده شوند.

---

## قرارداد دادهٔ وضعیت — `reports/state_report.json`

تولید: `python extract_save.py extract` — سیو فقط خوانده می‌شود؛ کل فرآیند (melt → parse →
استخراج) در **یک** اجرا انجام می‌شود و دو خروجی می‌دهد:
`reports/state_report.txt` (گزارش فارسی خوانا، شامل بخش‌های مرحلهٔ ۲ تا ۴) و
`reports/state_report.json` (منبع حقیقت ماشینی‌خوان). هر تحلیل‌گری باید JSON را مبنا بگیرد.

### بخش‌های سیزده‌گانهٔ JSON (تأییدشده روی خروجی واقعی)

| بخش | محتوای کلیدی |
|---|---|
| `meta` | `game_date`، `save_file`، `traits_lookup` (لیست ID→کلید صفت؛ اندیس = trait ID) |
| `quality` | `counts` (۱۴ شمارندهٔ رسمی)، `sources` (مسیر سیوِ هر بخش)، `missing_fields`، `warnings`، `unmapped_ids`، `extraction_time`، `save_file_name` |
| `player` | `id/name/age/alive`، `skills[6]`، `traits[]`، `gold/income/prestige/piety`، `stress/health/fertility/dread/tyranny`، `legitimacy`، `domain_limit`، `vassal_power_value`، `realm_capital`، `government/laws`، `family{primary_spouse,spouses,children,former_spouses}`، `heir_raw` |
| `domain` | آرایهٔ عناوین `landed_data.domain` با `title_id/key/tier/holder`، `is_county`، `is_domain`، `mapped` |
| `counties` | همهٔ شهرستان‌های `county_manager` (۲۶۵۲ مورد): `county_key/development/development_progress/county_control/culture/faith/capital/de_jure_liege` |
| `holdings` | فقط استان‌های دامِین: `province_id/county_key/holding_type/holding_owner/income/levy/garrison/fort_level/winter_severity` + `buildings[]` + `constructions[]` |
| `vassals` | قراردادهای رعیت: `contract_id/vassal/liege/contract_group/levels_raw/war_with_liege` |
| `factions` | فکتون‌های فعال: `type/target/leader/power/power_threshold/power_over_threshold/discontent/members[]/war` |
| `wars` | **فقط جنگ‌های فعال** (بلوک `active_wars` داخل بخش `wars` سیو): `casus_belli/cb_attacker/cb_defender/cb_claimant/start_date`، طرفین با `participants[]/ticking_war_score`، `battles[]`، `war_score_sum` |
| `military` | `levy/current_strength/total_strength`، `regiments[]` (من‌ات‌آرمز: `type/size/max`)، `knights[]` (شناسه‌های واقعی)، `commanders[]` |
| `court` | `council_tasks[]`، `court_positions[]`، `decisions` (فلگ‌های خام bool) |
| `succession` | `laws[]/gender_law`، `succession_line[]` (خط جانشینی ذخیره‌شدهٔ خود بازی)، `first_in_line{id,name}`، `algorithm_recomputed` (همیشه false — الگوریتم بازمحاسبه نشده) |
| `characters` | شخصیت‌های مپ‌شده (player + خانواده + رهبران فکتون + …): همان شکل player |

### فیلدهای منسوخ گزارش تخت قدیمی → جایگزین JSON

| قدیمی (استفاده ممنوع) | جایگزین |
|---|---|
| `balance` | `player.gold` |
| `monthly_income` | `player.income` |
| `domain_titles` | `domain[]` + `quality.counts.domain_count` (فقط شهرستان‌های واقعی `c_`) |
| `vassal_power_value` (به‌عنوان فیلد تخت) | `player.vassal_power_value` |
| `legitimacy` (به‌عنوان فیلد تخت) | `player.legitimacy` |
| `war_record` | `wars[]` (فعال‌ها؛ شمارنده‌های تاریخچهٔ `alive_data.wars` عمداً جنگ حساب نمی‌شوند) |
| `claims_pressed` | `wars[].casus_belli` + `wars[].cb_claimant` |
| لیست فکتون متنِ آزاد | `factions[]` با `power_over_threshold` |
| خط جانشینی متنِ آزاد | `succession.succession_line` + `succession.first_in_line` |
| شورید/court متنِ آزاد | `court.council_tasks` / `court.court_positions` / `court.decisions` |
| شوالیه‌ها/من‌ات‌آرمز متنِ آزاد | `military.knights` / `military.regiments` |
| نام صفات به‌صورت متن | `characters[].traits` (ID) + `meta.traits_lookup` |

### قواعد دادهٔ صادق (غیرقابل‌مذاکره)

1. **null ≠ صفر.** هر فیلد `null` یا غایب یعنی «در سیو ذخیره نشده». نمونه‌های واقعی این
   فرمت: `player.faith` روی بلوک بازیکن ذخیره نمی‌شود؛ `levy/garrison/fort_level` برخی
   استان‌ها؛ `war_score_sum` وقتی نبردی ثبت نشده. مقدار نمی‌سازیم.
2. قبل از قضاوت `quality.missing_fields`، `quality.warnings` و `quality.unmapped_ids` را
   بخوان. اگر تحلیل به فیلد گم‌شده وابسته است، صریح بگو «قابل ارزیابی نیست».
3. دادهٔ کلاسه‌بندی‌نشده: سطح buildingها `unknown` است (در سیو ذخیره نمی‌شود)؛
   `vassals[].levels_raw` اندیس خام است (نگاشت بازی‌داده موجود نیست)؛
   `court.decisions` فلگ خام است — `false` هرگز «در دسترس» تفسیر نمی‌شود؛
   `military.rally_points = "unavailable"` یعنی داده‌ای در سیو نیست.
4. اعدادِ جمعی را از `quality.counts` بیاور (`domain_count`، `active_wars`، `factions`،
   `knights`، …)؛ دستی بازنشمار و عدد دیگری ادعا نکن.
5. منشأ داده در `quality.sources` ثبت است (هر بخش از کجای سیو آمده)؛
   `quality.save_file_name` و `quality.extraction_time` هم برای ردیابی هستند.

---

پرامپت:

```
تو یک کارشناس ارشد Crusader Kings 3 (نسخهٔ 1.17) هستی. وظیفهٔ تو این است که دانش دقیق و
مستند بازی را استخراج کنی تا یک «وزیر بزرگ» (مشاور هوشمند درون‌بازی) بتواند توصیه‌های
دقیق و قابل‌اجرا بدهد.

منابع معتبر (اگر در دسترس‌اند باز کن، وگرنه از دانش خودت استفاده کن و هر جا مطمئن نیستی
برچسب «(نامطمئن)» بزن):
- https://ck3.paradoxwikis.com/Resources
- https://ck3.paradoxwikis.com/Economy
- https://ck3.paradoxwikis.com/Army
- https://ck3.paradoxwikis.com/Men-at-arms
- https://ck3.paradoxwikis.com/Casus_belli
- https://ck3.paradoxwikis.com/Succession
- https://ck3.paradoxwikis.com/Domain
- https://ck3.paradoxwikis.com/Vassal
- https://ck3.paradoxwikis.com/Faction
- https://ck3.paradoxwikis.com/Tyranny
- https://ck3.paradoxwikis.com/Lifestyle
- https://ck3.paradoxwikis.com/Diplomacy
- https://ck3.paradoxwikis.com/Marriage

خروجی را به فارسی و در قالب ۸ فصل زیر برگردان. اعداد و مقادیر دقیق را حتماً حفظ کن:

۱) اقتصاد و پول: منابع اصلی درآمد (قلمرو مستقیم، رعایا، تجارت، یک‌باره‌ها)، بهترین ساختمان‌ها
   برای هر مرحله (اقتصادی سطح ۱ و …)، ترتیب خروج از بدهی، نقش کشورداری و دیوان (Steward روی
   Increase Development).

۲) سپاه و جنگ: ترکیب بهینهٔ Men-at-Arms برای هر مرحله، تعداد سرباز هر نوع واحد
   (سوارهٔ سنگین ۵۰، سنگ‌انداز محاصره ۱۰، …)، نقش Levies در برابر Men-at-Arms، محاصره در
   برابر نبرد، مدیریت ارتش پس از جنگ (مرخص کردن مزدوران).

۳) حقِ جنگ (Casus belli): انواع مهم (ادعا، فتح درست، de jure و …)، هزینهٔ دقیق پرستیژ/تقوا
   (معمولاً ۲۵ تا ۳۰۰)، شرایط استفاده، بهترین راه‌های به‌دست آوردن ادعا.

۴) جانشینی و قلمرو: قوانین (Confederate Partition / Partition / Primogeniture)، چرا و چگونه
   قلمرو پراکنده می‌شود، راه‌های جلوگیری (قانون بالاتر، ایجاد عنوانِ بالاتر، تقسیم عمدی،
   کاهش وارثان)، سقف قلمرو (Domain limit) و روش‌های افزایشش.

۵) رعایا و فکتون: چرا رعایا به فکتون می‌پیوندند (نظر/opinion، ظلم/tyranny، فرصت)، روش‌های
   جلوگیری (هدیه، Sway، ازدواج، ضعیف نگه داشتن رعایا، گرفتنِ عنوان با دلیل قانونی).

۶) دیپلماسی / ازدواج / اتحاد: استفادهٔ استراتژیک از ازدواج و فرزندان (اتحاد، ادعا، تولید
   وارث)، ایجاد و حفظ اتحاد، تأثیر پرستیژ/تقوا بر مذاکرات.

۷) لایف‌استایل / استرس / پرک: بهترین تمرکز برای هر مهارت (Stewardship برای پول، Diplomacy
   برای روابط، Martial برای جنگ)، کاهش استرس و الگوهای مقابله، بازنشانی پرک (۱۰۰ استرس).

۸) اولویت‌بندی وزیر: یک جدول تصمیم‌گیری عددی که بر اساس مقادیر واقعی حالت از
   reports/state_report.json — player.gold و player.income (بدهی/درآمد)،
   player.vassal_power_value در برابر military.total_strength (نسبت قدرت رعایا)،
   len(player.family.children) و succession.succession_line (تعداد وارثان)،
   player.domain_limit و quality.counts.domain_count (سقف قلمرو)، player.age و
   player.health (سن/سلامت) — اولین اقدامِ پیشنهادی را مشخص کند. هر ردیف جدول باید مسیر
   JSON خودش را ذکر کند؛ اگر فیلد null یا غایب بود (مثلاً player.faith در این فرمت سیو
   ذخیره نمی‌شود)، آن ردیف را «قابل ارزیابی نیست» علامت بزن — هرگز صفر فرض نکن.

در انتها یک بخش «منابع» بگذار که بگویی هر عدد از کدام منبع آمده و اگر چیزی بین منابع
مغایرت داشت یا مربوط به نسخهٔ 1.17 نبود، صریح بنویس. اعدادِ وضعیتِ زنده فقط از
reports/state_report.json مجازند (و بلوک quality آن را همراه بیاور)، نه از حدس.
```

---

## بعد از برگشتن خروجی
1. خروجی را به‌عنوان جایگزین/الحاق در `docs/CK3_STRATEGY_GUIDE.md` بچسبان.
2. به من خبر بده تا اسکیل‌های `.agents/skills/` (که همین حالا مستقیم از
   `reports/state_report.json` می‌خوانند) با محتوای دقیق‌تر هماهنگ شوند —
   مخصوصاً «جدول تصمیم‌گیری عددی» فصل ۸ که مسیرهای JSON را ذکر می‌کند.
