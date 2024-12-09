import json
from pykafka import KafkaClient
from pykafka.common import OffsetType
import xgboost as xgb
from datetime import datetime
import pandas as pd
import os
from minio import Minio
import redis

def execute_with_retry(command, *args, **kwargs):
    """
    Executes a Redis command with retry logic.

    Parameters:
    - command: The Redis command to execute (as a function).
    - args, kwargs: Arguments to pass to the Redis command.

    Returns:
    - The result of the Redis command.
    """
    global redisClient
    try:
        # Call the Redis command
        result = command(*args, **kwargs)
        print(f"Command:{command} result:{result}")
        return result
    except (TimeoutError, ConnectionError) as e:
        # Creating the Redis client again
        redisClient = redis.StrictRedis(host=redisHost, 
                                port=redisPort, 
                                db=0)
        result = command(*args, **kwargs)  
        print(f"Command:{command} result:{result}")
        return result

# Initializing minio variables
minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

# Defining Redis Variables
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379

# Creating a minio client object
minio_client = Minio(minioHost,
               secure=False,
               access_key=minioUser,
               secret_key=minioPasswd)

# Creating the Redis client
redisClient = redis.StrictRedis(host=redisHost, 
                                    port=redisPort, 
                                    db=0)

bucket = "models"

# Creating the Kafka Client object and the Kafka topic
client = KafkaClient("localhost:9092")
topic = client.topics['hospital-data-topic']

# Loading the mappings for categorical variables to their corresponding integer values from 
# data/mappings.json
with open(os.path.join(os.getcwd(), 'data', 'mappings.json')) as fp:
    mappings = json.load(fp)

# Creating the Kafka consumer
consumer = topic.get_simple_consumer(consumer_group=b"default",
    auto_offset_reset=OffsetType.LATEST,
    reset_offset_on_start=True,
    auto_commit_enable=True)

# Initializing the XGBoost model
model = xgb.XGBRegressor()

# Getting the V0 XGB model from Minio object storage
response = minio_client.fget_object(bucket, 'xgb_model_v0.json', os.getcwd())

# Loading the model
model.load_model(os.path.join(os.getcwd(), 'xgb_model_v0.json'))

for msg in consumer:
    # Decoding the JSON message coming from the producer
    sample = json.loads(msg.value.decode('utf-8'))

    # Converting the timestamp to a datetime object to extract temporal features
    timestamp = datetime.strptime(sample['timestamp'], "%Y-%m-%d %H:%M:%S")

    # Adding the temporal lag features to the sample
    ground_truth_key = f"ground_truth:{sample['hospital_name']}"
    key_exists = execute_with_retry(redisClient.exists, ground_truth_key)

    # the key does not exist which means that the hospital data has never been seen before
    if not key_exists:
        # initialize the lag features to 0
        lags = [0] * 12
    else:
        # get the ground truth values stored in redis
        lags = redisClient.lrange(ground_truth_key, 0, -1)
        lags = execute_with_retry(redisClient.lrange, ground_truth_key, 0 , -1)

    for i in range(12):
        sample[f"lag_{i+1}"] = lags[i]

    # Add temporal features to the sample
    sample["hour"] = timestamp.hour
    sample["day_of_week"] = timestamp.weekday()
    sample["day_of_month"] = timestamp.day
    sample["month"] = timestamp.month
    sample["year"] = timestamp.year

    # Storing the latitude, longitude, city and address of the current message before dropping them
    # from the sample. These variables are not required for prediction
    lat, lng = sample['lat'], sample['lng']
    city, address = sample['city'], sample['address']

    # Deleting the columns not required for model predictions
    for key in ["lat", "lng", "city", "address", "timestamp", "subtotal_acute_utilization"]:
        del sample[key]

    # Mapping all the categorical variables to integer values
    for col in sample.keys():
        if col in mappings:
            sample[col] = mappings[col][sample[col]]

    print(sample)

    # Creating a dataframe of the current sample
    sample_df = pd.DataFrame(sample, index=['index'])
    sample_df.set_index(['index'], inplace=True)
    print(sample_df.columns)

    # Predict the utilization for the next hour
    predicted_utilization = model.predict(sample_df)

    print("Predicted utilization: ", predicted_utilization)
    print()

    # Store the predicted utilization in Redis cache
    predicted_utilization_key = f"pred_utilization:{sample['hospital_name']}"
    execute_with_retry(redisClient.set, predicted_utilization_key, predicted_utilization)

    # consumer.commit_offsets()

    # Add the ground truth utilization to the temporal lags
    execute_with_retry(redisClient.rpush, ground_truth_key, sample['simulated_utilization'])
    # Remove the oldest lag
    execute_with_retry(redisClient.lpop, ground_truth_key)

    # TODO: Store the current model in MinIO



    




    

