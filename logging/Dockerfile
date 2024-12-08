FROM python:3.6-alpine
LABEL MAINTAINER="isba1563@colorado.edu"

RUN  pip3 install redis

WORKDIR /srv
COPY    logs.py /srv
CMD [ "python3", "logs.py"]
