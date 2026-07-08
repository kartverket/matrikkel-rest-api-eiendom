# syntax=docker/dockerfile:1

FROM python:3-alpine@sha256:26730869004e2b9c4b9ad09cab8625e81d256d1ce97e72df5520e806b1709f92

EXPOSE 5000

WORKDIR /app

COPY requirements.txt requirements.txt

# Needed for psycopg2
RUN apk add build-base postgresql-dev

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "gunicorn", "-c" , "gunicorn_config.py", "main:app"]
