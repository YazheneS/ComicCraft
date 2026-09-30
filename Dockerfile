FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
# Set GEMINI_API_KEY / HF_API_KEY with: docker run --env-file .env -p 8000:8000 comiccraft
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
