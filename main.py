import os
import asyncio
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = -1002558520064  # اكتب هنا ID القناة اللي قولتلي عليه

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل رابط Google Drive أو ملف مباشر!")

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith("http"):
        await update.message.reply_text("ارسل لينك صالح.")
        return

    filename = url.split("/")[-1].split("?")[0]
    filename = filename.replace("%20", " ")  # تصحيح لو فيه مسافات مرمزة

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    file_data = await resp.read()
                    await context.bot.send_document(
                        chat_id=CHANNEL_ID,
                        document=file_data,
                        filename=filename,
                        caption=f"تم رفع الملف: {filename}"
                    )
                    await update.message.reply_text(f"✅ تم رفع الملف: {filename}")
                else:
                    await update.message.reply_text("فشل التحميل، حاول رابط آخر.")
    except Exception as e:
        await update.message.reply_text(f"خطأ أثناء التحميل: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_and_send))
    app.run_polling()

if __name__ == "__main__":
    main()
