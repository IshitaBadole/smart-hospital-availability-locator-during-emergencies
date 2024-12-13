VERSION=v1
DOCKERUSER=isba1563

build:
	docker build -f Dockerfile -t worker .
push:build
	docker tag worker $(DOCKERUSER)/worker:$(VERSION)
	docker push $(DOCKERUSER)/worker:$(VERSION)
	docker tag worker $(DOCKERUSER)/worker:latest
	docker push $(DOCKERUSER)/worker:latest
