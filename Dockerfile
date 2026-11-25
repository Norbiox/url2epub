# Debian trixie ships pandoc 3.x (needed for --epub-title-page / --split-level)
FROM python:3.13-slim-trixie
RUN apt-get update && apt-get install -y --no-install-recommends pandoc ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
USER nobody
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
