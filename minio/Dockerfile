FROM python:3.10-slim

RUN pip3 install minio

COPY ./minio_setup.py /
COPY ./minio-config.yaml /

RUN mkdir models
COPY models/xgb_model.json /models

RUN mkdir data
COPY data/final_hospital_data.csv /data
COPY data/mappings.json /data

WORKDIR /
CMD  python3 /minio_setup.py