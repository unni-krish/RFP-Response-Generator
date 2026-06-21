FROM python:3.11-slim

WORKDIR /app

# Install graphviz and basic fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz \
    fonts-liberation \
    fontconfig \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser and its system dependencies
RUN playwright install --with-deps chromium

COPY . .

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
