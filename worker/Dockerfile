FROM xserrat/facebook-demucs:latest

WORKDIR /srv

COPY worker-server.py .

RUN  pip3 install --upgrade minio redis requests

ENTRYPOINT ["python3", "worker-server.py"]

