"""
ربات آزمون رانندگی
Python 3.10+
کتابخانه: python-telegram-bot

نصب:
pip install python-telegram-bot --upgrade

اجرا:
Linux/macOS:
  export BOT_TOKEN="توکن_ربات"
  python bot.py

Windows PowerShell:
  $env:BOT_TOKEN="توکن_ربات"
  python bot.py
"""

import json
import os
import random
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

BASE = Path(__file__).resolve().parent
with open(BASE / "questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)


def new_quiz():
    # همان منطق فایل اصلی: ترتیب سؤال‌ها و گزینه‌ها تصادفی می‌شود.
    qs = list(QUESTIONS)
    random.shuffle(qs)
    for q in qs:
        q["options"] = list(q["options"])
        # پاسخ درست در فایل اصلی همیشه گزینه اول هر سؤال است.
        correct_text = q["options"][q["correct_index"]]
        random.shuffle(q["options"])
        q["correct_index"] = q["options"].index(correct_text)
    return qs


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("🚗 شروع آزمون", callback_data="start_quiz")]]
    await update.message.reply_text(
        "سلام 👋\n\n"
        "آزمون رانندگی آماده است.\n"
        "۵۰ سؤال چهارگزینه‌ای داری و در پایان نمره‌ات نمایش داده می‌شود.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def send_question(query, context):
    qs = context.user_data["questions"]
    i = context.user_data["index"]
    q = qs[i]

    letters = ["الف", "ب", "ج", "د"]
    keyboard = [
        [InlineKeyboardButton(f"{letters[j]}) {option}", callback_data=f"answer:{j}")]
        for j, option in enumerate(q["options"])
    ]

    await query.edit_message_text(
        f"سؤال {i + 1} از {len(qs)}\n\n{q['question']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "start_quiz":
        context.user_data["questions"] = new_quiz()
        context.user_data["index"] = 0
        context.user_data["score"] = 0
        context.user_data["wrong"] = []
        await send_question(query, context)
        return

    if not query.data.startswith("answer:"):
        return

    qs = context.user_data.get("questions")
    if not qs:
        await query.edit_message_text("برای شروع دوباره /start را بزن.")
        return

    i = context.user_data["index"]
    q = qs[i]
    selected = int(query.data.split(":")[1])
    correct = q["correct_index"]

    if selected == correct:
        context.user_data["score"] += 1
        result = "✅ درست بود!"
    else:
        result = (
            "❌ نادرست بود.\n"
            f"پاسخ درست: {q['options'][correct]}"
        )
        context.user_data["wrong"].append({
            "question": q["question"],
            "your_answer": q["options"][selected],
            "correct_answer": q["options"][correct],
        })

    i += 1
    context.user_data["index"] = i

    if i >= len(qs):
        score = context.user_data["score"]
        total = len(qs)
        percent = round(score / total * 100)

        text = (
            f"{result}\n\n"
            f"🏁 آزمون تمام شد!\n\n"
            f"نمره: {score} از {total}\n"
            f"درصد: {percent}%"
        )

        wrong = context.user_data["wrong"]
        if wrong:
            text += f"\n\n❌ تعداد پاسخ‌های غلط: {len(wrong)}"
            text += "\n\nمرور پاسخ‌های غلط:"
            for n, w in enumerate(wrong, 1):
                text += (
                    f"\n\n{n}. {w['question']}"
                    f"\nپاسخ شما: {w['your_answer']}"
                    f"\nپاسخ درست: {w['correct_answer']}"
                )

        keyboard = [[InlineKeyboardButton("🔄 آزمون دوباره", callback_data="start_quiz")]]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        keyboard = [[InlineKeyboardButton("➡️ سؤال بعدی", callback_data="next")]]
        await query.edit_message_text(
            f"{result}\n\nسؤال بعدی را بزن.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await send_question(query, context)


def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN تنظیم نشده است. توکن BotFather را در متغیر محیطی BOT_TOKEN قرار بده."
        )

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(next_question, pattern=r"^next$"))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
