VERSION=v1
DOCKERUSER=isba1563

build:
	docker build -t minio .

push:
	docker tag minio $(DOCKERUSER)/minio:$(VERSION)
	docker push $(DOCKERUSER)/minio:$(VERSION)
	docker tag minio $(DOCKERUSER)/minio:latest
	docker push $(DOCKERUSER)/minio:latest