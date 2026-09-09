# مرحلهٔ ۵ از بازطراحی استخراج سیو CK3 — دسیسه، روابط، دودمان و اشیاء

این سند، پرامپت آمادهٔ مرحلهٔ ۵ است. متنِ داخل بلوک کد را مستقیم به ایجنت بده.
همهٔ مسیرها و اعداد پایین **روی `reports/melted.txt` واقعی (سیو ۹۴۵/۱/۱، ۱۹۹٫۷ مگابایت،
۲۰٬۳۸۸ بلوک ریشه، parse کامل تا EOF) تأیید ساختاری شده‌اند** — ایجنت لازم نیست دوباره
از صفر کاوش کند؛ فقط verify سریع + پیاده‌سازی.

پیش‌شرط: مراحل ۱ تا ۴ با VERIFY: PASS تأیید شده‌اند؛ فاز ۱ (اسنپ‌شات + تحلیل‌گر روند +
نگهبان داده) هم پیاده‌سازی شده است. تست‌ها: `python -m pytest tests/ -q` ← ۸۲ پاس.

```
# مرحلهٔ ۵ — دسیسه، روابط، دودمان و اشیاء (فقط استخراج ساختاری)

## قوانین اجباری (همان قرارداد مراحل ۲ تا ۴)

1. قبل از هر تغییر، پلن شماره‌دار بنویس (ابزار sequentialthinking نصب نیست؛
   با write_todos پلن را ثبت کن و در طول کار به‌روز نگه دار).
2. قبل از پیاده‌سازی، با Parser مرحلهٔ ۱ ساختارهای واقعی melted.txt را verify کن
   (مسیرهای پایین همه تأییدشده‌اند).
3. هیچ Regex سراسری و هیچ text.find اولین‌تطابق ممنوع؛ همه‌چیز از مسیر ساختاری.
4. فایل ۱۹۹ مگابایتی در هر اجرا فقط یک بار parse شود.
5. فقط Scope این مرحله را تغییر بده؛ AGENTS.md را رعایت کن (سیو فقط خوانده شود،
   گزارش فقط در reports/، Commit/Push ممنوع، تغییرات قبلی کاربر حفظ شود).
6. پس از تست کامل، با گزارش شواهد و READY FOR HUMAN VERIFY متوقف شو.
7. تا VERIFY: PASS مرحلهٔ بعدی را شروع نکن.

## داده‌های تأییدشده (سیو واقعی ۹۴۵/۱/۱)

### الف) دسیسه‌ها — root.schemes.active
- ۱۴۸۶ دسیسهٔ فعال. فیلدهای هر بلوک:
  type="murder"/"sway"/...، status، owner، target{type,target}، progress،
  opportunities، agent_slots[] (با character/contribution/type)، secrecy،
  scheme_exposed، date، ramping_success_chance
- دسیسه‌های بدون فیلد type: ۵۲ مورد — باید به‌عنوان missing گزارش شوند، نه حذف.
- ۴۲۹۴۹۶۷۲۹۵ = شناسهٔ خالیِ اسلات (sentinel) — هرگز به‌عنوان character ID مصرف نشود.
- برای گزارش نهایی: فقط دسیسه‌هایی که owner یا target یا agent آن‌ها بازیکن یا
  اعضای خانواده است جزئیات کامل می‌گیرند؛ بقیه فقط شمارش نوع‌بندی‌شده.

### ب) رازها — root.secrets
- secrets.secrets: ۳۶۲۹ راز با type/owner/target/participants؛
  انواع واقعی: secret_non_believer 1204، secret_deviant 578، secret_lover 539، ...
- secrets.known_secrets: ۵۶۲۰ ورودی؛ children این نود «لیست» است نه dict —
  مثل همان درسی که vassal_contracts یاد گرفتیم، flatten لیستی صحیح انجام شود.

### ج) روابط و اتحاد — root.relations.active_relations
- ۱۸۰۱۷ ورودی با شکل: first، second، alliances[] (allied_through_0/1) و
  active_hook_1{type,expiration_date} — اتحاد و اوراق فشار در همین جدولند.
- اتحادِ مرتبط با بازیکن = ورودی‌ای که first یا second آن بازیکن/خانواده است.
- expiration_date=9999.1.1 یعنی بدون انقضا — نه «منقضی‌شده».

### د) دودمان — root.dynasties
- dynasties.dynasties: ۱۶۰۶۸ دودمان؛ از این تعداد: ۱۰۱۲۱ با شکوه (prestige.
  currency/accumulated)، ۹۵۹ با perkهای legacy، ۶۸۷۶ با dynasty_head.
- dynasties.dynasty_house: ۱۶۶۳۲ خانه با name/dynasty/motto.
- این جدول کل بازی است؛ برای خروجی فقط دودمان بازیکن و دودمان‌های مرتبط
  (بازیکن، خانواده، همسران، رؤسای فکتون) کامل گزارش شود؛ بقیه فقط شمارش.
- درختی از همهٔ اعضا در سیو نیست — هیچ ساختار درختی اختراع نشود.

### هـ) اشیاء — root.artifacts.artifacts
- ۴۳۱۰ شیء با name (متن رمزگذاری‌شدهٔ خاص — دستکاری نشود)، type، rarity،
  durability/max_durability، history.entries[] (با recipient).
- inventory شخصیت: داخل بلوک خود شخصیت است (owner/equipped/artifacts).
- نکتهٔ صادقانهٔ مهم: بلوک شخصیتِ بازیکنِ فعلی هیچ‌یک از این فیلدها را ندارد —
  این یعنی در این سیو برای بازیکن قابل استخراج نیست و باید missing گزارش شود،
  نه اینکه از جدول عمومی برایش چیزی ساخته شود.

### و) لایف‌استایل و پرک شخصیت‌ها
- lifestyle_xp در بلوک شخصیت‌های دیگر دیده می‌شود (مثلاً learning_lifestyle=150)؛
  برای بازیکن هم اگر در سیو ذخیره شده باشد استخراج می‌شود، اگر نبود missing.
- پرک‌های legacy در جدول دودمان است (فیلد perk) — نه در بلوک شخصیت.

## Scope مجاز

- extract_save.py (توابع جدید extract_schemes/secrets/relations/dynasty/artifacts
  + گسترش _character_summary برای lifestyle_xp)
- تست‌های جدید (tests/test_intrigue_diplomacy_extract.py یا مشابه)
- fixtureهای مصنوعی کوچک
- گزارش: بخش جدید جدا در state_report.txt + به‌روزرسانی build_state_json با
  بخش‌های schemes/secrets/relations/dynasties/artifacts
- به‌روزرسانی اسنپ‌شات (save_state_snapshot) خودکار است — ساختار JSON جدید را هم می‌گیرد.

## خروجی JSON

- schemes[]: فقط موارد مرتبط با بازیکن/خانواده (کامل) + quality.counts.schemes_total
- secrets[]: فقط رازهایی که owner یا participants بازیکن/خانواده‌اند؛ count کل در counts
- relations[]: اتحادهای بازیکن/خانواده با allied_through و اوراق فشار فعال
- dynasties: دودمان بازیکن (شکوه، head، perkها) + خلاصهٔ آماری کل
- artifacts[]: اشیاءِ همان شده به بازیکن/خانواده از طریق inventory + equipped slots
- quality.counts: schemes_total, schemes_missing_type, secrets_total, relations_total,
  dynasties_total, artifacts_total
- هیچ بخش جدیدی نباید موجب دوبرابر شدن حجم state_report.json شود —
  فیلتر مربوط به بازیکن/خانواده الزامی است.

## تست‌های اجباری (fixture مصنوعی)

1. دسیسهٔ کامل با agent_slots و sentinel ۴۲۹۴۹۶۷۲۹۵ (نباید مپ شود)
2. دسیسهٔ بدون type ← missing، نه حذف
3. راز با participants و known_secrets لیستی
4. اتحاد first/second + hook با انقضای واقعی در برابر 9999.1.1
5. دودمان با/بدون prestige و perk و dynasty_head
6. artifact با durability و history.entries
7. inventory شخصیت با equipped و artifacts
8. شخصیت بدون lifestyle_xp ← missing
9. فیلتر بازیکن/خانواده (هیچ فکشن/دسیسهٔ بی‌ربط جزئیات کامل نگیرد)
10. شمارنده‌های quality.counts سازگار با محتوا

سپس اجرای واقعی روی melted.txt و ثبت: تعداد کل، تعداد مرتبط با بازیکن،
تعداد missing، حجم JSON قبل/بعد.

## معیار پذیرش

- همهٔ داده‌ها فقط از مسیر ساختاری؛ بدون Regex سراسری/text.find
- sentinel 4294967295 هیچ‌وقت ID نیست؛ 9999.1.1 هرگز «منقضی» نیست
- missing = missing؛ هیچ مقداری ساخته نشود
- تست‌های قبلی (۸۲) سبز بمانند + تست‌های جدید سبز
- گزارش legacy و بخش‌های مرحله‌های ۲ تا ۴ دست‌نخورده (فقط الحاق)
- حجم JSON بیش از ~۲× نشود

## گزارش پایانی

- file:line هر تابع استخراج جدید
- فرمان تست + Exit Code + تفکیک تعداد تست‌ها
- آمار اجرای واقعی (فوق) + حجم JSON قبل/بعد
- فهرست صادقانهٔ چیزهایی که قابل استخراج نیستند
- به‌روزرسانی skills (دسیسه/دیپلماسی/سلسله) که فیلدهای جدید را مصرف کنند — بعد از VERIFY.

READY FOR HUMAN VERIFY
```
