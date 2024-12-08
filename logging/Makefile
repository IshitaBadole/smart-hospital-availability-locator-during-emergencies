VERSION=v1
DOCKERUSER=isba1563

#
# You should probably update the docker.io user if you update this
#

build:
	docker build -f Dockerfile -t logs  .

#
# The following make rule labels the current docker image with the version
# number specified above and also the "latest" tag. It then pushes it to
# hub.docker.io
#
push: build
	docker tag logs  $(DOCKERUSER)/logs:$(VERSION)
	docker push $(DOCKERUSER)/logs:$(VERSION)
	docker tag logs  $(DOCKERUSER)/logs:latest
	docker push $(DOCKERUSER)/logs:latest