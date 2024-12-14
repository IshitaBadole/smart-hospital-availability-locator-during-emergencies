#!/bin/sh
#
# To kill the port-forward processes us e.g. "ps aux | grep port-forward"
# to identify the processes ids

kubectl apply -f redis/redis-deployment.yaml
kubectl apply -f redis/redis-service.yaml
kubectl port-forward --address 0.0.0.0 service/redis 6379:6379 &

helm repo add bitnami https://charts.bitnami.com/bitnami
helm install -f minio/minio-config.yaml -n minio-ns --create-namespace minio-proj bitnami/minio
kubectl apply -f minio/minio-deployment.yaml
kubectl apply -f minio/minio-external-service.yaml

kubectl port-forward -n minio-ns --address 0.0.0.0 service/minio-proj 9000:9000 &
kubectl port-forward -n minio-ns --address 0.0.0.0 service/minio-proj 9001:9001 &

# Run the kafka consumer to listen for producer messages
python3 kafka/kafka-consumer.py
# Run the kafka producer to simulate real-time messages
python3 kafka/kafka-producer.py

# Run the rest server locally in terminal
python3 rest/rest-server.py
# In another terminal window, 
python3 worker/worker-server.py