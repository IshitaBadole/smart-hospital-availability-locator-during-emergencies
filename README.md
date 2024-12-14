# SHALE : Smart Hospital Availability Locator for Emergencies

## Project Members:
- Ishita Badole
- Anirudh Ragam

## Create a venv and install dependencies

`python3 -m venv venv`

`pip3 install -r requirements.txt`

## Kafka

To run the kafka producer and consumer first start kafka and zookeeper

1. Install kafka:
    `brew install kafka`

2. To start kafka now and restart at login:

    `brew services start kafka`

    Or, if you don't want/need a background service you can just run:
    `/opt/homebrew/opt/kafka/bin/kafka-server-start /opt/homebrew/etc/kafka/server.properties`

3. Start the Zookeeper service
    `brew services start zookeeper`

## Deploy

Run `sh deploy-all.sh` to setup the application

## Test

Run `python3 test-queries.py` to test the application with sample queries.