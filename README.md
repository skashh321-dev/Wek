# Wek — WhatsApp Manager

بوت تيليجرام إداري بسيط بلغة Python لتسجيل أرقام واتساب ومتابعة البلاغات التي تحتاج مراجعة بشرية.

## المتطلبات
- Python 3.10 أو أحدث
- توكن بوت من BotFather

## التشغيل على Windows
1. فك ضغط المشروع.
2. افتح Terminal داخل مجلد `Wek`.
3. أنشئ بيئة افتراضية (اختياري لكنه مستحسن):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
4. ثبّت المكتبات:
   ```bash
   pip install -r requirements.txt
   ```
5. انسخ `.env.example` إلى ملف باسم `.env`.
6. ضع توكن البوت في `BOT_TOKEN` واترك `ADMIN_ID=8874299303`.
7. شغّل:
   ```bash
   python bot.py
   ```

## التشغيل على Android / Termux
```bash
pkg update
pkg install python
pip install -r requirements.txt
cp .env.example .env
nano .env
python bot.py
```

## الأوامر
- `/start` — القائمة الرئيسية
- `/add_account` — تسجيل رقم في قاعدة البيانات
- `/accounts` — عرض الأرقام
- `/remove_account` — حذف سجل
- `/new_report` — تسجيل بلاغ للمراجعة اليدوية
- `/reports` — عرض آخر البلاغات
- `/cancel` — إلغاء العملية

## تنبيه مهم حول واتساب
إضافة رقم داخل هذا البوت هي عملية تسجيل إدارية فقط، وليست ربطاً بجلسة واتساب أو جهاز مصاحب. ربط واتساب الفعلي يحتاج إعداد WhatsApp Business Platform / Cloud API من Meta، ولا توفر واجهة Cloud API ربط الأجهزة المصاحبة بالطريقة نفسها الموجودة في تطبيق واتساب.

هذا المشروع لا يرسل بلاغات واتساب تلقائية أو جماعية. البلاغات تُحفظ للمراجعة اليدوية، ويجب إرسالها عبر قنوات واتساب الرسمية وبناءً على مخالفات حقيقية.
