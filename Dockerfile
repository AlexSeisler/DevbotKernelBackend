# Base Python image — stable for SaaS Kernel ops
FROM python:3.11-slim

# System dependencies for Rust + maturin + build tooling
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libssl-dev \
    pkg-config \
    git \
    rustc \
    cargo \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy only requirements first (for better build caching)
COPY requirements.txt .

# Upgrade pip + install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Now copy full application source
COPY . .

# Expose port
EXPOSE 8000

# Kernel entrypoint for Render
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
