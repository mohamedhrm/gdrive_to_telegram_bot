import os
import asyncio
import aiofiles
import gdown
from telegram import Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # مثلا "-1002558520064"

bot = Bot(token=BOT_TOKEN)

async def start(update, context):
    await update.message.reply_text("ارسل رابط Google Drive وسأقوم بتحميله ورفعه ✅")

async def handle_message(update, context):
    url = update.message.text.strip()

    if not ("drive.google.com" in url):
        await update.message.reply_text("الرجاء إرسال رابط Google Drive صحيح 📎")
        return

    await update.message.reply_text("جاري التحميل من Google Drive... ⏳")

    try:
        # تحديد اسم الملف أو الفولدر
        output_name = "downloaded_content"

        # تحميل الملف أو الفولدر
        gdown.download_folder(url, output=output_name, quiet=True, use_cookies=False)

        # رفع كل الملفات
        for root, dirs, files in os.walk(output_name):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                await upload_file(file_path)
                os.remove(file_path)

        await update.message.reply_text("تم الرفع بنجاح ✅✅")

    except Exception as e:
        await update.message.reply_text(f"حدث خطأ: {e}")

async def upload_file(file_path):
    async with aiofiles.open(file_path, "rb") as f:
        file_data = await f.read()
        await bot.send_document(
            chat_id=CHANNEL_ID,
            document=file_data,
            filename=os.path.basename(file_path),
            caption="📂 ملف مرفوع من Google Drive"
        )

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
