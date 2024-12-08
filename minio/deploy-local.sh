#!/bin/sh

make build
make push

helm repo add bitnami https://charts.bitnami.com/bitnami
helm install -f ./minio-config.yaml -n minio-ns --create-namespace minio-proj bitnami/minio

kubectl apply -f ./minio-deployment.yaml
kubectl apply -f ./minio-external-service.yaml

kubectl port-forward --namespace minio-ns svc/minio-proj 9000:9000 &
kubectl port-forward --namespace minio-ns svc/minio-proj 9001:9001 &

ps aux | grep port-forward
# kill pid

kubectl port-forward --namespace minio-ns svc/minio-proj 9000:9000 &
kubectl port-forward --namespace minio-ns svc/minio-proj 9001:9001 &

# For uninstalling:

# kill processes
ps aux | grep port-forward
helm uninstall -n minio-ns minio-proj 
kubectl delete deployments.apps minio-deployment

