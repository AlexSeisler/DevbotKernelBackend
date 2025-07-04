# ✅ Base Python image — stable, minimal, compatible with astdiff
FROM python:3.11-slim

# 🛠️ Build tools required for psycopg2 and others
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

# ✅ Pre-copy requirements for Docker cache layer
COPY requirements.txt constraints.txt ./

# ✅ Upgrade pip + prevent cache pollution
RUN pip install --upgrade pip setuptools wheel && \
    pip cache purge

# ✅ Install all dependencies deterministically
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt

# ✅ Patch astdiff (AST compare tooling)
RUN curl -sSL https://raw.githubusercontent.com/auntbertha/ASTdiff/master/astdiff/astdiff.py \
    -o /usr/local/lib/python3.11/site-packages/astdiff/astdiff.py && \
    echo "from .astdiff import compare_ast" >> /usr/local/lib/python3.11/site-packages/astdiff/__init__.py

# ✅ Copy full application code (layered after deps for cache efficiency)
COPY . .

# ✅ Optional: create non-root user for container safety
RUN useradd -m devbot && chown -R devbot /app
USER devbot

# ✅ Expose port for Render/local dev
EXPOSE 8000

# ✅ Runtime mode env flag (adjustable per container or agent role)
ENV DEV_MODE=1

# ✅ Entrypoint — uvicorn with hot reload (swap `--reload` in production)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
