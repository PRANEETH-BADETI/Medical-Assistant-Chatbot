# Use Python 3.10 for maximum ML compatibility
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (Required for PostgreSQL & generic build tools)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the server requirements from your project
COPY server/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire server folder into the container
COPY server/ ./server/

# Copy the startup script (we will create this next)
COPY start.sh .
RUN chmod +x start.sh

# Create the upload directory so the app doesn't crash
RUN mkdir -p server/uploaded_docs

# Expose the port Hugging Face expects
EXPOSE 7860

# Run the startup script
CMD ["./start.sh"]