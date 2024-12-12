# imports
import os
import sys

import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import json
import redis
from minio import InvalidResponseError, Minio

# Defining Minio Variables
minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

# bucket variables
data_bucket = "data"

# Creating a minio client object
minio_client = Minio(
    minioHost, secure=False, access_key=minioUser, secret_key=minioPasswd
)

# Downloading hospital_data.csv from Minio object storage
minio_client.fget_object(
    data_bucket, f"hospital_data.csv", os.path.join(os.getcwd(), "hospital_data.csv")
)
# Reading hospital data and storing it in a dataframe
hospital_data = pd.read_csv(os.path.join(os.getcwd(), "hospital_data.csv"), index_col=0)

# Defining Redis Variables
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379

# Defining the geolocator object
geolocator = Nominatim(user_agent="my app")

# Logging variables
infoKey = "worker:[INFO]"
debugKey = "worker:[DEBUG]"


def log_debug(message):
    print("DEBUG:", message, file=sys.stdout)
    redisLog = redis.StrictRedis(host=redisHost, port=redisPort, db=2)
    redisLog.lpush("logging", f"{debugKey}:{message}")


def log_info(message):
    print("INFO:", message, file=sys.stdout)
    redisLog = redis.StrictRedis(host=redisHost, port=redisPort, db=2)
    redisLog.lpush("logging", f"{infoKey}:{message}")


def get_distance(lat1, lng1, lat2, lng2):
    return geodesic((lat1, lng1), (lat2, lng2)).miles


# define the n closest hospitals to return
n_closest = 6

# Define a maximum utilization above which the worker returns
# n-closest hospitals
max_utilization = 80


def get_predicted_utilization(redis_cache, hospital_name):
    predicted_utilization_key = f"pred_utilization:{hospital_name}"
    predicted_utilization = redis_cache.get(predicted_utilization_key)
    predicted_utilization = (
        float(predicted_utilization) if predicted_utilization else "Not Found"
    )
    return predicted_utilization


if __name__ == "__main__":

    while True:
        try:

            # Creating a redis client object for work queue
            redis_queue = redis.StrictRedis(host=redisHost, port=redisPort, db=1)

            # Creating a redis client object for the redis cache containing cached predictions
            redis_cache = redis.StrictRedis(host=redisHost, port=redisPort, db=0)

            # Creating a redis client object for the redis cache containing all the worker results
            redis_output = redis.StrictRedis(host=redisHost, port=redisPort, db=3)

            # BLPOP will block until an item is available in the list
            # Checking for items with the toWorker queue in the redis kist
            work = redis_queue.blpop("toWorker", timeout=0)
            task = json.loads(work[1]) 

            # Fetching the task ID and queried hospital name from task data
            task_id = task["id"]
            hospital_name = task['hospital_name']
            log_info(f"Processing task {task_id}. Queried hospital : {hospital_name}")

            log_debug(f"Fetching location for {hospital_name}")
            location = geolocator.geocode(hospital_name, exactly_one=True)

            queried_hospital_row = hospital_data[
                hospital_data["hospital_name"] == hospital_name
            ]

            # Getting the latitude and the longitude of the queried hospital
            queried_lat = queried_hospital_row["lat"].iloc[0]
            queried_lng = queried_hospital_row["lng"].iloc[0]

            print(f"queried_lat {type(queried_lat)}")
            print(f"queried_lng {queried_lng}")

            # get data of hospitals in the same state as the queried hospital
            same_state_df = hospital_data[
                hospital_data["state"] == queried_hospital_row["state"].values[0]
            ]

            # call get_distance on each row in same_state_df
            same_state_df["distance"] = same_state_df.apply(
                lambda x: get_distance(
                    x["lat"],
                    x["lng"],
                    queried_lat,
                    queried_lng,
                ),
                axis=1,
            )

            # sort same_state_df by distance
            same_state_df.sort_values(by=["distance"])

            closest_hospitals_df = same_state_df.head(n_closest)
            log_info(f"closest_hospitals_df {closest_hospitals_df}")

            response = {}

            # Getting the cached prediction for the queried hospital name
            predicted_utilization = get_predicted_utilization(redis_cache, hospital_name)
            log_info(
                f"Forecasted utilization for {hospital_name} is {predicted_utilization}"
            )

            closest_hospitals_utilizations = dict()
            if (
                type(predicted_utilization) == float
                and predicted_utilization > max_utilization
            ):
                log_info(
                    f"Forecasted utilization for {hospital_name} is > {max_utilization}. Looking for alternatives."
                )
                candidates = []
                for index, row in closest_hospitals_df.iterrows():
                    candidate_hospital = row["hospital_name"]
                    if candidate_hospital != hospital_name:
                        nearby_predicted_utilization = get_predicted_utilization(
                            redis_cache, hospital_name=candidate_hospital
                        )
                        if type(nearby_predicted_utilization) == float:
                            log_info(
                                f"Forecasted utilization for {candidate_hospital} is {nearby_predicted_utilization}"
                            )
                            candidates.append(
                                (candidate_hospital, nearby_predicted_utilization)
                            )

                sorted_candidates = sorted(candidates, key=lambda x: x[1])

                log_info(f"{sorted_candidates[0]}")

                # Getting hospital_name, address, forecasted utilization
                final_hospital = sorted_candidates[0][0]
                forecasted_utilization = sorted_candidates[0][1]

                # Getting the address of the recommended hospital
                address = hospital_data[hospital_data['hospital_name'] == final_hospital]['address'].iloc[0]
                print(f"final hospital address : {address}")


                worker_result = {
                    "recommended_hospital" : final_hospital,
                    "address" : address,
                    "forecasted_utilization" : forecasted_utilization
                }

                # Pushing worker result to Redis output cache
                redis_output.set(task_id, json.dumps(worker_result))

        except Exception as exp:
            print(f"Exception raised in log loop: {str(exp)}")
            sys.stdout.flush()
            sys.stderr.flush()
