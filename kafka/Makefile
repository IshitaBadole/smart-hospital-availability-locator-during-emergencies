VERSION=v1
DOCKERUSER=isba1563

#
# You should probably update the docker.io user if you update this
#

build:
	docker build -f Dockerfile -t kafka_producer  .
	docker build -f Dockerfile -t kafka_consumer  .

#
# The following make rule labels the current docker image with the version
# number specified above and also the "latest" tag. It then pushes it to
# hub.docker.io
#
push:
	docker tag kafka_producer  $(DOCKERUSER)/kafka_producer:$(VERSION)
	docker push $(DOCKERUSER)/kafka_producer:$(VERSION)
	docker tag kafka_producer  $(DOCKERUSER)/kafka_producer:latest
	docker push $(DOCKERUSER)/kafka_producer:latest
	docker tag kafka_consumer  $(DOCKERUSER)/kafka_consumer:$(VERSION)
	docker push $(DOCKERUSER)/kafka_consumer:$(VERSION)
	docker tag kafka_consumer  $(DOCKERUSER)/kafka_consumer:latest
	docker push $(DOCKERUSER)/kafka_consumer:latest