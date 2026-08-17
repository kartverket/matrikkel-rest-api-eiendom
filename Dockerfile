# syntax=docker/dockerfile:1

FROM python:3-alpine@sha256:05b2b8b732ecd268fee8727a369f936f022d1321b59befd13c30ede22769dcdc

EXPOSE 5000

WORKDIR /app

COPY requirements.txt requirements.txt

# Needed for psycopg2
RUN apk add build-base postgresql-dev

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "gunicorn", "-c" , "gunicorn_config.py", "main:app"]
