import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from bs4 import BeautifulSoup
import json

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")  # مثال: '-1002558520064'

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

async def download_file(url, context):
    try:
        file_id = extract_file_id(url)
        if not file_id:
            await context.bot.send_message(chat_id=CHANNEL_ID, text="❌ لم أستطع استخراج معرف الملف.")
            return

        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        session = requests.Session()
        response = session.get(download_url, stream=True)

        if "Content-Disposition" in response.headers:
            filename = response.headers["Content-Disposition"].split("filename=")[1].strip("\"'")
        else:
            filename = "file_from_drive"

        file_path = os.path.join("/tmp", filename)

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)

        await context.bot.send_document(chat_id=CHANNEL_ID, document=open(file_path, "rb"), filename=filename)
        os.remove(file_path)

    except Exception as e:
        print("Error downloading file:", e)
        await context.bot.send_message(chat_id=CHANNEL_ID, text="❌ حدث خطأ أثناء تحميل الملف.")

async def download_folder(folder_url, context):
    try:
        folder_id = extract_folder_id(folder_url)
        if not folder_id:
            await context.bot.send_message(chat_id=CHANNEL_ID, text="❌ لم أستطع استخراج معرف المجلد.")
            return

        page_url = f"https://drive.google.com/drive/folders/{folder_id}"
        session = requests.Session()
        response = session.get(page_url)

        soup = BeautifulSoup(response.text, "html.parser")
        scripts = soup.find_all("script")

        files = []
        data = None

        for script in scripts:
            if "window['_DRIVE_ivd']" in script.text:
                start = script.text.find("[[")
                end = script.text.find("]]") + 2
                data = script.text[start:end]
                break

        if not data:
            await context.bot.send_message(chat_id=CHANNEL_ID, text="❌ لم أتمكن من قراءة ملفات المجلد.")
            return

        # استخراج الملفات
        data = json.loads(data)
        for item in data:
            if len(item) > 3:
                file_id = item[0]
                filename = item[2]
                files.append((file_id, filename))

        await context.bot.send_message(chat_id=CHANNEL_ID, text=f"📂 تم العثور على {len(files)} ملف داخل المجلد. جاري التحميل...")

        for file_id, filename in files:
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            file_path = os.path.join("/tmp", filename)
            res = session.get(download_url, stream=True)

            with open(file_path, "wb") as f:
                for chunk in res.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)

            await context.bot.send_document(chat_id=CHANNEL_ID, document=open(file_path, "rb"), filename=filename)
            os.remove(file_path)

    except Exception as e:
        print("Error downloading folder:", e)
        await context.bot.send_message(chat_id=CHANNEL_ID, text="❌ حدث خطأ أثناء تحميل المجلد.")

def extract_file_id(url):
    if "id=" in url:
        return url.split("id=")[-1].split("&")[0]
    elif "/d/" in url:
        return url.split("/d/")[1].split("/")[0]
    else:
        return None

def extract_folder_id(url):
    if "folders/" in url:
        return url.split("folders/")[1].split("?")[0]
    else:
        return None

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))

    # ضروري: استقبال أي نص مش أمر
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
