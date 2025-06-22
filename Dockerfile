# ✅ Base Python image — stable, minimal, compatible with astdiff
FROM python:3.11-slim

# ✅ Install essential build + runtime tools (keeps final image lean)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ✅ Set working directory
WORKDIR /app

# ✅ Isolate dependency resolution to allow better Docker caching
COPY requirements.txt constraints.txt ./

# ✅ Force pip upgrade and prevent cached mismatches
RUN pip install --upgrade pip setuptools wheel && \
    pip cache purge

# ✅ Install all Python dependencies without cache, respecting version pins
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt
# Patch astdiff's broken top-level import
RUN echo "from .diff import compare_ast_strings" >> /usr/local/lib/python3.11/site-packages/astdiff/__init__.py

# ✅ Copy application code (after deps to leverage Docker layer caching)
COPY . .

# ✅ Port exposed for Render or containerized testing
EXPOSE 8000

# ✅ Environment flag (can be read in app via os.getenv("DEV_MODE"))
ENV DEV_MODE=1

# ✅ Entry point using uvicorn (not fastapi-cli), supports reload for local dev
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]