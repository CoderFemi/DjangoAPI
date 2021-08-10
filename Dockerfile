FROM python:3.9-alpine
LABEL "maintainer"="Coder Femi"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir /app
WORKDIR /app
COPY ./app /app

# Create a user with limited access priviledge.
RUN adduser -D user
USER user