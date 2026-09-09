---
name: ck3-realm-analysis
description: |
  تحلیل کلی وضعیت قلمرو بازیکن در Crusader Kings 3 بر اساس خروجی ساختاریافتهٔ جدید
  (reports/state_report.json). از این اسکیل استفاده کن وقتی بازیکن می‌خواهد بداند
  ضعف اصلی قلمروش کجاست و کدام شاخه (اقتصاد، سپاه، دیپلماسی، قلمرو/رعایا، جانشینی)
  را باید اول تقویت کند.

  منبع داده: reports/state_report.json
  فیلدهای کلیدی:
  - player: skills، traits، gold، income، domain_limit، vassal_power_value، dread، tyranny، legitimacy
  - quality.counts: domain_count، maa_regiments، knights، factions، active_wars، characters_mapped
  - succession.first_in_line و succession.laws
  - factions[].power_over_threshold
  - quality.missing_fields / quality.warnings (داده‌های ناموجود)
license: Apache-2.0
metadata:
  version: v2
  publisher: user
---

# تحلیل وضعیت قلمرو (Realm Analysis) — نسخهٔ دادهٔ ساختاریافته

هدف این اسکیل ارزیابی اولویت‌بندی‌شدهٔ وضعیت کلی بازیکن است تا مشخص شود
ظرفیت اصلی پیشرفت و بزرگ‌ترین ریسک فعلی کدام است.

## ورودی

`reports/state_report.json` را بخوان. اگر `quality.warnings` هشداری دارد که به
سؤال مرتبط است، اول آن را شفاف گزارش کن. تحلیل را روی این بخش‌ها بساز:
`player`, `military`, `factions`, `succession`, `quality.counts`.

## ترتیب ارزیابی

ضعف‌ها را به این ترتیب بسنج (فوری‌ترین اول):

1. **وضعیت مالی**: `player.gold` منفی (بدهی) یا کمتر از ۷۵، یا `player.income`
   منفی/اندک → اقتصاد فوری‌ترین مشکل است.
2. **جنگ / امنیت**: `quality.counts.active_wars > 0` → بخش `wars` را بخوان؛
   جنگ‌هایی که `cb_attacker/cb_defender` آن‌ها `player.id` است مستقیماً به تو مربع‌اند.
   اگر `player.vassal_power_value >= military.total_strength`، خطر شورش داخلی از
   جنگ خارجی مهم‌تر است.
3. **فکشن‌ها**: `factions[]` با `power_over_threshold == true` (معیار عددی صریح:
   `power > power_threshold`) → بشمار و با نوع (`type`) گزارش کن.
4. **سقف قلمرو**: `quality.counts.domain_count > player.domain_limit` → تجاوز از
   سقف؛ جریمهٔ درآمد و رنجش رعایا.
5. **جانشینی**: `succession.first_in_line == null` یا نبود فرزند (`player.family.children`)
   → بحران جانشینی. اگر خط جانشینی (`succession.succession_line`) هست، نفر اول را
   با نام بده (خودِ JSON نام را از سیو گرفته؛ حدس نزن).
6. **ظرفیت رشد**: `legitimacy` پایین → تثبیت مشروعیت؛ در غیر این صورت توسعه و ساختمان.

## خروجی پیشنهادی

- **فوری‌ترین مشکل**: (یک جمله، با عدد از JSON)
- **سه اقدام اولویت‌دار**: (سه خط عددشده)
- **نقاط قوت**: (چه چیز خوب پیش می‌رود تا روی آن بسازد)
- برای هر حوزه «اقتصاد / سپاه / دیپلماسی / قلمرو / جانشینی» یک توصیهٔ کوتاه که با
  داده‌های همان JSON سازگار باشد.

## قواعد رفتاری

- فقط تحلیل و پیشنهاد ده — هیچ فایلی را باز نکن، تغییر نده و دستوری اجرا نکن.
- اگر داده‌ای در JSON نیست یا `null` است (مثلاً `player.faith` در این فرمت سیو ذخیره
  نمی‌شود)، حدس نزن؛ نبودش را صریح بگو و به‌جایش راهنمای کلی بده.
- با توجه به مهارت‌های بازیکن (`player.skills` — ترتیب: دیپلماسی، سپاه، کشورداری،
  دسیسه، دانش، قوت) توصیه را متناسب کن.
