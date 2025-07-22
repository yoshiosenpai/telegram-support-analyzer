from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import pytesseract
from PIL import Image
import requests
import os
import google.generativeai as genai

# SETUP: Your Gemini API Key
genai.configure(api_key="YAIzaSyBEyhNuh3k7e3Q3V4SGehzpTCiqVwBV5v0")

model = genai.GenerativeModel("gemini-pro")  # or "gemini-pro-vision" if image directly used

# OCR from image file
def extract_text_from_image(file_path):
    image = Image.open(file_path)
    return pytesseract.image_to_string(image)

# Use Gemini to classify & summarize
def analyze_text(text):
    prompt = f"""The following is a customer support message. 
Tag it as either 'Product Usage' or 'Project Help', then summarize it for the Repeat Pattern log.

Text:
{text}

Format:
Category: ...
Summary: ...
Product/Keyword: ...
"""
    response = model.generate_content(prompt)
    return response.text.strip()

# Telegram handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        file_path = "temp_img.jpg"
        await file.download_to_drive(file_path)
        extracted = extract_text_from_image(file_path)
        os.remove(file_path)
        result = analyze_text(extracted)
    elif update.message.text:
        result = analyze_text(update.message.text)
    else:
        return

    await context.bot.send_message(chat_id=2283022281, text=result)

app = ApplicationBuilder().token("7893151080:AAEQCLlq8D6KVWkXANE__DFdpKXP7JLQ6FE").build()
app.add_handler(MessageHandler(filters.ALL, handle_message))
app.run_polling()
