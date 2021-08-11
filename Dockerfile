FROM python:3.9-alpine
LABEL "maintainer"="Coder Femi"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt

# update flag means to update the registry before adding the client
# no-cache flag means registry index should not be cached i.e. no dependencies left on the docker image.
RUN apk add --update --no-cache postgresql-client

# virtual flag sets up an alias that will be used to remove the temporary dependencies later
RUN apk add --update --no-cache --virtual .tmp-build-deps \
    gcc libc-dev linux-headers postgresql-dev

RUN pip install -r /requirements.txt
RUN apk del .tmp-build-deps

RUN mkdir /app
WORKDIR /app
COPY ./app /app

# Create a user with limited access priviledge.
RUN adduser -D user
USER user