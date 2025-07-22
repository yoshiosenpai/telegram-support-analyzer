import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime, timedelta
from telegram import Bot
import asyncio
import textwrap
import pytz
from dotenv import load_dotenv


# ========== CONFIG ==========
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPEAT_CHAT_ID = int(os.getenv("REPEAT_CHAT_ID"))
REPEAT_THREAD_ID = int(os.getenv("REPEAT_THREAD_ID"))
GSHEET_NAME = os.getenv("GSHEET_NAME")
GSHEET_CRED_FILE = os.getenv("GSHEET_CRED_FILE")

# ========== Connect to Google Sheets ==========
def load_weekly_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GSHEET_CRED_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(GSHEET_NAME).sheet1
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df

# ========== Analyze Data ==========
def analyze_week(df):
    today = datetime.now(pytz.UTC)
    start = today - timedelta(days=7)
    df_week = df[df["timestamp"] >= start]

    keywords = df_week["Product_Keyword"].dropna().str.split(r",\s*").explode().value_counts()
    categories = df_week["Category"].value_counts()
    summaries = df_week["Summary"].value_counts()
    return keywords, categories, summaries, start, today

# ========== Format Summary Message ==========
def generate_summary_msg(keywords, categories, summaries, start, end):
    msg = f"""🧠 *Weekly Trend Summary* ({start.strftime('%b %d')} – {end.strftime('%b %d')})

🔑 *Top Keywords:*
{textwrap.dedent(chr(10).join([f"- {kw} → {count} mention(s)" for kw, count in keywords.items()]) or "No keyword data.")}

🗂️ *Top Categories:*
{textwrap.dedent(chr(10).join([f"- {cat} → {count} message(s)" for cat, count in categories.items()]) or "No category data.")}

📝 *Frequent Summaries:*
{textwrap.dedent(chr(10).join([f"- {s} → {count}x" for s, count in summaries.items()][:3]) or "No repeated summaries.")}

👉 Use this to prioritize next week's content!
"""
    return msg.strip()

# ========== Send to Telegram ==========
async def send_telegram_summary(message):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(
        chat_id=REPEAT_CHAT_ID,
        message_thread_id=REPEAT_THREAD_ID,
        text=message,
        parse_mode="Markdown"
    )

# ========== Run Script ==========
if __name__ == "__main__":
    df = load_weekly_data()
    keywords, categories, summaries, start, end = analyze_week(df)
    report = generate_summary_msg(keywords, categories, summaries, start, end)
    print("Sending summary to Telegram...")
    asyncio.run(send_telegram_summary(report))
