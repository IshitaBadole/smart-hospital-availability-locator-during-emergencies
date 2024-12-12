# Imports

from flask import Flask, request, Response, send_file
import base64
import io
import json
from io import BytesIO
import os
from minio import Minio, InvalidResponseError
import uuid
import redis
import sys

# Initialize the Flask application
app = Flask(__name__)

# Logging variables
infoKey = "rest_server:[INFO]"
debugKey = "rest_server:[DEBUG]"

def log_debug(message):
    print("DEBUG:", message, file=sys.stdout)
    redisLog = redis.StrictRedis(host=redisHost, port=redisPort, db=2)
    redisLog.lpush('logging', f"{debugKey}:{message}")

def log_info(message):
    print("INFO:", message, file=sys.stdout)
    redisLog = redis.StrictRedis(host=redisHost, port=redisPort, db=2)
    redisLog.lpush('logging', f"{infoKey}:{message}")

# Defining Redis Variables
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/api/v1/query', methods=['POST'])
def query():
    json_data = request.json

    # Getting the hospital_name from the JSON payload
    hospital_name = json_data['hospital_name']

    # Creating the Redis client to connect to the redis worker queue
    redisClient = redis.StrictRedis(host=redisHost, 
                                    port=redisPort, 
                                    db=1)
    
    # Pusing the songhash to be processed to the Redis Queue
    log_info(f"Adding {hospital_name} to Redis queue")
    redisClient.rpush("toWorker", hospital_name)

    # Returing a response after successfully storing the mp3 on minio and adding the song to the Redis Queu
    return {
        "hospital_name": hospital_name, 
        "reason": f"{hospital_name} added to queue"
    }


@app.route("/api/v1/queue", methods = ["GET"])
def get_queue():
    # Creating the Redis client
    redisClient = redis.StrictRedis(host=redisHost, 
                                    port=redisPort, 
                                    db=1)
    queue = []
    
    # Get all elements from the Redis list with the toWorker key
    elements = redisClient.lrange('toWorker', 0, -1)    

    # Looping through all the elements and storing them in a list
    for element in elements:
        queue.append(element.decode('utf-8'))
    
    # Return the queue list in the response
    return {
        "queue": queue
    }

# start flask app
app.run(host="0.0.0.0", port=5000)