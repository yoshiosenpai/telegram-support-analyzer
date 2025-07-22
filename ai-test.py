import google.generativeai as genai

genai.configure(api_key="AIzaSyBEyhNuh3k7e3Q3V4SGehzpTCiqVwBV5v0")  # your valid API key

model = genai.GenerativeModel(model_name="models/gemini-2.0-flash")
response = model.generate_content("Summarize this: Raspberry Pi 5 is overheating")

print(response.text)
