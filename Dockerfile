FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if any needed for pillow/others)
# RUN apt-get update && apt-get install -y ...

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
