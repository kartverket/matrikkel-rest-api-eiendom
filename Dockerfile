# syntax=docker/dockerfile:1

FROM python:3.15.2-slim-trixie@sha256:8c13a3f37a6a5b71498228e902c4b9f51c1f7900d49fabf71f9a650c6120e0d0 AS builder

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --target /app/deps -r requirements.txt

# The runtime image has no locales; compile no_NO.UTF-8 (needed to sort æøå) here and copy it over
RUN apt-get update \
    && apt-get install -y --no-install-recommends locales \
    && mkdir -p /app/locale \
    && localedef -i nb_NO -f UTF-8 /app/locale/no_NO.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

FROM dhi.io/python:3.15.2-debian13@sha256:d18cc222a379b8caa077ce41db24b77e351934dc4c4966d52225dfe40efa1e61 AS runtime

WORKDIR /app

ENV PYTHONPATH=/app/deps
ENV LOCPATH=/app/locale

COPY --from=builder /app/deps /app/deps
COPY --from=builder /app/locale /app/locale
COPY . .

EXPOSE 5000

CMD [ "python", "-m", "gunicorn", "-c" , "gunicorn_config.py", "--no-control-socket", "main:app"]
