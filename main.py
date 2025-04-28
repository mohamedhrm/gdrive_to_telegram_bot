import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "7508643303:AAH_PN1mOZS5nWOzm9rHqAPPrn-Q2PUYonY"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً! 📥\nابعتلي رابط Google Drive عشان أنزله لك!")

async def download_gdrive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "drive.google.com" not in url:
        await update.message.reply_text("الرابط ده مش رابط Google Drive! حاول تبعت رابط صحيح.")
        return

    file_id = None
    if "id=" in url:
        file_id = url.split("id=")[1].split("&")[0]
    elif "/d/" in url:
        file_id = url.split("/d/")[1].split("/")[0]

    if not file_id:
        await update.message.reply_text("مقدرتش أحدد الملف من الرابط! تأكد إنه صحيح.")
        return

    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

    try:
        response = requests.get(download_url)
        response.raise_for_status()

        await update.message.reply_document(response.content, filename="gdrive_file")
    except Exception as e:
        await update.message.reply_text(f"حصل خطأ أثناء التحميل: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_gdrive))

    app.run_polling()

if __name__ == '__main__':
    main()
