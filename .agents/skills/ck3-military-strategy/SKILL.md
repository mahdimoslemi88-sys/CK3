---
name: ck3-military-strategy
description: |
  راهبرد سپاه و جنگ در Crusader Kings 3 بر اساس خروجی ساختاریافتهٔ جدید:
  ترکیب لشکر، خواندن جنگ‌های فعال، و انتخاب هدف حمله. از این اسکیل استفاده کن
  وقتی بازیکن در جنگ است، می‌خواهد حمله کند، یا وضعیت نظامی‌اش را می‌خواهد بداند.

  منبع داده: reports/state_report.json
  فیلدهای کلیدی:
  - military: current_strength / total_strength / levy / regiments[] / knights[]
  - wars[]: war_id / casus_belli / cb_attacker / cb_defender / start_date /
    attacker.ticking_war_score / defender.ticking_war_score / battles[] / war_score_sum
  - quality.counts.active_wars
  - player.id، player.vassal_power_value
license: Apache-2.0
metadata:
  version: v2
  publisher: user
---

# راهبرد سپاه و جنگ (Military Strategy) — نسخهٔ دادهٔ ساختاریافته

هدف این اسکیل تبدیل دادهٔ نظامی به توصیهٔ عملی است.
ورودی: `reports/state_report.json` (بخش‌های `military`, `wars`, `player`, `quality.counts`).

## ۱) ارزیابی قدرت

- `military.total_strength` و `military.current_strength` را با هم بخوان: فاصلهٔ
  زیاد یعنی ارتش جمع‌نشده یا تلفات — قبل از هر حمله‌ای توصیه به تجدید لشکر کن.
- `military.regiments[]` = من‌ات‌آرمز خودت؛ هر regiment با `type` و `size` و `max`
  آمده (`max == null` یعنی سقف در سیو ذخیره نشده — حدس نزن). ترکیب نوع‌ها را توصیف
  کن و کمبود نوع (پیاده، سواره، محاصره) را بگو.
- `military.knights` = شناسه‌های واقعی شوالیه‌ها؛ شمارش = طول همین list.
  اگر `player.vassal_power_value >= military.total_strength`، ریسک داخلی را قبل
  از هر ماجراجویی خارجی هشدار بده.

## ۲) جنگ‌های فعال را از جنگ‌های تاریخچه جدا کن

- `wars[]` فقط از بلوک `active_wars` داخل بخش `wars` در فایل سیو استخراج شده — شمارنده‌های تاریخچهٔ جنگ
  شخصیت‌ها عمداً به‌عنوان جنگ گزارش نمی‌شوند. پس هر ورودی این لیست جنگ زندهٔ امروزی است.
- جنگ‌های مربوط به بازیکن: `cb_attacker == player.id` یا `cb_defender == player.id`.
  اگر هیچ‌کدام نبود، صریح بگو «در هیچ جنگ فعالی مستقیماً طرف نیستی» و جنگ‌های همسایگان
  را فقط به‌عنوان فرصت/خطر جانبی تحلیل کن.
- امتیاز جنگ را فقط از دادهٔ قابل اثبات بخوان: `attacker.ticking_war_score`،
  `defender.ticking_war_score` و `war_score_sum` (مجموع امتیاز نبردهای ثبت‌شده).
  `war_score_sum == null` یعنی نبردی ثبت نشده — نگو «در حال باخت/برد»، بگو «دادهٔ
  نبردی موجود نیست».
- `battles[].province` و `attacker_won` را برای روند آخرین نبردها استفاده کن.

## ۳) انتخاب هدف حمله

- ادعاها (`claims`) در این خروجی قابل اثبات نیستند — اگر در گزارش چیزی نیست، نگو
  «فلان‌کس را بزن»؛ معیار انتخاب هدف را بگو (هدف ضعیف‌تر، ادعای معتبر، فاصله و سرزمین).
- کستِ جنگ (`casus_belli`) هر جنگ فعال در `wars[].casus_belli` آمده — نوع آن را در
  تحلیل بیاور (مثلاً peasant_war).

## قواعد رفتاری

- از اعداد واقعی JSON استفاده کن، نه تخمین.
- هر جا دادهٔ نظامی گم‌شده بود (مثلاً `max` یک regiment)، محدودیت را صریح بگو.
- فقط مشاوره ده — هیچ فایلی را باز یا تغییر نده.
