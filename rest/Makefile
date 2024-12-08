VERSION=v2
DOCKERUSER=vera5660

build:
	docker build -f Dockerfile-rest -t demucs-rest .

push:build
	docker tag demucs-rest $(DOCKERUSER)/demucs-rest:$(VERSION)
	docker push $(DOCKERUSER)/demucs-rest:$(VERSION)
	docker tag demucs-rest $(DOCKERUSER)/demucs-rest:latest
	docker push $(DOCKERUSER)/demucs-rest:latest
