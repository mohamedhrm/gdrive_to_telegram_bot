import os
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# إعداد المتغيرات البيئية
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
SERVICE_ACCOUNT_FILE = "/etc/secrets/service_account.json"

# إنشاء خدمة Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل رابط Google Drive 📂")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "drive.google.com" not in url:
        await update.message.reply_text("❌ الرابط ليس من Google Drive!")
        return

    if "/folders/" in url:
        await update.message.reply_text("🔍 جاري تحميل محتويات المجلد...")
        await download_folder(url, context)
    else:
        await update.message.reply_text("🔍 جاري تحميل الملف...")
        await download_file(url, context)

def extract_file_id(url):
    if "id=" in url:
        return url.split("id=")[-1].split("&")[0]
    elif "/d/" in url:
        return url.split("/d/")[1].split("/")[0]
    return None

def extract_folder_id(url):
    if "folders/" in url:
        return url.split("folders/")[1].split("?")[0]
    return None

async def download_file(url, context):
    try:
        file_id = extract_file_id(url)
        file_metadata = drive_service.files().get(fileId=file_id).execute()
        filename = file_metadata['name']

        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)
        await context.bot.send_document(chat_id=CHANNEL_ID, document=fh, filename=filename)

    except Exception as e:
        print("Error:", e)
        await context.bot.send_message(chat_id=CHANNEL_ID, text="❌ حدث خطأ أثناء تحميل الملف.")

async def download_folder(url, context):
    try:
        folder_id = extract_folder_id(url)
        query = f"'{folder_id}' in parents and trashed = false"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            await context.bot.send_message(chat_id=CHANNEL_ID, text="📂 المجلد فارغ أو لا يمكن الوصول إليه.")
            return

        await context.bot.send_message(chat_id=CHANNEL_ID, text=f"📁 عدد الملفات: {len(items)}. جاري التحميل...")

        for item in items:
            file_id = item['id']
            filename = item['name']
            request = drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()

            fh.seek(0)
            await context.bot.send_document(chat_id=CHANNEL_ID, document=fh, filename=filename)

    except Exception as e:
        print("Error:", e)
        await context.bot.send_message(chat_id=CHANNEL_ID, text="❌ حدث خطأ أثناء تحميل المجلد.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
