# syntax=docker/dockerfile:1

FROM python:3.16.0a1-slim-trixie@sha256:df293ba3b89f458e1aad6051b62ff1c4fad7b3b52b8147ae9cc4b667f9cf2741 AS builder

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --target /app/deps -r requirements.txt

# The runtime image has no locales; compile no_NO.UTF-8 (needed to sort æøå) here and copy it over
RUN apt-get update \
    && apt-get install -y --no-install-recommends locales \
    && mkdir -p /app/locale \
    && localedef -i nb_NO -f UTF-8 /app/locale/no_NO.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

FROM dhi.io/python:3.15.2-debian13@sha256: AS runtime

WORKDIR /app

ENV PYTHONPATH=/app/deps
ENV LOCPATH=/app/locale

COPY --from=builder /app/deps /app/deps
COPY --from=builder /app/locale /app/locale
COPY . .

USER 65532:65532

EXPOSE 5000

CMD [ "python", "-m", "gunicorn", "-c" , "gunicorn_config.py", "--no-control-socket", "main:app"]
