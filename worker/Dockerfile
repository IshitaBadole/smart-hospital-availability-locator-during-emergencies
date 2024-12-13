
FROM python:3.7

WORKDIR /srv

COPY worker-server.py .

RUN pip3 install --upgrade minio redis requests geopy pandas 

CMD ["python3", "worker-server.py"]

