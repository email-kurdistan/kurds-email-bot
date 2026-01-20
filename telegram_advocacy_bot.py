import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters, CallbackQueryHandler
)

logging.basicConfig(level=logging.INFO)

ASK_NAME = 0
BATCHES_PER_PAGE = 10
EMAIL_PAGE_URL = "https://email-kurdistan.github.io/kurds-email-bot/email_page.html"

# Groups and batches with flags
GROUPS = {
    "🇺🇸 ئەنجومەنی پیرانی ئەمریکا": [f"senate_{i}" for i in range(1, 10)],
    "🇪🇺 یەکێتی ئەوروپا": [f"eu_{i}" for i in range(1, 75)]
}

# -----------------------------
# /start
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "بەخێربێیت بۆ بۆتی ئیمەیڵی \"پشتیوانی رۆژئاوا\" ✌️\n\n"
        "ئەم بۆتە دروستکراوە بۆ ئەوەی بە شێوەیەکی سیستماتیک و کاریگەر، "
        "نامەی ناڕەزایی و داواکاری گەلی کورد بگەیەنینە ئەندامانی پەرلەمانی ئەوروپا، "
        "سیناتۆرەکانی ئەمریکا و ناوەندە دیپلۆماسییەکان.\n\n"
        "📌 هەنگاوەکان:\n"
        "1️⃣ ناوەکەت بنووسە: بۆ ئەوەی ئیمەیڵەکە بە فەرمی بە ناوی خۆتەوە بڕوات.\n"
        "2️⃣ گرووپ هەڵبژێرە: ئەو دەزگایە دیاری بکە کە دەتەوێت فشار بخەیتە سەری.\n"
        "3️⃣ ئیمەیڵ بنێرە: تەنها بە کلیکێک، ئیمەیڵێکی ئامادەکراو (Draft) لە مۆبایلەکەتدا دەکرێتەوە "
        "و تەنها دوگمەی Send دەکەیت.\n\n"
        "📝 دەنگت گرنگە، تکایە ناوەکەت  بە ئنگلیزی بنووسە بۆ دەستپێکردن:"
    )
    return ASK_NAME

# -----------------------------
# Receive name
# -----------------------------
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()

    # Show main groups
    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"group:{name}:0")]
        for name in GROUPS.keys()
    ]
    await update.message.reply_text(
        "دەزگایەک هەڵبژێرە:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

# -----------------------------
# Handle group batch pages
# -----------------------------
async def group_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split(":")
    if data[0] == "group":
        group_name = data[1]
        page = int(data[2])
        batches = GROUPS[group_name]
        total_pages = (len(batches) - 1) // BATCHES_PER_PAGE + 1

        start_idx = page * BATCHES_PER_PAGE
        end_idx = min(start_idx + BATCHES_PER_PAGE, len(batches))
        page_batches = batches[start_idx:end_idx]

        keyboard = []
        name = context.user_data.get("name", "User")
        for batch in page_batches:
            url = f"{EMAIL_PAGE_URL}?batch={batch}&name={name}"
            keyboard.append([InlineKeyboardButton(batch.replace("_", " "), url=url)])

        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅ ⏮️ Previous", callback_data=f"group:{group_name}:{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Next ⏭️ ➡", callback_data=f"group:{group_name}:{page+1}"))
        if nav_buttons:
            keyboard.append(nav_buttons)

        keyboard.append([InlineKeyboardButton("🏠 Back to groups", callback_data="back_to_groups")])

        await query.edit_message_text(
            f"{group_name} Batches (Page {page+1}/{total_pages}):",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data[0] == "back_to_groups":
        keyboard = [
            [InlineKeyboardButton(name, callback_data=f"group:{name}:0")]
            for name in GROUPS.keys()
        ]
        await query.edit_message_text(
            "Choose a group of recipients:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# -----------------------------
# Cancel
# -----------------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. Use /start to begin again.")
    return ConversationHandler.END

# -----------------------------
# Main
# -----------------------------
def main():
    BOT_TOKEN = "8059209397:AAE6MChEXHtkuqi93WREXKBFSURA2MkjBOQ"

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(group_page))

    print("Bot running…")
    app.run_polling()

if __name__ == "__main__":
    main()
