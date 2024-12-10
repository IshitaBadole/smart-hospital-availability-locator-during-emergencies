
# imports
import sys
import os
import redis
from minio import Minio, InvalidResponseError
from geopy.geocoders import Nominatim


# Defining Redis Variables
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379

# Defining the geolocator object
geolocator = Nominatim(user_agent="my app")

if __name__ == '__main__':

    while True:
        try:

            # Creating a redis client object for work queue
            redis_queue = redis.StrictRedis(host=redisHost, port=redisPort, db=1)

            # Creating a redis client object for the redis cache containing cached predictions
            redis_cache = redis.StrictRedis(host=redisHost, port=redisPort, db=0)

            # BLPOP will block until an item is available in the list
            # Checking for items with the toWorker queue in the redis kist
            work = redis_queue.blpop("toWorker", timeout=0)

            # Fetching the queried hospital name from the item which will be at index 1
            hospital_name = work[1].decode('utf-8')
            
            # TODO: In the case of multiple matches for location add some 
            # further logic to narrow down to the correct one?
            location = geolocator.geocode(hospital_name , exactly_one=True)

            # Getting the cached prediction for the queried hospital name
            predicted_utilization_key = f"pred_utilization:{hospital_name}"
            predicted_utilization = float(redis_cache.get(predicted_utilization_key))

            print(f"Forecasted utilization for {hospital_name} is {predicted_utilization}")

        except Exception as exp:
            print(f"Exception raised in log loop: {str(exp)}")
        sys.stdout.flush()
        sys.stderr.flush()