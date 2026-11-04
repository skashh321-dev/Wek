import os
import logging
import sqlite3
from datetime import datetime, timezone

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
)

load_dotenv()
BOT_TOKEN = os.getenv("8902506022:AAGPztR2xXQqM0y1cWFIPJCgZe0ytHvAwE4", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "8204739948"))
DB_PATH = os.getenv("DB_PATH", "wek.db")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
log = logging.getLogger("wek")

ADD_ACCOUNT, REMOVE_ACCOUNT, REPORT_PHONE, REPORT_DETAILS = range(4)


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'registered',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                details TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending_review',
                created_at TEXT NOT NULL
            )
        """)


def is_admin(update: Update) -> bool:
    user = update.effective_user
    return bool(user and user.id == ADMIN_ID)


async def deny(update: Update):
    if update.effective_message:
        await update.effective_message.reply_text("غير مصرح لك باستخدام هذا البوت.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await deny(update)
    await update.message.reply_text(
        "أهلاً بك في Wek — WhatsApp Manager\n\n"
        "الأوامر المتاحة:\n"
        "/add_account — تسجيل رقم في لوحة الإدارة\n"
        "/accounts — عرض الأرقام المسجلة\n"
        "/remove_account — حذف رقم مسجل\n"
        "/new_report — تسجيل بلاغ للمراجعة اليدوية\n"
        "/reports — عرض البلاغات المسجلة\n"
        "/help — المساعدة\n\n"
        "ملاحظة: تسجيل الرقم هنا لا يربطه بواتساب. ربط واتساب الفعلي يحتاج واجهة Meta الرسمية."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await deny(update)
    await start(update, context)


async def add_account_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await deny(update)
    await update.message.reply_text("أرسل اسماً تعريفياً للرقم، مثال: رقم العمل")
    return ADD_ACCOUNT


async def add_account_label(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return ConversationHandler.END
    context.user_data["account_label"] = update.message.text.strip()[:80]
    await update.message.reply_text("أرسل رقم واتساب بصيغة دولية، مثال: +201xxxxxxxxx")
    return REMOVE_ACCOUNT


async def add_account_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return ConversationHandler.END
    phone = update.message.text.strip()
    if not phone.startswith("+") or not phone[1:].isdigit() or not (8 <= len(phone[1:]) <= 15):
        await update.message.reply_text("صيغة الرقم غير صحيحة. أرسله بصيغة دولية مثل +201xxxxxxxxx")
        return REMOVE_ACCOUNT
    label = context.user_data.pop("account_label", "WhatsApp")
    try:
        with db() as conn:
            conn.execute(
                "INSERT INTO accounts(label, phone, created_at) VALUES(?,?,?)",
                (label, phone, datetime.now(timezone.utc).isoformat())
            )
        await update.message.reply_text(f"تم تسجيل {label} — {phone} في لوحة Wek.")
    except sqlite3.IntegrityError:
        await update.message.reply_text("هذا الرقم مسجل بالفعل.")
    return ConversationHandler.END


async def accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await deny(update)
    with db() as conn:
        rows = conn.execute("SELECT id,label,phone,status FROM accounts ORDER BY id").fetchall()
    if not rows:
        return await update.message.reply_text("لا توجد أرقام مسجلة حتى الآن.")
    lines = ["الأرقام المسجلة في Wek:"]
    for row in rows:
        lines.append(f"#{row['id']} | {row['label']} | {row['phone']} | {row['status']}")
    await update.message.reply_text("\n".join(lines))


async def remove_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await deny(update)
    await update.message.reply_text("أرسل رقم ID للسجل الذي تريد حذفه. استخدم /accounts لمعرفة الـ ID.")
    return REMOVE_ACCOUNT


async def remove_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return ConversationHandler.END
    try:
        account_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("أرسل رقم ID صحيحاً.")
        return REMOVE_ACCOUNT
    with db() as conn:
        cur = conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
    await update.message.reply_text("تم حذف السجل." if cur.rowcount else "لم يتم العثور على هذا السجل.")
    return ConversationHandler.END


async def new_report_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await deny(update)
    await update.message.reply_text("أرسل رقم واتساب محل البلاغ بصيغة دولية.")
    return REPORT_PHONE


async def report_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return ConversationHandler.END
    phone = update.message.text.strip()
    if not phone.startswith("+") or not phone[1:].isdigit() or not (8 <= len(phone[1:]) <= 15):
        await update.message.reply_text("صيغة الرقم غير صحيحة. أرسله بصيغة دولية.")
        return REPORT_PHONE
    context.user_data["report_phone"] = phone
    await update.message.reply_text("اكتب وصفاً مختصراً للمخالفة والأدلة المتاحة. لا ترسل بيانات حساسة غير ضرورية.")
    return REPORT_DETAILS


async def report_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return ConversationHandler.END
    details = update.message.text.strip()[:2000]
    phone = context.user_data.pop("report_phone", "")
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO reports(phone,details,created_at) VALUES(?,?,?)",
            (phone, details, datetime.now(timezone.utc).isoformat())
        )
        report_id = cur.lastrowid
    await update.message.reply_text(
        f"تم تسجيل البلاغ للمراجعة اليدوية.\nرقم البلاغ: #{report_id}\n"
        "لم يتم إرسال بلاغ إلى واتساب تلقائياً."
    )
    return ConversationHandler.END


async def reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await deny(update)
    with db() as conn:
        rows = conn.execute(
            "SELECT id,phone,status,created_at FROM reports ORDER BY id DESC LIMIT 30"
        ).fetchall()
    if not rows:
        return await update.message.reply_text("لا توجد بلاغات مسجلة.")
    lines = ["آخر البلاغات المسجلة:"]
    for row in rows:
        lines.append(f"#{row['id']} | {row['phone']} | {row['status']} | {row['created_at'][:10]}")
    await update.message.reply_text("\n".join(lines))


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END


def main():
    if not BOT_TOKEN:
        raise RuntimeError("ضع BOT_TOKEN داخل ملف .env قبل التشغيل.")
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add_account", add_account_start)],
        states={
            ADD_ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_account_label)],
            REMOVE_ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_account_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    remove_conv = ConversationHandler(
        entry_points=[CommandHandler("remove_account", remove_start)],
        states={REMOVE_ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_finish)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    report_conv = ConversationHandler(
        entry_points=[CommandHandler("new_report", new_report_start)],
        states={
            REPORT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_phone)],
            REPORT_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_details)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("accounts", accounts))
    app.add_handler(CommandHandler("reports", reports))
    app.add_handler(add_conv)
    app.add_handler(remove_conv)
    app.add_handler(report_conv)

    log.info("Wek bot is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
