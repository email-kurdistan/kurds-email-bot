import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters, CallbackQueryHandler
)

# Logging configuration
logging.basicConfig(level=logging.INFO)

ASK_NAME = 0
BATCHES_PER_PAGE = 10
EMAIL_PAGE_URL = "https://email-kurdistan.github.io/kurds-email-bot/email_page.html"

# Global counter for the Bot Owner (Total emails across all users)
TOTAL_EMAILS_SENT = 0 

GROUPS = {
    "ئەنجومەنی پیرانی ئەمریکا": [f"senate_{i}" for i in range(1, 10)],
    "پەرلەمانی ئەوروپا": [f"eu_{i}" for i in range(1, 75)],
    "میدیا جیهانیەکان، رۆژنامە نوسان،": [f"medi_{i}" for i in range(1, 140)]
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "sent_emails" not in context.user_data:
        context.user_data["sent_emails"] = 0

    welcome_text = (
        "✌️ **هەڵمەتی نێودەوڵەتی بۆ پشتیگیری و گەیاندنی دەنگی ڕۆژئاوای کوردستان**\n\n"
        "تکایە ئێستا ناوی تەواوی خۆت بە زمانی **ئینگلیزی** بنووسە بۆ دەستپێکردنی پڕۆسەکە:"
    )

    await update.message.reply_text(welcome_text, parse_mode='Markdown')
    return ASK_NAME

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_total = context.user_data.get("sent_emails", 0)
    global_total = TOTAL_EMAILS_SENT
    
    stats_text = (
        f"📊 **ئاماری چالاکییەکان:**\n\n"
        f"👤 ژمارەی ئەو ئیمێڵانەی تەنها تۆ ناردووتە: {user_total}\n"
        f"🌍 کۆی گشتی هەموو ئیمێڵە نێردراوەکانی بۆتەکە: {global_total}"
    )
    
    if query:
        await query.answer()
        keyboard = [[InlineKeyboardButton("گەڕانەوە بۆ لیستی سەرەکی", callback_data="back_to_groups")]]
        await query.edit_message_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(stats_text, parse_mode="Markdown")

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    return await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(name, callback_data=f"group:{name}:0")] for name in GROUPS.keys()]
    keyboard.append([InlineKeyboardButton("📊 بینینی ئامار", callback_data="view_stats")])
    
    text = f"بەرێز {context.user_data.get('name')}، لایەنێک هەڵبژێرە:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def group_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TOTAL_EMAILS_SENT
    query = update.callback_query
    data = query.data.split(":")
    
    if data[0] == "view_stats":
        await show_stats(update, context)
        return

    if data[0] == "track":
        group_name = data[1]
        batch = data[2]
        
        # Change: Media group adds 20, others add 10
        increment = 20 if "میدیا" in group_name else 10
        
        context.user_data["sent_emails"] = context.user_data.get("sent_emails", 0) + increment
        TOTAL_EMAILS_SENT += increment
        
        name = context.user_data.get("name", "User")
        url = f"{EMAIL_PAGE_URL}?batch={batch}&name={name}"
        
        await query.answer("تۆمارکرا!")
        await query.message.reply_text(f"✅ ئامادەیە! کلیک لێرە بکە بۆ ناردنی {increment} ئیمێڵەکە:\n\n{url}")
        return

    if data[0] == "group":
        group_name = data[1]
        page = int(data[2])
        batches = GROUPS[group_name]
        total_pages = (len(batches) - 1) // BATCHES_PER_PAGE + 1
        page_batches = batches[page * BATCHES_PER_PAGE : (page + 1) * BATCHES_PER_PAGE]

        # Change: Display 20 for Media, 10 for others
        count_text = "٢٠" if "میدیا" in group_name else "١٠"

        keyboard = []
        for batch in page_batches:
            keyboard.append([InlineKeyboardButton(
                f"ناردنی {count_text} ئیمێڵ بۆ: {batch.replace('_', ' ').upper()}", 
                callback_data=f"track:{group_name}:{batch}"
            )])

        nav_buttons = []
        if page > 0: nav_buttons.append(InlineKeyboardButton("⬅️ پێشتر", callback_data=f"group:{group_name}:{page-1}"))
        if page < total_pages - 1: nav_buttons.append(InlineKeyboardButton("➡️ دواتر", callback_data=f"group:{group_name}:{page+1}"))
        if nav_buttons: keyboard.append(nav_buttons)
        keyboard.append([InlineKeyboardButton("🔙 گەڕانەوە", callback_data="back_to_groups")])

        await query.answer()
        await query.edit_message_text(f"لیستی: {group_name}\nلاپەڕە: {page+1} لە {total_pages}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data[0] == "back_to_groups":
        await query.answer()
        await show_main_menu(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("هەڵوەشایەوە.")
    return ConversationHandler.END

def main():
    BOT_TOKEN = "8059209397:AAE6MChEXHtkuqi93WREXKBFSURA2MkjBOQ"
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("stats", show_stats)) 
    app.add_handler(CallbackQueryHandler(group_page))

    app.run_polling()

if __name__ == "__main__":
    main()
    
# import logging
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import (
#     ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
#     ContextTypes, filters, CallbackQueryHandler
# )

# # Logging configuration
# logging.basicConfig(level=logging.INFO)

# ASK_NAME = 0
# BATCHES_PER_PAGE = 10
# EMAIL_PAGE_URL = "https://email-kurdistan.github.io/kurds-email-bot/email_page.html"

# # Global counter for the Bot Owner (Total across all users)
# TOTAL_EMAILS_SENT = 0 

# GROUPS = {
#     "ئەنجومەنی پیرانی ئەمریکا": [f"senate_{i}" for i in range(1, 10)],
#     "پەرلەمانی ئەوروپا": [f"eu_{i}" for i in range(1, 75)]
# }


# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     # Initialize user's personal count
#     if "sent_count" not in context.user_data:
#         context.user_data["sent_count"] = 0

#     welcome_text = (
#         "✌️ **هەڵمەتی نێودەوڵەتی بۆ پشتیگیری و گەیاندنی دەنگی ڕۆژئاوای کوردستان**\n\n"
#         "لەکاتێکدا برا و خوشکە شەڕڤانەکانمان لەسەر زەوی بە گیان و خوێن بەرگری لە خاک و کەرامەتی گەلەکەمان دەکەن، "
#         "لەسەر شانی ئێمەیە لە کایە دیپلۆماسییەکاندا ببینە دەنگی ڕاستەقینەیان و فشار بخەینە سەر ناوەندە بڕیاربەدەستەکانی جیهان.\n\n"
#         "📊 **ئامانجی ئەم هەڵمەتە:**\n"
#         "ئەم پڕۆژەیە بانکێکی زانیاری گەورە لەخۆ دەگرێت کە پتر لە **٧٠٠ ناونیشانی ئیمێڵی کاریگەر** و ستراتیژییە، لەوانە:\n"
#         "• سیناتۆر و نوێنەرانی کۆنگرێسی ئەمریکا 🇺🇸\n"
#         "• ئەندامانی پەرلەمانی وڵاتانی ئەوروپا 🇪🇺\n"
#         "• باڵیۆزخانە، کونسوڵخانە و ناوەندە دیپلۆماسییە جیهانییەکان 🌐\n\n"
#         "📖 **ڕێنماییەکان بۆ بەشداریکردن:**\n"
#         "١. **واژۆکردن:** پێویستە ناوی خۆت بە زمانی ئینگلیزی بنووسیت بۆ ئەوەی لە کۆتایی نامەکاندا وەک واژۆ بەکاربێت.\n"
#         "٢. **دابەشکاری:** ئیمێڵەکان بۆ چەند لیستێک دابەشکراون، هەر لیستێک **١٠ ناونیشانی جیاواز** لەخۆ دەگرێت.\n"
#         "٣. **بەردەوامی:** تکایە تەنها بە ناردنی یەک لیست نەوەستە؛ ئامانجی ئێمە گەیاندنی نامەکەیە بۆ هەر ٧٠٠ ناونیشانەکە. هەوڵ بدە هەموو لیستەکان تەواو بکەیت.\n\n"
#         "🔥 **با پێکەوە جیهان ناچار بکەین گوێ لە دەنگی ڕەوای گەلەکەمان بگرێت.**\n\n"
#         "تکایە ئێستا ناوی تەواوی خۆت بە زمانی **ئینگلیزی** بنووسە بۆ دەستپێکردنی پڕۆسەکە:"
#     )

#     await update.message.reply_text(welcome_text, parse_mode='Markdown')
#     return ASK_NAME

# # Function to show stats in Kurdish
# async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     user_total = context.user_data.get("sent_count", 0) * 10
#     global_total = TOTAL_EMAILS_SENT * 10
    
#     stats_text = (
#         f"📊 **ئاماری چالاکییەکان:**\n\n"
#         f"👤 ژمارەی ئەو ئیمێڵانەی تەنها تۆ ناردووتە: {user_total}\n"
#         f"🌍 کۆی گشتی هەموو ئیمێڵە نێردراوەکانی بۆتەکە: {global_total}\n\n"
#         f"تێبینی: هەر لیستێک کلیک دەکەیت ١٠ ئیمێڵ دەنێرێت."
#     )
    
#     # If called from a button, edit message; if from command, reply
#     if query:
#         await query.answer()
#         keyboard = [[InlineKeyboardButton("گەڕانەوە بۆ لیستی سەرەکی", callback_data="back_to_groups")]]
#         await query.edit_message_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
#     else:
#         await update.message.reply_text(stats_text, parse_mode="Markdown")

# async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data["name"] = update.message.text.strip()
#     return await show_main_menu(update, context)

# async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     keyboard = [[InlineKeyboardButton(name, callback_data=f"group:{name}:0")] for name in GROUPS.keys()]
#     # Added a dedicated button for Stats so users don't need to know commands
#     keyboard.append([InlineKeyboardButton("📊 بینینی ژمارەی ئیمێڵە نێردراوەکان", callback_data="view_stats")])
    
#     text = f"بەرێز {context.user_data.get('name')}، لایەنێک هەڵبژێرە بۆ ناردنی ئیمێڵ:"
    
#     if update.callback_query:
#         await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
#     else:
#         await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
#     return ConversationHandler.END

# async def group_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     global TOTAL_EMAILS_SENT
#     query = update.callback_query
#     data = query.data.split(":")
    
#     if data[0] == "view_stats":
#         await show_stats(update, context)
#         return

#     if data[0] == "track":
#         context.user_data["sent_count"] = context.user_data.get("sent_count", 0) + 1
#         TOTAL_EMAILS_SENT += 1
        
#         batch = data[2]
#         name = context.user_data.get("name", "User")
#         url = f"{EMAIL_PAGE_URL}?batch={batch}&name={name}"
        
#         user_total = context.user_data["sent_count"] * 10
        
#         await query.answer("تۆمارکرا!")
#         await query.message.reply_text(
#             f"✅ ئامادەیە! کلیک لەم بەستەرەی خوارەوە بکە بۆ ناردنی ١٠ ئیمێڵەکە:\n\n{url}\n\n"
#             f""
#         )
#         return

#     if data[0] == "group":
#         group_name = data[1]
#         page = int(data[2])
#         batches = GROUPS[group_name]
#         total_pages = (len(batches) - 1) // BATCHES_PER_PAGE + 1
#         page_batches = batches[page * BATCHES_PER_PAGE : (page + 1) * BATCHES_PER_PAGE]

#         keyboard = []
#         for batch in page_batches:
#             keyboard.append([InlineKeyboardButton(
#                 f"ناردنی ١٠ ئیمێڵ بۆ: {batch.replace('_', ' ').upper()}", 
#                 callback_data=f"track:{group_name}:{batch}"
#             )])

#         nav_buttons = []
#         if page > 0: nav_buttons.append(InlineKeyboardButton("⬅️ پێشتر", callback_data=f"group:{group_name}:{page-1}"))
#         if page < total_pages - 1: nav_buttons.append(InlineKeyboardButton("➡️ دواتر", callback_data=f"group:{group_name}:{page+1}"))
#         if nav_buttons: keyboard.append(nav_buttons)
#         keyboard.append([InlineKeyboardButton("🔙 گەڕانەوە بۆ لیستی سەرەکی", callback_data="back_to_groups")])

#         await query.answer()
#         await query.edit_message_text(f"لیستی: {group_name}\nلاپەڕە: {page+1} لە {total_pages}", reply_markup=InlineKeyboardMarkup(keyboard))

#     elif data[0] == "back_to_groups":
#         await query.answer()
#         await show_main_menu(update, context)

# async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text("هەڵوەشایەوە.")
#     return ConversationHandler.END

# def main():
#     BOT_TOKEN = "8059209397:AAE6MChEXHtkuqi93WREXKBFSURA2MkjBOQ"
#     app = ApplicationBuilder().token(BOT_TOKEN).build()

#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler("start", start)],
#         states={ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)]},
#         fallbacks=[CommandHandler("cancel", cancel)],
#     )
    
#     app.add_handler(conv_handler)
#     app.add_handler(CommandHandler("stats", show_stats)) 
#     app.add_handler(CallbackQueryHandler(group_page))

#     print("Bot is running...")
#     app.run_polling()

# if __name__ == "__main__":
#     main()
    
# import logging
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import (
#     ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
#     ContextTypes, filters, CallbackQueryHandler
# )
# from telegram.constants import ParseMode

# # 1. Logging configuration
# logging.basicConfig(level=logging.INFO)

# ASK_NAME = 0
# BATCHES_PER_PAGE = 10
# EMAIL_PAGE_URL = "https://email-kurdistan.github.io/kurds-email-bot/email_page.html"

# # Global counter (Note: This resets if the bot restarts)
# TOTAL_EMAILS_SENT = 0 

# GROUPS = {
#     "ئەنجومەنی پیرانی ئەمریکا": [f"senate_{i}" for i in range(1, 11)],
#     "پەرلەمانی ئەوروپا و سەفارەتەکان": [f"eu_{i}" for i in range(1, 75)]
# }

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if "sent_count" not in context.user_data:
#         context.user_data["sent_count"] = 0

#     welcome_text = (
#         "✌️ **بۆتی هەڵمەتی ناردنی ئیمێڵ بۆ پشتیوانی ڕۆژئاوا**\n\n"
#         "لەکاتێکدا خوشک و براکانمان لەسەر زەوی بە خوێن بەرگری لە خاک دەکەن، "
#         "ئەرکی ئێمەیە وەک **سەربازی سەر شاشەکان** ملیۆنان ئیمێڵ بنێرین.\n\n"
#         "✊ **تکایە ئێستا ناوی تەواوی خۆت بە ئینگلیزی بنووسە بۆ دەستپێکردن:**"
#     )
#     await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
#     return ASK_NAME

# async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data["name"] = update.message.text.strip()
#     # Move to main menu
#     return await show_main_menu(update, context)

# async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     keyboard = [[InlineKeyboardButton(name, callback_data=f"group:{name}:0")] for name in GROUPS.keys()]
#     keyboard.append([InlineKeyboardButton("📊 ئاماری گشتی", callback_data="view_stats")])
    
#     text = f"بەرێز {context.user_data.get('name')}، لایەنێک هەڵبژێرە:"
    
#     if update.callback_query:
#         await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
#     else:
#         await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
#     # We return ConversationHandler.END here so the bot stops waiting for a text message
#     # and starts listening to CallbackQueries (buttons).
#     return ConversationHandler.END

# async def group_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     global TOTAL_EMAILS_SENT
#     query = update.callback_query
#     await query.answer()
    
#     data = query.data.split(":")
    
#     if data[0] == "view_stats":
#         user_total = context.user_data.get("sent_count", 0) * 10
#         global_total = TOTAL_EMAILS_SENT * 10
#         stats_text = (
#             f"📊 **ئاماری چالاکییەکان:**\n\n"
#             f"👤 هی تۆ: {user_total}\n"
#             f"🌍 کۆی گشتی: {global_total}\n"
#         )
#         keyboard = [[InlineKeyboardButton("🔙 گەڕانەوە", callback_data="back_to_groups")]]
#         await query.edit_message_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
#         return

#     if data[0] == "track":
#         context.user_data["sent_count"] = context.user_data.get("sent_count", 0) + 1
#         TOTAL_EMAILS_SENT += 1
        
#         batch = data[2]
#         name = context.user_data.get("name", "User")
#         url = f"{EMAIL_PAGE_URL}?batch={batch}&name={name}"
        
#         await query.message.reply_text(
#             f"✅ ئامادەیە! کلیک لێرە بکە بۆ ناردن:\n{url}"
#         )
#         return

#     if data[0] == "group" or data[0] == "back_to_groups":
#         if data[0] == "back_to_groups":
#             return await show_main_menu(update, context)
            
#         group_name = data[1]
#         page = int(data[2])
#         batches = GROUPS[group_name]
#         total_pages = (len(batches) - 1) // BATCHES_PER_PAGE + 1
#         page_batches = batches[page * BATCHES_PER_PAGE : (page + 1) * BATCHES_PER_PAGE]

#         keyboard = []
#         for batch in page_batches:
#             keyboard.append([InlineKeyboardButton(
#                 f"📧 ناردنی: {batch.replace('_', ' ').upper()}", 
#                 callback_data=f"track:{group_name}:{batch}"
#             )])

#         nav_buttons = []
#         if page > 0: nav_buttons.append(InlineKeyboardButton("⬅️ پێشتر", callback_data=f"group:{group_name}:{page-1}"))
#         if page < total_pages - 1: nav_buttons.append(InlineKeyboardButton("➡️ دواتر", callback_data=f"group:{group_name}:{page+1}"))
#         if nav_buttons: keyboard.append(nav_buttons)
#         keyboard.append([InlineKeyboardButton("🔙 لیستە سەرەکییەکە", callback_data="back_to_groups")])

#         await query.edit_message_text(f"لیستی: {group_name}\nلاپەڕە: {page+1}/{total_pages}", reply_markup=InlineKeyboardMarkup(keyboard))

# async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text("هەڵوەشایەوە.")
#     return ConversationHandler.END

# def main():
#     # گرنگ: لێرە تۆکنە نوێیەکەت دابنێ
#     BOT_TOKEN = "8059209397:AAE6MChEXHtkuqi93WREXKBFSURA2MkjBOQ"
#     app = ApplicationBuilder().token(BOT_TOKEN).build()

#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler("start", start)],
#         states={
#             ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)]
#         },
#         fallbacks=[CommandHandler("cancel", cancel)],
#     )
    
#     app.add_handler(conv_handler)
#     app.add_handler(CallbackQueryHandler(group_page)) # Handle all button clicks here

#     print("Bot is running...")
#     app.run_polling()

# if __name__ == "__main__":
#     main()
    
# import logging
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import (
#     ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
#     ContextTypes, filters, CallbackQueryHandler
# )

# # Logging configuration
# logging.basicConfig(level=logging.INFO)

# ASK_NAME = 0
# BATCHES_PER_PAGE = 10
# EMAIL_PAGE_URL = "https://email-kurdistan.github.io/kurds-email-bot/email_page.html"

# # Global counter for the Bot Owner (Total across all users)
# TOTAL_EMAILS_SENT = 0 

# GROUPS = {
#     "ئەنجومەنی پیرانی ئەمریکا": [f"senate_{i}" for i in range(1, 10)],
#     "پەرلەمانی ئەوروپا و سەفارەتەکان": [f"eu_{i}" for i in range(1, 75)]
# }

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     # Initialize user's personal count
#     if "sent_count" not in context.user_data:
#         context.user_data["sent_count"] = 0

#     welcome_text = (
#         "✌️ **بۆتی هەڵمەتی ناردنی ئیمێڵ بۆ پشتیوانی ڕۆژئاوا**\n\n"
#         "لەکاتێکدا خوشک و براکانمان لەسەر زەوی بە خوێن بەرگری لە خاک دەکەن، "
#         "ئەرکی ئێمەیە وەک **سەربازی سەر شاشەکان** ملیۆنان ئیمێڵ بنێرین و "
#         "ڕێگە نەدەین جیهان لە ئاست ئەم داگیرکارییەدا بێدەنگ بێت.\n\n"
#         "🔥 **هەر ئیمێڵێک کە تۆ دەینێریت، فشارێکی سیاسییە لەسەر ناوەندە بڕیاربەدەستەکان.**\n\n"
#         "**هەنگاوەکان:**\n"
#         "١. ناوی خۆت بە ئینگلیزی بنووسە.\n"
#         "٢. وڵات یان لایەنی مەبەست هەڵبژێرە.\n"
#         "٣. بە یەک کلیک لیستەکان بنێرە.\n\n"
#         "✊ **تکایە ئێستا ناوی تەواوی خۆت بە ئینگلیزی بنووسە بۆ دەستپێکردن:**"
#     )
#     await update.message.reply_text(welcome_text)
#     return ASK_NAME

# # Function to show stats in Kurdish
# async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     user_total = context.user_data.get("sent_count", 0) * 10
#     global_total = TOTAL_EMAILS_SENT * 10
    
#     stats_text = (
#         f"📊 **ئاماری چالاکییەکان:**\n\n"
#         f"👤 ژمارەی ئەو ئیمێڵانەی تەنها تۆ ناردووتە: {user_total}\n"
#         f"🌍 کۆی گشتی هەموو ئیمێڵە نێردراوەکانی بۆتەکە: {global_total}\n\n"
#         f"تێبینی: هەر لیستێک کلیک دەکەیت ١٠ ئیمێڵ دەنێرێت."
#     )
    
#     # If called from a button, edit message; if from command, reply
#     if query:
#         await query.answer()
#         keyboard = [[InlineKeyboardButton("گەڕانەوە بۆ لیستی سەرەکی", callback_data="back_to_groups")]]
#         await query.edit_message_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
#     else:
#         await update.message.reply_text(stats_text, parse_mode="Markdown")

# async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data["name"] = update.message.text.strip()
#     return await show_main_menu(update, context)

# async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     keyboard = [[InlineKeyboardButton(name, callback_data=f"group:{name}:0")] for name in GROUPS.keys()]
#     # Added a dedicated button for Stats so users don't need to know commands
#     keyboard.append([InlineKeyboardButton("📊 بینینی ژمارەی ئیمێڵە نێردراوەکان", callback_data="view_stats")])
    
#     text = f"بەرێز {context.user_data.get('name')}، لایەنێک هەڵبژێرە بۆ ناردنی ئیمێڵ:"
    
#     if update.callback_query:
#         await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
#     else:
#         await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
#     return ConversationHandler.END

# async def group_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     global TOTAL_EMAILS_SENT
#     query = update.callback_query
#     data = query.data.split(":")
    
#     if data[0] == "view_stats":
#         await show_stats(update, context)
#         return

#     if data[0] == "track":
#         context.user_data["sent_count"] = context.user_data.get("sent_count", 0) + 1
#         TOTAL_EMAILS_SENT += 1
        
#         batch = data[2]
#         name = context.user_data.get("name", "User")
#         url = f"{EMAIL_PAGE_URL}?batch={batch}&name={name}"
        
#         user_total = context.user_data["sent_count"] * 10
        
#         await query.answer("تۆمارکرا!")
#         await query.message.reply_text(
#             f"✅ ئامادەیە! کلیک لەم بەستەرەی خوارەوە بکە بۆ ناردنی ١٠ ئیمێڵ:\n\n{url}\n\n"
#         )
#         return
    
    

#     if data[0] == "group":
#         group_name = data[1]
#         page = int(data[2])
#         batches = GROUPS[group_name]
#         total_pages = (len(batches) - 1) // BATCHES_PER_PAGE + 1
#         page_batches = batches[page * BATCHES_PER_PAGE : (page + 1) * BATCHES_PER_PAGE]

#         keyboard = []
#         for batch in page_batches:
#             keyboard.append([InlineKeyboardButton(
#                 f"ناردنی ١٠ ئیمێڵ بۆ: {batch.replace('_', ' ').upper()}", 
#                 callback_data=f"track:{group_name}:{batch}"
#             )])

#         nav_buttons = []
#         if page > 0: nav_buttons.append(InlineKeyboardButton("⬅️ پێشتر", callback_data=f"group:{group_name}:{page-1}"))
#         if page < total_pages - 1: nav_buttons.append(InlineKeyboardButton("➡️ دواتر", callback_data=f"group:{group_name}:{page+1}"))
#         if nav_buttons: keyboard.append(nav_buttons)
#         keyboard.append([InlineKeyboardButton("🔙 گەڕانەوە بۆ لیستی سەرەکی", callback_data="back_to_groups")])

#         await query.answer()
#         await query.edit_message_text(f"لیستی: {group_name}\nلاپەڕە: {page+1} لە {total_pages}", reply_markup=InlineKeyboardMarkup(keyboard))

#     elif data[0] == "back_to_groups":
#         await query.answer()
#         await show_main_menu(update, context)

# async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text("هەڵوەشایەوە.")
#     return ConversationHandler.END

# def main():
#     BOT_TOKEN = "8059209397:AAE6MChEXHtkuqi93WREXKBFSURA2MkjBOQ"
#     app = ApplicationBuilder().token(BOT_TOKEN).build()

#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler("start", start)],
#         states={ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)]},
#         fallbacks=[CommandHandler("cancel", cancel)],
#     )
    
#     app.add_handler(conv_handler)
#     app.add_handler(CommandHandler("stats", show_stats)) 
#     app.add_handler(CallbackQueryHandler(group_page))

#     print("Bot is running...")
#     app.run_polling()

# if __name__ == "__main__":
#     main()
    
# import logging
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import (
#     ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
#     ContextTypes, filters, CallbackQueryHandler
# )

# # Logging configuration
# logging.basicConfig(level=logging.INFO)

# ASK_NAME = 0
# BATCHES_PER_PAGE = 10
# EMAIL_PAGE_URL = "https://email-kurdistan.github.io/kurds-email-bot/email_page.html"

# # --- NEW: Global counter (In production, use a database or file) ---
# TOTAL_EMAILS_SENT = 0 

# GROUPS = {
#     "ئەنجومەنی پیرانی ئەمریکا": [f"senate_{i}" for i in range(1, 10)],
#     "پەرلەمانی ئەوروپا": [f"eu_{i}" for i in range(1, 75)]
# }

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     welcome_text = (
#         "بەخێربێیت بۆ بۆتی هەڵمەتی ناردنی ئیمێڵ\n\n"
#         "ئەم بۆتە دیزاین کراوە بۆ گەیاندنی دەنگی کوردانی ڕۆژئاوا...\n"
#         "تکایە ئێستا ناوی تەواوی خۆت بە ئینگلیزی بنووسە:"
#     )
#     await update.message.reply_text(welcome_text)
#     return ASK_NAME

# # --- NEW: Command to check stats ---
# async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text(f"📊 کۆی گشتی ئیمێڵە کلیککراوەکان: {TOTAL_EMAILS_SENT * 10}")

# async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data["name"] = update.message.text.strip()
#     keyboard = [[InlineKeyboardButton(name, callback_data=f"group:{name}:0")] for name in GROUPS.keys()]
#     await update.message.reply_text(f"بەرێز {context.user_data['name']}، لایەنێک هەڵبژێرە:", reply_markup=InlineKeyboardMarkup(keyboard))
#     return ConversationHandler.END

# async def group_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     global TOTAL_EMAILS_SENT
#     query = update.callback_query
#     await query.answer()

#     data = query.data.split(":")
    
#     # --- NEW: Logic to count the click ---
#     if data[0] == "track":
#         TOTAL_EMAILS_SENT += 1
#         group_name = data[1]
#         batch = data[2]
#         name = context.user_data.get("name", "User")
#         url = f"{EMAIL_PAGE_URL}?batch={batch}&name={name}"
        
#         # We must send a message with the actual link because Telegram 
#         # doesn't allow direct redirects from a callback logic for security.
#         await query.message.reply_text(
#             f"✅ ئامادەیە! کلیک لەم بەستەرە بکە بۆ ناردنی ئیمێڵەکان:\n\n{url}"
#         )
#         return

#     if data[0] == "group":
#         group_name = data[1]
#         page = int(data[2])
#         batches = GROUPS[group_name]
#         total_pages = (len(batches) - 1) // BATCHES_PER_PAGE + 1
#         page_batches = batches[page * BATCHES_PER_PAGE : (page + 1) * BATCHES_PER_PAGE]

#         keyboard = []
#         for batch in page_batches:
#             # CHANGED: Instead of a direct URL, we call our "track" callback
#             keyboard.append([InlineKeyboardButton(
#                 f"ناردن بۆ: {batch.replace('_', ' ').upper()} (١٠ ئیمێڵ)", 
#                 callback_data=f"track:{group_name}:{batch}"
#             )])

#         nav_buttons = []
#         if page > 0: nav_buttons.append(InlineKeyboardButton("پێشتر", callback_data=f"group:{group_name}:{page-1}"))
#         if page < total_pages - 1: nav_buttons.append(InlineKeyboardButton("دواتر", callback_data=f"group:{group_name}:{page+1}"))
#         if nav_buttons: keyboard.append(nav_buttons)
#         keyboard.append([InlineKeyboardButton("گەڕانەوە بۆ لیستی سەرەکی", callback_data="back_to_groups")])

#         await query.edit_message_text(f"لیستی: {group_name}\nلاپەڕە: {page+1} لە {total_pages}", reply_markup=InlineKeyboardMarkup(keyboard))

#     elif data[0] == "back_to_groups":
#         keyboard = [[InlineKeyboardButton(name, callback_data=f"group:{name}:0")] for name in GROUPS.keys()]
#         await query.edit_message_text("تکایە لایەنێک هەڵبژێرە:", reply_markup=InlineKeyboardMarkup(keyboard))

# async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text("هەڵوەشایەوە.")
#     return ConversationHandler.END

# def main():
#     BOT_TOKEN = "8059209397:AAE6MChEXHtkuqi93WREXKBFSURA2MkjBOQ"
#     app = ApplicationBuilder().token(BOT_TOKEN).build()

#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler("start", start)],
#         states={ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)]},
#         fallbacks=[CommandHandler("cancel", cancel)],
#     )
    
#     app.add_handler(conv_handler)
#     app.add_handler(CommandHandler("stats", stats)) # NEW: Stats command
#     app.add_handler(CallbackQueryHandler(group_page))

#     print("Bot is running...")
#     app.run_polling()

# if __name__ == "__main__":
#     main()
    
# import logging
# import os
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import (
#     ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
#     ContextTypes, filters, CallbackQueryHandler
# )

# # Logging configuration
# logging.basicConfig(level=logging.INFO)

# # States
# ASK_NAME, ASK_SUGGESTION = range(2)
# BATCHES_PER_PAGE = 10
# EMAIL_PAGE_URL = "https://email-kurdistan.github.io/kurds-email-bot/email_page.html"
# ADMIN_ID = 6451356602 
# STATS_FILE = "stats.txt"

# # Groups and batches
# GROUPS = {
#     "ئەنجومەنی پیرانی ئەمریکا": [f"senate_{i}" for i in range(1, 10)],
#     "پەرلەمانی ئەوروپا": [f"eu_{i}" for i in range(1, 75)]
# }

# # -----------------------------
# # Helper Functions for Stats
# # -----------------------------
# def increment_stat():
#     count = get_stats()
#     with open(STATS_FILE, "w") as f:
#         f.write(str(count + 1))

# def get_stats():
#     if not os.path.exists(STATS_FILE):
#         return 0
#     with open(STATS_FILE, "r") as f:
#         try:
#             return int(f.read().strip())
#         except:
#             return 0

# # -----------------------------
# # Keyboards
# # -----------------------------
# def main_menu_keyboard():
#     keyboard = [[InlineKeyboardButton(name, callback_data=f"group:{name}:0")] for name in GROUPS.keys()]
#     keyboard.append([InlineKeyboardButton("💡 پێشنیارکردنی ئیمێڵ یان ناوەند", callback_data="suggest_start")])
#     return InlineKeyboardMarkup(keyboard)

# # -----------------------------
# # Handlers
# # -----------------------------
# # async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
# #     welcome_text = (
# #         "بەخێربێیت بۆ بۆتی هەڵمەتی ناردنی ئیمێڵ\n\n"
# #         "ئەم بۆتە دیزاین کراوە بۆ گەیاندنی دەنگی کوردانی ڕۆژئاوا بە ناوەندە بڕیاربەدەستە نێودەوڵەتییەکان.\n\n"
# #         "ڕێنمایی بەکارهێنان:\n"
# #         "١. ناوی خۆت بە ئینگلیزی بنووسە بۆ ئەوەی وەک واژۆ لە کۆتایی نامەکەدا دابنرێت.\n"
# #         "٢. دامەزراوەی مەبەست هەڵبژێرە (ئەمریکا یان ئەوروپا).\n"
# #         "٣. کرتە لەسەر لیستەکان بکە؛ ئیمێڵەکان ئامادەکراون و تەنها پێویستیان بە ناردن (Send) هەیە.\n\n"
# #         "تێبینی:\n"
# #         "هەر گروپێک لە لیستەکان ئیمێڵی ١٠ کەسی جیاوازی تێدایە. تکایە هەوڵبدە هەموو لیستەکان بنێریت بۆ ئەوەی پەیامەکە بگاتە زۆرترین کەس.\n\n"
# #         "تکایە ئێستا ناوی تەواوی خۆت بە ئینگلیزی بنووسە:"
# #     )
# #     await update.message.reply_text(welcome_text)
# #     return ASK_NAME

# async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Command to check how many clicks have been recorded"""
#     if update.effective_user.id == ADMIN_ID:
#         total = get_stats()
#         await update.message.reply_text(f"📊 ئاماری گشتی:\nتا ئێستا {total} جار کلیک لەسەر لینکەکانی ناردن کراوە.")
#     else:
#         await update.message.reply_text("تەنها بەڕێوەبەر دەتوانێت ئەم فەرمانە بەکاربهێنێت.")

# async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data["name"] = update.message.text.strip()
#     await update.message.reply_text(
#         f"بەرێز {context.user_data['name']}، لایەنێک هەڵبژێرە بۆ ناردنی ئیمێڵ یان پێشنیار بنێرە:",
#         reply_markup=main_menu_keyboard()
#     )
#     return ConversationHandler.END

# async def group_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#     data = query.data.split(":")

#     if data[0] == "group":
#         group_name, page = data[1], int(data[2])
#         batches = GROUPS[group_name]
#         total_pages = (len(batches) - 1) // BATCHES_PER_PAGE + 1
#         start_idx = page * BATCHES_PER_PAGE
#         page_batches = batches[start_idx : start_idx + BATCHES_PER_PAGE]

#         keyboard = []
#         name = context.user_data.get("name", "User")
        
#         for batch in page_batches:
#             # We change this to a callback_data so we can catch the click and count it
#             keyboard.append([InlineKeyboardButton(f"ناردن بۆ: {batch.upper()}", callback_data=f"track:{batch}")])

#         nav_buttons = []
#         if page > 0: nav_buttons.append(InlineKeyboardButton("پێشتر", callback_data=f"group:{group_name}:{page-1}"))
#         if page < total_pages - 1: nav_buttons.append(InlineKeyboardButton("دواتر", callback_data=f"group:{group_name}:{page+1}"))
        
#         if nav_buttons: keyboard.append(nav_buttons)
#         keyboard.append([InlineKeyboardButton("🏠 گەڕانەوە", callback_data="back_to_groups")])

#         await query.edit_message_text(f"لیستی: {group_name}", reply_markup=InlineKeyboardMarkup(keyboard))

#     elif data[0] == "track":
#         # This part increments the counter and then gives the link
#         batch_id = data[1]
#         name = context.user_data.get("name", "User")
#         increment_stat()
        
#         url = f"{EMAIL_PAGE_URL}?batch={batch_id}&name={name}"
        
#         # We send a small message with the actual link to open
#         await query.message.reply_text(
#             f"بۆ ناردنی ئیمێڵەکانی {batch_id.upper()} کلیک لەم لینکەی خوارەوە بکە:",
#             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Open Email Page ✉️", url=url)]])
#         )

#     elif data[0] == "back_to_groups":
#         await query.edit_message_text("تکایە لایەنێک هەڵبژێرە:", reply_markup=main_menu_keyboard())

# # --- Suggestions and Cancel handlers remain the same as your previous working code ---
# async def suggest_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#     await query.edit_message_text("تکایە ناو یان ئیمێڵەکەی لێرە بنووسە و بۆمان بنێرە:")
#     return ASK_SUGGESTION

# async def receive_suggestion(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     suggestion = update.message.text
#     user_info = update.message.from_user.first_name
#     try:
#         await context.bot.send_message(chat_id=ADMIN_ID, text=f"📩 پێشنیارێکی نوێ:\nلە لایەن: {user_info}\nناوەرۆک: {suggestion}")
#     except: pass
#     await update.message.reply_text("زۆر سوپاس! پێشنیارەکەت وەرگیرا.", reply_markup=main_menu_keyboard())
#     return ConversationHandler.END

# async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text("هەڵوەشایەوە.")
#     return ConversationHandler.END

# def main():
#     BOT_TOKEN = "8059209397:AAE6MChEXHtkuqi93WREXKBFSURA2MkjBOQ"
#     app = ApplicationBuilder().token(BOT_TOKEN).build()

#     conv_handler = ConversationHandler(
#         entry_points=[
#             CommandHandler("start", start),
#             CallbackQueryHandler(suggest_callback, pattern="^suggest_start$")
#         ],
#         states={
#             ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
#             ASK_SUGGESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_suggestion)]
#         },
#         fallbacks=[CommandHandler("cancel", cancel)],
#         allow_reentry=True
#     )
    
#     app.add_handler(conv_handler)
#     app.add_handler(CommandHandler("stats", stats_command))
#     app.add_handler(CallbackQueryHandler(group_page))

#     print("Bot is running...")
#     app.run_polling()

# if __name__ == "__main__":
#     main()
# import logging
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import (
#     ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
#     ContextTypes, filters, CallbackQueryHandler
# )

# # Logging configuration
# logging.basicConfig(level=logging.INFO)

# ASK_NAME = 0
# BATCHES_PER_PAGE = 10
# EMAIL_PAGE_URL = "https://email-kurdistan.github.io/kurds-email-bot/email_page.html"

# # Groups and batches
# GROUPS = {
#     "ئەنجومەنی پیرانی ئەمریکا": [f"senate_{i}" for i in range(1, 10)],
#     "پەرلەمانی ئەوروپا": [f"eu_{i}" for i in range(1, 75)]
# }

# # -----------------------------
# # /start
# # -----------------------------
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     welcome_text = (
#         "بەخێربێیت بۆ بۆتی هەڵمەتی ناردنی ئیمێڵ\n\n"
#         "ئەم بۆتە دیزاین کراوە بۆ گەیاندنی دەنگی کوردانی ڕۆژئاوا بە ناوەندە بڕیاربەدەستە نێودەوڵەتییەکان.\n\n"
#         "ڕێنمایی بەکارهێنان:\n"
#         "١. ناوی خۆت بە ئینگلیزی بنووسە بۆ ئەوەی وەک واژۆ لە کۆتایی نامەکەدا دابنرێت.\n"
#         "٢. دامەزراوەی مەبەست هەڵبژێرە (ئەمریکا یان ئەوروپا).\n"
#         "٣. کرتە لەسەر لیستەکان بکە؛ ئیمێڵەکان ئامادەکراون و تەنها پێویستیان بە ناردن (Send) هەیە.\n\n"
#         "تێبینی:\n"
#         "هەر گروپێک لە لیستەکان ئیمێڵی ١٠ کەسی جیاوازی تێدایە. تکایە هەوڵبدە هەموو لیستەکان بنێریت بۆ ئەوەی پەیامەکە بگاتە زۆرترین کەس.\n\n"
#         "تکایە ئێستا ناوی تەواوی خۆت بە ئینگلیزی بنووسە:"
#     )
#     await update.message.reply_text(welcome_text)
#     return ASK_NAME

# # -----------------------------
# # Receive name
# # -----------------------------
# async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data["name"] = update.message.text.strip()
    
#     keyboard = [
#         [InlineKeyboardButton(name, callback_data=f"group:{name}:0")]
#         for name in GROUPS.keys()
#     ]
    
#     await update.message.reply_text(
#         f"بەرێز {context.user_data['name']}، تکایە لایەنی مەبەست هەڵبژێرە:",
#         reply_markup=InlineKeyboardMarkup(keyboard)
#     )
#     return ConversationHandler.END

# # -----------------------------
# # Handle group batch pages
# # -----------------------------
# async def group_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()

#     data = query.data.split(":")
#     if data[0] == "group":
#         group_name = data[1]
#         page = int(data[2])
#         batches = GROUPS[group_name]
#         total_pages = (len(batches) - 1) // BATCHES_PER_PAGE + 1

#         start_idx = page * BATCHES_PER_PAGE
#         end_idx = min(start_idx + BATCHES_PER_PAGE, len(batches))
#         page_batches = batches[start_idx:end_idx]

#         keyboard = []
#         name = context.user_data.get("name", "User")
        
#         for batch in page_batches:
#             url = f"{EMAIL_PAGE_URL}?batch={batch}&name={name}"
#             display_name = batch.replace("_", " ").upper()
#             keyboard.append([InlineKeyboardButton(f"ناردن بۆ: {display_name} (١٠ ئیمێڵ)", url=url)])

#         nav_buttons = []
#         if page > 0:
#             nav_buttons.append(InlineKeyboardButton("پێشتر", callback_data=f"group:{group_name}:{page-1}"))
#         if page < total_pages - 1:
#             nav_buttons.append(InlineKeyboardButton("دواتر", callback_data=f"group:{group_name}:{page+1}"))
        
#         if nav_buttons:
#             keyboard.append(nav_buttons)

#         keyboard.append([InlineKeyboardButton("گەڕانەوە بۆ لیستی سەرەکی", callback_data="back_to_groups")])

#         instruction_text = (
#             f"لیستی: {group_name}\n"
#             f"هەر بەستەرێکی خوارەوە ئیمێڵ بۆ ١٠ نوێنەری جیاواز دەنێرێت.\n"
#             f"لاپەڕە: {page+1} لە {total_pages}"
#         )

#         await query.edit_message_text(
#             instruction_text,
#             reply_markup=InlineKeyboardMarkup(keyboard)
#         )

#     elif data[0] == "back_to_groups":
#         keyboard = [
#             [InlineKeyboardButton(name, callback_data=f"group:{name}:0")]
#             for name in GROUPS.keys()
#         ]
#         await query.edit_message_text(
#             "تکایە لایەنێک هەڵبژێرە:",
#             reply_markup=InlineKeyboardMarkup(keyboard)
#         )

# # -----------------------------
# # Cancel
# # -----------------------------
# async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text("کردارەکە هەڵوەشایەوە. بۆ دەستپێکردنەوە بنووسە /start")
#     return ConversationHandler.END

# # -----------------------------
# # Main
# # -----------------------------
# def main():
#     # ⚠️ Reminder: Use your actual token here from @BotFather
#     BOT_TOKEN = "8059209397:AAE6MChEXHtkuqi93WREXKBFSURA2MkjBOQ"

#     app = ApplicationBuilder().token(BOT_TOKEN).build()

#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler("start", start)],
#         states={ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)]},
#         fallbacks=[CommandHandler("cancel", cancel)],
#     )
    
#     app.add_handler(conv_handler)
#     app.add_handler(CallbackQueryHandler(group_page))

#     print("Bot is running...")
#     app.run_polling()

# if __name__ == "__main__":
#     main()
    
# # import logging
# # from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# # from telegram.ext import (
# #     ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
# #     ContextTypes, filters, CallbackQueryHandler
# # )

# # logging.basicConfig(level=logging.INFO)

# # ASK_NAME = 0
# # BATCHES_PER_PAGE = 10
# # EMAIL_PAGE_URL = "https://email-kurdistan.github.io/kurds-email-bot/email_page.html"

# # # Groups and batches with flags
# # GROUPS = {
# #     "🇺🇸 ئەنجومەنی پیرانی ئەمریکا": [f"senate_{i}" for i in range(1, 10)],
# #     "🇪🇺 یەکێتی ئەوروپا": [f"eu_{i}" for i in range(1, 75)]
# # }

# # # -----------------------------
# # # /start
# # # -----------------------------
# # async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
# #     await update.message.reply_text(
# #         " هەڵمەتی ناردنی ئیمێڵ بۆ پاڵپشتی ڕۆژئاوا\n\n"
# #         "لەڕێگەی ئەم بۆتەوە، دەنگت بگەیەنە بە "
# #         "٩٠ کۆنگرێسمانی ئەمریکا و ٤٠٠ ئەندامی پەرلەمانی ئەوروپا.\n\n"
# #         "🛠 چۆن بەژدار دەبیت؟\n"
# #         "1️⃣ بچۆ ناو بۆتەکە و Start بکە.\n"
# #         "2️⃣ ناوی خۆت بنوسە.\n"
# #         "3️⃣ بەشی ئەمریکا یان ئەوروپا هەڵبژێرە.\n"
# #         "4️⃣ ناردن: تەنها دەست بنێ بە Open و پاشان Send.\n\n"
# #         "⚠️ خاڵی گرنگ:\n"
# #         "ناونیشانی کەسەکان و دەقی نامەکان بە ئۆتۆماتیکی پڕکراونەتەوە؛ "
# #         "تۆ تەنها دەنێریت.\n"
# #         "تکایە هەموو بەشەکان بنێرە چونکە هەر لینکێک بۆ ١٠ کەسی جیاواز دەچێت.\n\n"
# #         "📝 تکایە ناوی خۆت بە ئینگلیزی بنووسە:"
# #     )
# #     return ASK_NAME

# # # -----------------------------
# # # Receive name
# # # -----------------------------
# # async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
# #     context.user_data["name"] = update.message.text.strip()

# #     # Show main groups
# #     keyboard = [
# #         [InlineKeyboardButton(name, callback_data=f"group:{name}:0")]
# #         for name in GROUPS.keys()
# #     ]
# #     await update.message.reply_text(
# #         "دەزگایەک هەڵبژێرە:",
# #         reply_markup=InlineKeyboardMarkup(keyboard)
# #     )
# #     return ConversationHandler.END

# # # -----------------------------
# # # Handle group batch pages
# # # -----------------------------
# # async def group_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
# #     query = update.callback_query
# #     await query.answer()

# #     data = query.data.split(":")
# #     if data[0] == "group":
# #         group_name = data[1]
# #         page = int(data[2])
# #         batches = GROUPS[group_name]
# #         total_pages = (len(batches) - 1) // BATCHES_PER_PAGE + 1

# #         start_idx = page * BATCHES_PER_PAGE
# #         end_idx = min(start_idx + BATCHES_PER_PAGE, len(batches))
# #         page_batches = batches[start_idx:end_idx]

# #         keyboard = []
# #         name = context.user_data.get("name", "User")
# #         for batch in page_batches:
# #             url = f"{EMAIL_PAGE_URL}?batch={batch}&name={name}"
# #             keyboard.append([InlineKeyboardButton(batch.replace("_", " "), url=url)])

# #         nav_buttons = []
# #         if page > 0:
# #             nav_buttons.append(InlineKeyboardButton("⬅ ⏮️ Previous", callback_data=f"group:{group_name}:{page-1}"))
# #         if page < total_pages - 1:
# #             nav_buttons.append(InlineKeyboardButton("Next ⏭️ ➡", callback_data=f"group:{group_name}:{page+1}"))
# #         if nav_buttons:
# #             keyboard.append(nav_buttons)

# #         keyboard.append([InlineKeyboardButton("🏠 Back to groups", callback_data="back_to_groups")])

# #         await query.edit_message_text(
# #             f"{group_name} Batches (Page {page+1}/{total_pages}):",
# #             reply_markup=InlineKeyboardMarkup(keyboard)
# #         )

# #     elif data[0] == "back_to_groups":
# #         keyboard = [
# #             [InlineKeyboardButton(name, callback_data=f"group:{name}:0")]
# #             for name in GROUPS.keys()
# #         ]
# #         await query.edit_message_text(
# #             "Choose a group of recipients:",
# #             reply_markup=InlineKeyboardMarkup(keyboard)
# #         )

# # # -----------------------------
# # # Cancel
# # # -----------------------------
# # async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
# #     await update.message.reply_text("Cancelled. Use /start to begin again.")
# #     return ConversationHandler.END

# # # -----------------------------
# # # Main
# # # -----------------------------
# # def main():
# #     BOT_TOKEN = "8059209397:AAE6MChEXHtkuqi93WREXKBFSURA2MkjBOQ"

# #     app = ApplicationBuilder().token(BOT_TOKEN).build()

# #     conv_handler = ConversationHandler(
# #         entry_points=[CommandHandler("start", start)],
# #         states={ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)]},
# #         fallbacks=[CommandHandler("cancel", cancel)],
# #     )
# #     app.add_handler(conv_handler)
# #     app.add_handler(CallbackQueryHandler(group_page))

# #     print("Bot running…")
# #     app.run_polling()

# # if __name__ == "__main__":
# #     main()
# import logging
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import (
#     ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
#     ContextTypes, filters, CallbackQueryHandler
# )

# logging.basicConfig(level=logging.INFO)

# ASK_NAME = 0
# BATCHES_PER_PAGE = 10
# EMAIL_PAGE_URL = "https://email-kurdistan.github.io/kurds-email-bot/email_page.html"

# # Groups and batches with flags
# GROUPS = {
#     "🇺🇸 ئەنجومەنی پیرانی ئەمریکا": [f"senate_{i}" for i in range(1, 10)],
#     "🇪🇺 یەکێتی ئەوروپا": [f"eu_{i}" for i in range(1, 75)]
# }

# # -----------------------------
# # /start
# # -----------------------------
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text(
#         "بەخێربێیت بۆ بۆتی ئیمەیڵی \"پشتیوانی رۆژئاوا\" ✌️\n\n"
#         "ئەم بۆتە دروستکراوە بۆ ئەوەی بە شێوەیەکی سیستماتیک و کاریگەر، "
#         "نامەی ناڕەزایی و داواکاری گەلی کورد بگەیەنینە ئەندامانی پەرلەمانی ئەوروپا، "
#         "سیناتۆرەکانی ئەمریکا و ناوەندە دیپلۆماسییەکان.\n\n"
#         "📌 هەنگاوەکان:\n"
#         "1️⃣ ناوەکەت بنووسە: بۆ ئەوەی ئیمەیڵەکە بە فەرمی بە ناوی خۆتەوە بڕوات.\n"
#         "2️⃣ گرووپ هەڵبژێرە: ئەو دەزگایە دیاری بکە کە دەتەوێت فشار بخەیتە سەری.\n"
#         "3️⃣ ئیمەیڵ بنێرە: تەنها بە کلیکێک، ئیمەیڵێکی ئامادەکراو (Draft) لە مۆبایلەکەتدا دەکرێتەوە "
#         "و تەنها دوگمەی Send دەکەیت.\n\n"
#         "📝 دەنگت گرنگە، تکایە ناوەکەت  بە ئنگلیزی بنووسە بۆ دەستپێکردن:"
#     )
#     return ASK_NAME

# # -----------------------------
# # Receive name
# # -----------------------------
# async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data["name"] = update.message.text.strip()

#     # Show main groups
#     keyboard = [
#         [InlineKeyboardButton(name, callback_data=f"group:{name}:0")]
#         for name in GROUPS.keys()
#     ]
#     await update.message.reply_text(
#         "دەزگایەک هەڵبژێرە:",
#         reply_markup=InlineKeyboardMarkup(keyboard)
#     )
#     return ConversationHandler.END

# # -----------------------------
# # Handle group batch pages
# # -----------------------------
# async def group_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()

#     data = query.data.split(":")
#     if data[0] == "group":
#         group_name = data[1]
#         page = int(data[2])
#         batches = GROUPS[group_name]
#         total_pages = (len(batches) - 1) // BATCHES_PER_PAGE + 1

#         start_idx = page * BATCHES_PER_PAGE
#         end_idx = min(start_idx + BATCHES_PER_PAGE, len(batches))
#         page_batches = batches[start_idx:end_idx]

#         keyboard = []
#         name = context.user_data.get("name", "User")
#         for batch in page_batches:
#             url = f"{EMAIL_PAGE_URL}?batch={batch}&name={name}"
#             keyboard.append([InlineKeyboardButton(batch.replace("_", " "), url=url)])

#         nav_buttons = []
#         if page > 0:
#             nav_buttons.append(InlineKeyboardButton("⬅ ⏮️ Previous", callback_data=f"group:{group_name}:{page-1}"))
#         if page < total_pages - 1:
#             nav_buttons.append(InlineKeyboardButton("Next ⏭️ ➡", callback_data=f"group:{group_name}:{page+1}"))
#         if nav_buttons:
#             keyboard.append(nav_buttons)

#         keyboard.append([InlineKeyboardButton("🏠 Back to groups", callback_data="back_to_groups")])

#         await query.edit_message_text(
#             f"{group_name} Batches (Page {page+1}/{total_pages}):",
#             reply_markup=InlineKeyboardMarkup(keyboard)
#         )

#     elif data[0] == "back_to_groups":
#         keyboard = [
#             [InlineKeyboardButton(name, callback_data=f"group:{name}:0")]
#             for name in GROUPS.keys()
#         ]
#         await query.edit_message_text(
#             "Choose a group of recipients:",
#             reply_markup=InlineKeyboardMarkup(keyboard)
#         )

# # -----------------------------
# # Cancel
# # -----------------------------
# async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text("Cancelled. Use /start to begin again.")
#     return ConversationHandler.END

# # -----------------------------
# # Main
# # -----------------------------
# def main():
#     BOT_TOKEN = "8059209397:AAE6MChEXHtkuqi93WREXKBFSURA2MkjBOQ"

#     app = ApplicationBuilder().token(BOT_TOKEN).build()

#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler("start", start)],
#         states={ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)]},
#         fallbacks=[CommandHandler("cancel", cancel)],
#     )
#     app.add_handler(conv_handler)
#     app.add_handler(CallbackQueryHandler(group_page))

#     print("Bot running…")
#     app.run_polling()

# if __name__ == "__main__":
#     main()
