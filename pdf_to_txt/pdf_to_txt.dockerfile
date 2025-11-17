FROM python:3.10-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your script(s)
COPY . .

# Run your main script
CMD ["python", "pdf_to_txt.py"]