# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy only requirements first for caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY bot.py .
COPY weekly_report.py .

# Default command (can be overridden)
CMD ["python", "bot.py"]
