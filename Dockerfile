# ✅ Base Python image — stable, minimal
FROM python:3.11-slim

# 🛠️ Build tools for psycopg2 and more
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

# ✅ Install deps first for Docker caching
COPY requirements.txt constraints.txt ./
RUN pip install --upgrade pip setuptools wheel && \
    pip cache purge && \
    pip install --no-cache-dir -r requirements.txt -c constraints.txt

# ✅ Patch astdiff
RUN curl -sSL https://raw.githubusercontent.com/auntbertha/ASTdiff/master/astdiff/astdiff.py \
  -o /usr/local/lib/python3.11/site-packages/astdiff/astdiff.py && \
  echo "from .astdiff import compare_ast" >> /usr/local/lib/python3.11/site-packages/astdiff/__init__.py

# ✅ Copy all application code
COPY . .

# ✅ Create safe user and set ownership
RUN useradd -m devbot && chown -R devbot /app
USER devbot

# ✅ Expose API port
ENV PORT=8000
EXPOSE 8000

# ✅ Start Uvicorn in production mode
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]