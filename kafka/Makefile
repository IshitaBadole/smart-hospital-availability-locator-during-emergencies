VERSION=v1
DOCKERUSER=isba1563

#
# You should probably update the docker.io user if you update this
#

build:
	docker build -f Dockerfile-kafka-producer -t kafka-producer  .
	docker build -f Dockerfile-kafka-consumer -t kafka-consumer  .

#
# The following make rule labels the current docker image with the version
# number specified above and also the "latest" tag. It then pushes it to
# hub.docker.io
#
push:
	docker tag kafka-producer  $(DOCKERUSER)/kafka-producer:$(VERSION)
	docker push $(DOCKERUSER)/kafka-producer:$(VERSION)
	docker tag kafka-producer  $(DOCKERUSER)/kafka-producer:latest
	docker push $(DOCKERUSER)/kafka-producer:latest
	docker tag kafka-consumer  $(DOCKERUSER)/kafka-consumer:$(VERSION)
	docker push $(DOCKERUSER)/kafka-consumer:$(VERSION)
	docker tag kafka-consumer  $(DOCKERUSER)/kafka-consumer:latest
	docker push $(DOCKERUSER)/kafka-consumer:latest