# Base Python image – stable for SaaS Kernel ops
FROM python:3.11-slim

# Install full system dependencies (Postgres, SSL, Compiler, Build Tools)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements separately for Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Precompile critical dependencies to avoid on-server pip recursion
RUN pip install --no-cache-dir --upgrade \
    certifi==2023.7.22 \
    annotated-types==0.5.0 \
    astdiff==0.2.5

# Copy full application codebase
COPY . .

# Expose container port
EXPOSE 8000

# Kernel entrypoint
ENV DEV_MODE=1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
