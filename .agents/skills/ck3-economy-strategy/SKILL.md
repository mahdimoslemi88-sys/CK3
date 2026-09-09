---
name: ck3-economy-strategy
description: |
  مدیریت اقتصادی قلمرو در Crusader Kings 3 بر اساس خروجی ساختاریافتهٔ جدید:
  خروج از بدهی، افزایش درآمد پایدار، و تصمیم‌گیری دربارهٔ ساختمان‌ها.
  از این اسکیل استفاده کن وقتی بازیکن بدهکار است، درآمدش کم است، یا می‌خواهد
  بهترین جهت سرمایه‌گذاری در قلمرو مستقیم را بداند.

  منبع داده: reports/state_report.json
  فیلدهای کلیدی:
  - player.gold (طلا/بدهی) و player.income (درآمد ماهانه)
  - domain[] (عنوان‌های قلمرو — key/tier/name/is_county)
  - holdings[] (استان‌های قلمرو: holding_type، income، levy، garrison، buildings[]، constructions[])
  - counties[] (توسعه: development، county_control، culture، faith)
  - player.skills[2] (کشورداری) و quality.counts.domain_count / player.domain_limit
license: Apache-2.0
metadata:
  version: v2
  publisher: user
---

# راهبرد اقتصاد (Economy Strategy) — نسخهٔ دادهٔ ساختاریافته

هدف این اسکیل هدایت بازیکن به سمت ثبات مالی و سپس رشد است.
ورودی: `reports/state_report.json` (بخش‌های `player`, `domain`, `holdings`, `counties`).

## ۱) خروج از بدهی

اگر `player.gold < 0` یا `player.income` منفی است، این اولویت‌ها را به همین ترتیب بده:

1. **درآمد سریع یک‌بار**: فروش عنوان‌ها/اسیران، فدیه، ازدواج پولدار — صریح بگو «یک‌بار» است.
2. **کاهش مخارج**: مزدوران سنگین و ساخت‌وساز غیرضروری تا بهبود تعطیل.
3. **ساختمان تولیدی**: از `holdings[]` آن استان‌هایی که `constructions[]` دارند را ببین —
   اگر پروژهٔ در حال ساخت هست، تاریخ `completion_date` را بگو و توصیه کن تا اتمام
   ساخت جدید شروع نشود مگر برای رفع بدهی فوری.

## ۲) سرمایه‌گذاری هوشمند

- ساختمان‌های موجود هر holding را از `holdings[].buildings[].type` بخوان (سطح ساختمان
  در این خروجی `unknown` است — چون سیو سطح را ذخیره نمی‌کند؛ حدس نزن و روی «نوعِ
  تکرارنشده» استدلال کن).
- `holdings[].holding_type` اگر `null` بود یعنی نوع holding در سیو ذخیره نشده —
  صریح بگو و نوع ساختمان پیشنهادی را مشروط بده («اگر قلعه است…»).
- برای اولویت‌دهی شهرستان، از `counties[]` استفاده کن: `development` پایین + 
  `county_control` کامل = ظرفیت رشد؛ `county_control` ناقص = اول کنترل، بعد ساختمان.
- `county_control` کمتر از ۱۰۰ یعنی مالیات/سرباز آن شهرستان کسری دارد — قبل از
  ساختمان، کنترل را با `realm_capital` و marshall توصیه کن.
- هر ساختمان را **با نام شهرستان** پیشنهاد بده (`holdings[].county_key`)، نه کلی.

## ۳) سقف قلمرو و توسعه

- اگر `quality.counts.domain_count > player.domain_limit`: یک عنوان ضعیف را از
  `domain[]` (آن‌ها که `is_county == false` یا توسعهٔ پایین دارند) رها کن.
- `player.skills[2]` (کشورداری) بالا → سرمایه‌گذاری بزرگ‌تر مجاز؛ پایین → اول
  ساختمان‌های کم‌هزینه.

## قواعد رفتاری

- درآمد را بر حسب `player.income` بیان کن («حدود N در ماه»).
- هر عدد را از JSON بیاور؛ اگر فیلدی گم‌شده بود (`quality.missing_fields`)،
  محدودیت تحلیل را بگو، نه حدس.
- فقط پیشنهاد ده؛ هیچ فایلی را باز یا تغییر نده.
