# syntax=docker/dockerfile:1

FROM python:3-alpine@sha256:c6ead215bfd31f1e433d968853b7a769989117115b728874824e6c0a27cb96fc

EXPOSE 5000

WORKDIR /app

COPY requirements.txt requirements.txt

# Needed for psycopg2
RUN apk add build-base postgresql-dev

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "gunicorn", "-c" , "gunicorn_config.py", "--no-control-socket", "main:app"]
