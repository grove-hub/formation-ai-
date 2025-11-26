FROM python:3.11-slim

# Avoid Python buffering and .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps (for lxml, etc. if needed by bs4)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
# (you can instead COPY a requirements.txt if you have one)
RUN pip install --no-cache-dir \
    requests \
    beautifulsoup4 \
    pypdf \
    python-docx \
    azure-identity \
    azure-storage-file-datalake

# Copy your scraper code into the image
COPY scrap.py /app/

# Run the scraper
CMD ["python", "scrap.py"]