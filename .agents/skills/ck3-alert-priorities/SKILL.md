---
name: ck3-alert-priorities
description: |
  قواعد تشخیص وضعیت بحرانی در Crusader Kings 3 و اولویت‌بندی هشدارها بر اساس
  خروجی ساختاریافتهٔ جدید (reports/state_report.json).
  از این اسکیل استفاده کن تا قبل از هر توصیهٔ بلندمدت، خطرهای فوری را شناسایی و
  در صدر پاسخ بیاوری. این اسکیل بدنهٔ همهٔ اسکیل‌های راهبردی دیگر را با یک
  سلسله‌مراتب هشدار تکمیل می‌کند.

  منبع داده: reports/state_report.json (خروجی استخراج سیو — نسخهٔ جدید)
  فیلدهای کلیدی:
  - player.gold / player.income / player.stress / player.health / player.age
  - quality.counts.active_wars
  - player.vassal_power_value و military.total_strength
  - quality.counts.domain_count در برابر player.domain_limit
  - succession.first_in_line و player.family.children
  - quality.missing_fields / quality.unmapped_ids / quality.warnings
license: Apache-2.0
metadata:
  version: v2
  publisher: user
---

# اولویت‌بندی هشدارها (Alert Priorities) — نسخهٔ دادهٔ ساختاریافته

این اسکیل یک «پردازشگر وقایع» است: قبل از هر چیز، `reports/state_report.json` را
از نظر این فلگ‌ها اسکن کن و هرکدام فعال بود، آن خطر را در **صدر** پاسخ بیاور،
بدون توجه به موضوع اصلی سؤال.

## سلسله‌مراتب (از فوری به کمتر فوری)

| # | شرط (مسیر JSON) | زنگ خطر |
|---|------|---------|
| 1 | `player.gold < 0` | بدهی — بحران مالی آنی |
| 2 | `quality.counts.active_wars > 0` | در جنگ — بخش `wars` را بخوان؛ جنگ‌های `wars[].cb_attacker/cb_defender == player.id` مهم‌ترند |
| 3 | `player.vassal_power_value >= military.total_strength` | رعایا از لشکر تو قوی‌ترند — خطر شورش |
| 4 | `player.family.children == []` و `succession.first_in_line == null` | وارثی در کار نیست — خطر سقوط سلسله |
| 5 | `quality.counts.domain_count > player.domain_limit` | تجاوز از سقف قلمرو — جریمهٔ درآمد |
| 6 | `player.income < 0` | درآمد منفی — به سمت بدهی |
| 7 | `player.age` بالا (≥ ۵۰) و `player.health` پایین (≤ ۲) | خطر مرگ و بحران جانشینی قریب‌الوقوع |
| 8 | `player.stress >= 90` | استرس بحرانی — خطر فروپاشی روانی |
| 9 | `factions[]` با `power_over_threshold == true` | فکشن(های) فعال بالاتر از حد آستانه — شمارش را گزارش کن |

## قاعدهٔ حیاتی: دادهٔ گم‌شده چیزِ ساختگی جایش نمی‌شود

- هر فیلدی که در JSON نیست یا `null` است، یعنی «در سیو موجود نیست» — نه صفر و نه بد.
  مثال‌های واقعی این ذخیره: `player.faith` روی بلوک بازیکن ذخیره نمی‌شود؛
  `player.income/stress/health` زودتر از `null` را با صفر اشتباه نگیر.
- قبل از قضاوت، `quality.missing_fields` و `quality.warnings` را بخوان و اگر تحلیل
  تو به فیلدی گم‌شده وابسته است، صریح بگو «قابل ارزیابی نیست».
- `quality.unmapped_ids` بزرگ ≠ خرابی؛ یعنی آن IDها در `living/dead_unprunable` نبودند.

## قواعد استفاده

1. همهٔ فلگ‌ها را در یک بار اسکن کن؛ اگر چندتایی هم‌زمان بود، بالاترین ردیفِ جدول
   «فوری‌ترین مشکل» است و بقیه بعد از آن.
2. برای هر خطرِ فعال یک راه آشکار و عملی بده (نه فقط «مراقب باش»).
3. اگر هیچ فلگی فعال نبود، «وضعیت باثبات» را اعلام کن و روی اسکیل‌های رشد تمرکز کن.
4. این اسکیل را **همیشه** اول اعمال کن؛ بعدش سراغ اسکیلِ موضوع سؤال برو.

## قواعد رفتاری

- اگر دادهٔ لازم برای یک فلگ در JSON نیست، آن ردیف را نادیده بگیر و حدس نزن.
- اعداد را از JSON بیاور و در پاسخ به کار ببر («۳ فکشن از ۲۲۰ بالای حد آستانه‌اند»).
- فقط مشاوره ده — هیچ فایلی را باز یا تغییر نده.
