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

# ========== CONFIGURATION ==========
TELEGRAM_TOKEN = "7893151080:AAEQCLlq8D6KVWkXANE__DFdpKXP7JLQ6FE"
REPEAT_CHAT_ID = "2283022281"
GEMINI_API_KEY = "AIzaSyBEyhNuh3k7e3Q3V4SGehzpTCiqVwBV5v0"

# Optional: specify Tesseract path if not in PATH
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="models/gemini-2.0-flash")

# ========== OCR FUNCTION ==========
def extract_text_from_image(file_path):
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        return f"[OCR Error] {e}"

# ========== AI SUMMARIZER ==========
def analyze_text(raw_text: str) -> str:
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

# ========== TELEGRAM MESSAGE HANDLER ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Chat ID:", update.effective_chat.id)
    print("Thread ID:", update.message.message_thread_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Got it!")

    result = None

    # Handle image
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        file_path = "temp_img.jpg"
        await photo_file.download_to_drive(file_path)
        text = extract_text_from_image(file_path)
        os.remove(file_path)
        result = analyze_text(text)

    # Handle plain text
    elif update.message.text:
        result = analyze_text(update.message.text)

    # Send result if we got one
    if result:
        await context.bot.send_message(chat_id=REPEAT_CHAT_ID, text=result)

# ========== START BOT ==========
if __name__ == "__main__":
    print("Bot starting...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    app.run_polling()
