import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل رابط Mediafire أو Google Drive!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "mediafire.com" in url:
        await process_mediafire(update, context, url)
    elif "drive.google.com" in url:
        await process_google_drive(update, context, url)
    else:
        await update.message.reply_text("الرابط غير مدعوم حالياً.")

async def process_mediafire(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    await update.message.reply_text("جارٍ تحميل الملف من Mediafire...")

    download_link, original_filename = get_mediafire_direct_link(url)

    if not download_link:
        await update.message.reply_text("فشل استخراج رابط التحميل.")
        return

    response = requests.get(download_link, stream=True)
    with open(original_filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    await update.message.reply_document(document=open(original_filename, "rb"), filename=original_filename)
    os.remove(original_filename)

def get_mediafire_direct_link(url):
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        link = soup.find("a", {"id": "downloadButton"})["href"]
        filename = soup.find("div", {"class": "filename"}).text.strip()
        return link, filename
    except Exception:
        return None, None

async def process_google_drive(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    await update.message.reply_text("جارٍ تحميل الملفات من Google Drive...")

    links = get_drive_file_links(url)

    if not links:
        await update.message.reply_text("فشل في استخراج روابط الملفات من الفولدر.")
        return

    for file_name, download_url in links:
        try:
            response = requests.get(download_url, stream=True)
            with open(file_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            await update.message.reply_document(document=open(file_name, "rb"), filename=file_name)
            os.remove(file_name)
        except Exception as e:
            await update.message.reply_text(f"خطأ في تحميل ملف {file_name}: {e}")

def get_drive_file_links(folder_url):
    try:
        import re

        folder_id_match = re.search(r"folders/([a-zA-Z0-9_-]+)", folder_url)
        if not folder_id_match:
            return []

        folder_id = folder_id_match.group(1)

        api_url = f"https://drive.google.com/embeddedfolderview?id={folder_id}#grid"
        page = requests.get(api_url)
        soup = BeautifulSoup(page.text, "html.parser")

        links = []

        for div in soup.find_all("div", {"class": "flip-entry"}):
            try:
                data_id = div['id'].replace('entry-', '')
                name = div.find("div", {"class": "flip-entry-title"}).text.strip()
                download_link = f"https://drive.google.com/uc?id={data_id}&export=download"
                links.append((name, download_link))
            except Exception:
                continue

        return links

    except Exception:
        return []

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
