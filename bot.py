import os
import pytesseract
from PIL import Image
import google.generativeai as genai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from dotenv import load_dotenv

# ========== CONFIGURATION ==========
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPEAT_CHAT_ID = int(os.getenv("REPEAT_CHAT_ID"))
REPEAT_THREAD_ID = int(os.getenv("REPEAT_THREAD_ID"))
GSHEET_NAME = os.getenv("GSHEET_NAME")
GSHEET_CRED_FILE = os.getenv("GSHEET_CRED_FILE")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# Optional: specify Tesseract path if needed
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ========== SETUP ==========
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="models/gemini-2.0-flash")

# ========== GOOGLE SHEETS LOGGER ==========
def setup_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GSHEET_CRED_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(GSHEET_NAME).sheet1
    return sheet

def log_to_gsheet(timestamp, category, summary, keyword, raw_text):
    try:
        sheet = setup_gsheet()
        sheet.append_row([
            timestamp.isoformat(),
            category,
            summary,
            keyword,
            raw_text[:100].replace('\n', ' ') + "..."
        ])
    except Exception as e:
        print(f"[Google Sheets Error] {e}")

# ========== OCR FUNCTION ==========
def extract_text_from_image(file_path):
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        return f"[OCR Error] {e}"

# ========== AI SUMMARIZER ==========
def analyze_text(raw_text: str):
    prompt = f"""
You are analyzing technical support messages from makers and developers.

Given the following input, classify it as either:
- 🔧 Product Usage
- 🤖 Project Help

Then summarize the question, and extract any product name or keyword mentioned.

Return in this format:
Category: ...
Summary: ...
Product/Keyword: ...

Text:
{raw_text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"[Gemini Error] {e}"

# ========== PARSE GEMINI RESPONSE ==========
def parse_summary(response_text):
    try:
        lines = response_text.splitlines()
        category = next((l.split(":", 1)[1].strip() for l in lines if "Category:" in l), "Unknown")
        summary = next((l.split(":", 1)[1].strip() for l in lines if "Summary:" in l), "")
        keyword = next((l.split(":", 1)[1].strip() for l in lines if "Product/Keyword:" in l), "")
        return category, summary, keyword
    except Exception:
        return "Unknown", response_text, ""

# ========== TELEGRAM HANDLER ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Received message")

    result = None
    raw_text = ""
    timestamp = update.message.date

    # Image
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        file_path = "temp_img.jpg"
        await photo_file.download_to_drive(file_path)
        raw_text = extract_text_from_image(file_path)
        os.remove(file_path)

    # Text
    elif update.message.text:
        raw_text = update.message.text.strip()

    if raw_text:
        result = analyze_text(raw_text)
        category, summary, keyword = parse_summary(result)

        # Log to Google Sheet
        log_to_gsheet(timestamp, category, summary, keyword, raw_text)

        # Post to Telegram topic
        await context.bot.send_message(
            chat_id=REPEAT_CHAT_ID,
            message_thread_id=REPEAT_THREAD_ID,
            text=result
        )

# ========== START BOT ==========
if __name__ == "__main__":
    print("Bot starting...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    app.run_polling()