
# imports
import sys
import os
import redis
from minio import Minio, InvalidResponseError

# Defining Minio variables
minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

# Defining Redis Variables
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379



def separate_song_into_tracks(songhash):
    """Function that accepts the songhash, separates into tracks using demucs and dumps the tracks back into the output bucket in minio"""

    # Creating the Minio client object
    minioClient = Minio(minioHost,
               secure=False,
               access_key=minioUser,
               secret_key=minioPasswd)
    
    # Defining directories
    input_dir = os.path.join(os.getcwd(),"data", "input")
    output_dir = os.path.join(os.getcwd(),"data", "output")
    models_dir = os.path.join(os.getcwd(),"data", "models")
    
    # Check if the output bucket in minio is already created
    # If the "output" bucket does not exist, create it
    if not minioClient.bucket_exists("output"):
        print("Creating the output bucket on minio")
        minioClient.make_bucket("output")

    # Fetch the song from the songs bucket from minio
    file_path = os.path.join(input_dir, f"{songhash}.mp3")
    minioClient.fget_object("songs", f"{songhash}.mp3", file_path)
    print(f"Downloaded {songhash}.mp3 to {file_path}")

    # Defining the demucs command to separate the mp3 into tracks
    demucs_cmd = f"python3 -m demucs.separate --out /srv/data/output /srv/data/input/{songhash}.mp3 --mp3"
    
    # Running the demucs command
    print(demucs_cmd)
    os.system(demucs_cmd)

    # Fetch separated tracks from the output directory and put them into the output bucket in minio

    # Defining directory path where the track files will be stored by demucs
    output_track_dir = os.path.join(output_dir, "mdx_extra_q", songhash)
    
    # If the output directory exists
    if os.path.isdir(output_track_dir):
        # Iterating through all the track files
        for root, _, files in os.walk(output_track_dir):
            for file in files:
                # Defining the complete track file path
                track_file_path = os.path.join(output_track_dir, file)
                # Getting the type of track (bass, drum, vocals, etc) to append in the Minio object name
                track, _ = os.path.splitext(file)
                # Defining the name of the minio object to be uploaded
                minio_file_name = f"{songhash}-{track}.mp3"

                # Uploading the track to the output bucket in Minio
                minioClient.fput_object('output', minio_file_name, track_file_path)
                print(f"Uploaded {songhash}-{track}.mp3 to output bucket")


    # Remove songhash.mp3 from the songs bucket on minio after successfully separating it into tracks
    minioClient.remove_object("songs",f"{songhash}.mp3")

    
if __name__ == '__main__':

    while True:
        try:

            # Creating a redis client object
            redisClient = redis.StrictRedis(host=redisHost, port=redisPort, db=0)
            # BLPOP will block until an item is available in the list
            # Checking for items with the toWorker queue in the redis kist
            work = redisClient.blpop("toWorker", timeout=0)

            # Fetching the songhash from the item which will be at index 1
            songhash = work[1].decode('utf-8')
            print(songhash)

            # Separate mp3 into tracks and upload to Minio
            result = separate_song_into_tracks(songhash)


        except Exception as exp:
            print(f"Exception raised in log loop: {str(exp)}")
        sys.stdout.flush()
        sys.stderr.flush()