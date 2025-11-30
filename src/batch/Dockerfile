FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements file
COPY ../../requirements.txt .

# Install CPU-only PyTorch first (for sentence-transformers)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy batch processing scripts
COPY scrap.py .
COPY traitement.py .
COPY pipeline.py .
COPY __init__.py .

# Set Python path
ENV PYTHONPATH=/app

# Run the complete pipeline
CMD ["python", "pipeline.py"]