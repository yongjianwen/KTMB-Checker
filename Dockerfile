# Use a lightweight Python image
FROM python:3.12-slim

WORKDIR /app
COPY . .

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Expose port 7860 (required for Hugging Face)
EXPOSE 7860

# Run the app
CMD ["gunicorn", "-b", "0.0.0.0:7860", "bot:app"]
