# Imports

from flask import Flask, request, Response, send_file
import jsonpickle
import base64
import io
import json
from io import BytesIO
import os
from minio import Minio, InvalidResponseError
import uuid
import redis

# Initialize the Flask application
app = Flask(__name__)

# Defining Minio variables
minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

# Defining Redis Variables
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379



@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/apiv1/separate', methods=['POST'])
def separate():
   
    # Getting the ecoded MP3 from the JSON payload
    data = jsonpickle.decode(request.data)
    encoded_mp3 = data["mp3"]
 
    # Decoding the encoded MP3
    decoded_mp3 = base64.b64decode(encoded_mp3)

    # Creating a hash for the song
    songhash = str(uuid.uuid1())

    # Filename to be used when storing the mp3 on Minio
    filename = f"{songhash}.mp3"
    # Name onf the bucket to store the MP3 in
    bucketname = "songs"

    # Creating the Minio client
    minioClient = Minio(minioHost,
               secure=False,
               access_key=minioUser,
               secret_key=minioPasswd)
    
    # Creating the Redis client
    redisClient = redis.StrictRedis(host=redisHost, 
                                    port=redisPort, 
                                    db=0)
    
    # Pusing the songhash to be processed to the Redis Queue
    redisClient.rpush("toWorker", songhash)

    # If the "songs" bucket does not exist, create it
    if not minioClient.bucket_exists(bucketname):
        minioClient.make_bucket(bucketname)
    
    try:
        # Storing the MP3 file in the dongs bucket
        result = minioClient.put_object(bucketname, filename, io.BytesIO(decoded_mp3), length = len(decoded_mp3))
    except InvalidResponseError as err:
        print("Error when adding files the first time")
        print(err)

    # Returing a response after successfully storing the mp3 on minio and adding the song to the Redis Queu
    return {
        "hash": songhash, 
        "reason": "Song enqueued for separation"
    }


@app.route("/apiv1/queue", methods = ["GET"])
def get_queue():
    # Creating the Redis client
    redisClient = redis.StrictRedis(host=redisHost, 
                                    port=redisPort, 
                                    db=0)
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

@app.route("/apiv1/track/<songhash>/<track>", methods = ['GET'])
def get_track(songhash, track):

    # Creating the Minio client
    minioClient = Minio(minioHost,
               secure=False,
               access_key=minioUser,
               secret_key=minioPasswd)

    # Getting the songhash-track.mp3 file from the output bucket on Minio
    response = minioClient.get_object("output", f"{songhash}-{track}.mp3")

    # return Response(
        #     response.data,
        #     mimetype='audio/mpeg',
        #     headers={
        #         'Content-Disposition': f'attachment; filename="{songhash}-{track}'
        #     }
        # )
    return send_file(
        io.BytesIO(response.data),
        mimetype='audio/mpeg',
        as_attachment=True,
        download_name=f"{songhash}-{track}.mp3"
    )
  
@app.route("/apiv1/remove/<songhash>/<track>", methods = ['DELETE'])
def delete_track(songhash, track):

    # Creating the Minio client
    minioClient = Minio(minioHost,
               secure=False,
               access_key=minioUser,
               secret_key=minioPasswd)
    
    # Removing the object from Minio
    minioClient.remove_object("output",f"{songhash}-{track}.mp3")

    return {
        "track": f"{songhash}-{track}.mp3", 
        "reason": f"{songhash}-{track}.mp3 has been deleted"
    }

    
# start flask app
app.run(host="0.0.0.0", port=5000)