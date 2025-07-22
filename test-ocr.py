import pytesseract
from PIL import Image

# Optional if you didn't set Tesseract path globally
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

img = Image.open("sample_screenshot.jpg")
text = pytesseract.image_to_string(img)
print(text)
