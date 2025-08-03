# Base image
FROM python:3

# Set working directory
WORKDIR /app

# Install system deps + clean
RUN apt-get update && apt-get install -y gcc && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port and run app
EXPOSE 5000
CMD ["python", "app.py"]
