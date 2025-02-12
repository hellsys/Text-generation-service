# Use the official Python 3.10 slim image as the base
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/models/cache

ARG MODEL_PROVIDER
ARG HUGGINGFACE_TOKEN
RUN if [ "$MODEL_PROVIDER" = "mistral" ]; then \
    python -c "from huggingface_hub import snapshot_download; \
    import os; \
    snapshot_download(repo_id='mistralai/Mistral-7B-v0.1', cache_dir='/app/models/cache', use_auth_token=os.getenv('HUGGINGFACE_TOKEN'), resume_download=True, local_dir_use_symlinks=False)"; \
    fi

EXPOSE 8000

# RUN chmod +x entrypoint.sh
ENTRYPOINT ["/bin/sh", "entrypoint.sh"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]