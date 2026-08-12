# syntax=docker/dockerfile:1

FROM python:3-alpine@sha256:a1321512d6a287428c50dcdf2ab3857761127e03a23b1f648e9c1c0de59288f8

EXPOSE 5000

WORKDIR /app

COPY requirements.txt requirements.txt

# Needed for psycopg2
RUN apk add build-base postgresql-dev

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "gunicorn", "-c" , "gunicorn_config.py", "main:app"]
