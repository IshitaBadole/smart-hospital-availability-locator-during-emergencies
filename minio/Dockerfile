FROM python:3.10-slim

RUN pip3 install minio

COPY ./minio_setup.py /
COPY ./minio-config.yaml /
COPY models/xgb_model.json /
WORKDIR /
CMD  python3 /minio_setup.py