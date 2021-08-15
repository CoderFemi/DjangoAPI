FROM python:3.9-alpine
LABEL "maintainer"="Coder Femi"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt

# Add permanent dependencies.
# update flag means to update the registry before adding the client
# no-cache flag means registry index should not be cached i.e. no dependencies left on the docker image.
RUN apk add --update --no-cache postgresql-client jpeg-dev

# Add temporary dependencies.
# virtual flag sets up an alias that will be used to remove the temporary dependencies later
RUN apk add --update --no-cache --virtual .tmp-build-deps \
    gcc libc-dev linux-headers postgresql-dev musl-dev zlib zlib-dev

RUN pip install -r /requirements.txt

# Remove temporary dependencies.
RUN apk del .tmp-build-deps

RUN mkdir /app
WORKDIR /app
COPY ./app /app

# Create static file directories. -p flag creates the specified directories, if non-existent.
RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static

# Create a user with limited access priviledge.
RUN adduser -D user
# Assign specific file access to user -R flag recursively assigns all subdirectories. chown i.e. change ownership.
RUN chown -R user:user /vol/
# Assign full permissions for owner, read-only & execute for others.
RUN chmod -R 755 /vol/web
# Switch to user.
USER user