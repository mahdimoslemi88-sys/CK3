---
name: ck3-data-steward
description: |
  نگهبان داده — پس از هر استخراج، سلامت `reports/state_report.json` و اسنپ‌شات‌های
  `reports/history/` را کنترل می‌کند: مسیرهای JSON که اسکیل‌ها به آن‌ها تکیه دارند،
  سازگاری داخلی شمارنده‌ها، افت کیفیت نسبت به اسنپ‌شات قبلی، و تغییر نسخهٔ بازی.
  این اسکیل مالک قرارداد «اسکیل ↔ JSON» است؛ اگر مسیری دیگر resolve نشود، اولین
  کسی است که زنگ می‌زند.

  منبع داده: reports/state_report.json + reports/history/snapshot_*.json
license: Apache-2.0
metadata:
  version: v2
  publisher: user
---

# نگهبان داده (Data Steward)

## چک‌لیست اجباری بعد از هر استخراج

### ۱. سلامت schema و قرارداد مسیرها
- ساختار ۱۳‌بخشی موجود است؟ `meta, quality, player, domain, counties, holdings,
  characters, vassals, factions, succession, wars, military, court`
- مسیرهای حیاتی که اسکیل‌ها به آن‌ها تکیه دارند resolve می‌شوند؟ دست‌کم:
  `quality.counts.domain_count`، `player.domain_limit`، `player.vassal_power_value`،
  `player.resources.gold`، `quality.counts.counties_world`، `quality.counts.development_world_avg`،
  `player.legitimacy`، `player.family.children`، `succession.first_in_line`،
  `succession.algorithm_recomputed`، `military.regiments`، `military.knights`،
  `court.decisions`، `meta.traits_lookup`
- `meta.traits_lookup` غیرخالی است؟ (بدون آن، نام صفات قابل حل نیست)

### ۲. سازگاری داخلی (عدد در برابر عدد)
- `quality.counts.domain_count == تعداد domain[] با is_county==true و is_domain==true`
- `quality.counts.active_wars == len(wars[])`
- `quality.counts.factions == len(factions[])`، `counts.knights == len(military.knights)`
- `quality.counts.characters_mapped + characters_unmapped == len(characters[])`
- `quality.counts.counties == len(counties[])` و `counties_world >= counties`
  (از نسخهٔ فیلترشده، `counties[]` فقط دامنهٔ بازیکن است و آمار دنیا در counts می‌ماند؛
  در اسنپ‌شات‌های قدیمی counties == counties_world — این تفاوت، تغییر نسخه است نه افت کیفیت)
- `player.resources` موجود است؟ `resources.gold == player.gold` باید یکسان باشند
  (دو نمای یکسان از همان سیو)؛ تقوا/شکوه با currency مطابقت دارند
- هر ناسازگاری = نقص در استخراج؛ گزارش کن، تصحیح نکن، حدس نزن.

### ۳. افت کیفیت نسبت به اسنپ‌شات قبلی
- `quality.counts.characters_unmapped` از صفر بزرگ‌تر شده؟
- `quality.missing_fields` تازه چه چیزی دارد؟ (فیلد تازه‌گم‌شده = احتمال تغییر ساختار سیو)
- `quality.warnings` جدید؟
- اگر `reports/history/` قبلی موجود است مقایسه کن؛ نبودِ تاریخچه را «اولین اسنپ‌شات»
  گزارش کن، نه خطا.

### ۴. نسخهٔ بازی و تازگی داده
- `quality.save_file_name` و `quality.extraction_time` را بخوان؛ اگر بازیکن از سیوی حرف
  می‌زند که با این‌ها نمی‌خواند، قبل از هر تحلیلی re-extract را پیشنهاد بده.
- شکل‌های عجیب (`"none"` رشته‌ای به‌جای حذف، تاریخ خالی) = علامت نسخهٔ متفاوت سیو.

## گزارش خروجی

| سطح | معنی |
|---|---|
| ✅ سالم | همهٔ چک‌ها سبز — تحلیل‌گران آزادند کار کنند |
| ⚠️ هشدار | افت کیفیت یا ناسازگاری جزئی — تحلیل با ذکر محدودیت ادامه یابد |
| 🔴 خراب | ساختار یا مسیر حیاتی شکسته — هیچ تحلیلی روی این خروجی انجام نشود؛ اول تعمیر استخراج |

این اسکیل فقط تشخیص می‌دهد؛ هرگز فایل خروجی را دستکاری نمی‌کند و مقداری نمی‌سازد.
