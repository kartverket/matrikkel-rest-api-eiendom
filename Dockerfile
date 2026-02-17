# syntax=docker/dockerfile:1

FROM python:3-alpine@sha256:faee120f7885a06fcc9677922331391fa690d911c020abb9e8025ff3d908e510

EXPOSE 5000

WORKDIR /app

COPY requirements.txt requirements.txt

# Needed for psycopg2
RUN apk add build-base postgresql-dev

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "gunicorn", "-c" , "gunicorn_config.py", "main:app"]
