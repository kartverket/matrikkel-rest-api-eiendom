# syntax=docker/dockerfile:1

FROM python:3.15.2-slim-trixie@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928 AS builder

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
