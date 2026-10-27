# syntax=docker/dockerfile:1
# Сборка: docker build -f docker/Dockerfile .

FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npx vite build --outDir /web/dist --emptyOutDir

FROM python:3.12-slim-bookworm AS models
RUN pip install --no-cache-dir huggingface_hub==2.3.0
# ревизии моделей зафиксированы — калибровка (calibration.json) посчитана именно на них
RUN python -c "from huggingface_hub import snapshot_download as d; \
[d(m, revision=r, local_dir='/models/' + m.split('/')[1], allow_patterns=['*.json', 'pytorch_model.bin', '*.txt']) \
 for m, r in [('facebook/wav2vec2-lv-60-espeak-cv-ft', 'ae45363bf3413b374fecd9dc8bc1df0e24c3b7f4'), \
              ('facebook/wav2vec2-xlsr-53-espeak-cv-ft', '2c733782da5604684829819a5eb744c193fe9398'), \
              ('microsoft/wavlm-base-plus-sv', 'feb593a6c23c1cc3d9510425c29b0a14d2b07b1e')]]"

FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 DATA_DIR=/data MODELS_DIR=/models CHROMIUM_BIN=chromium HF_HUB_OFFLINE=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg chromium fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.1
# модели — отдельным слоем до кода, чтобы обновления кода не перекачивали гигабайты
COPY --from=models /models /models
WORKDIR /app
COPY backend/pyproject.toml ./
RUN mkdir vymova && touch vymova/__init__.py && pip install ".[ml]" && rm -rf vymova
COPY backend/vymova ./vymova
COPY --from=web /web/dist ./vymova/static
RUN pip install --no-deps .
EXPOSE 8765
VOLUME /data
CMD ["vymova", "serve", "--host", "0.0.0.0"]
