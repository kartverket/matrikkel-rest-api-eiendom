# syntax=docker/dockerfile:1

FROM python:3-alpine@sha256:5aa3872d12a059e22fda84b7556a8d103dc9dff314d044d2d47d5785378c5856

EXPOSE 5000

WORKDIR /app

COPY requirements.txt requirements.txt

# Needed for psycopg2
RUN apk add build-base postgresql-dev

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "gunicorn", "-c" , "gunicorn_config.py", "--no-control-socket", "main:app"]
