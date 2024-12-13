VERSION=v2
DOCKERUSER=isba1563

build:
	docker build -f Dockerfile-rest -t rest .

push:build
	docker tag rest $(DOCKERUSER)/rest:$(VERSION)
	docker push $(DOCKERUSER)/rest:$(VERSION)
	docker tag rest $(DOCKERUSER)/rest:latest
	docker push $(DOCKERUSER)/rest:latest
