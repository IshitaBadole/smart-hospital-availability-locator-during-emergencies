import json
import os
import sys
from datetime import datetime

import pandas as pd
import xgboost as xgb
from pykafka import KafkaClient
from pykafka.common import OffsetType

import redis
from minio import Minio

# Logging variables
infoKey = "kafka_consumer:[INFO]"
debugKey = "kafka_consumer:[DEBUG]"


def log_debug(message):
    print("DEBUG:", message, file=sys.stdout)
    redisLog = redis.StrictRedis(host=redisHost, port=redisPort, db=2)
    redisLog.lpush("logging", f"{debugKey}:{message}")


def log_info(message):
    print("INFO:", message, file=sys.stdout)
    redisLog = redis.StrictRedis(host=redisHost, port=redisPort, db=2)
    redisLog.lpush("logging", f"{infoKey}:{message}")


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
        log_debug(f"Command:{command} result:{result}")
        return result
    except (TimeoutError, ConnectionError) as e:
        # Creating the Redis client again
        redisClient = redis.StrictRedis(
            host=redisHost, port=redisPort, db=0, decode_responses=True
        )
        result = command(*args, **kwargs)
        log_debug(f"Command:{command} result:{result}")
        return result


# Defining minio variables
minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

# Defining Redis variables
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379

# Creating a minio client object
minio_client = Minio(
    minioHost, secure=False, access_key=minioUser, secret_key=minioPasswd
)

# Creating the Redis client
redisClient = redis.StrictRedis(
    host=redisHost, port=redisPort, db=0, decode_responses=True
)

# bucket variables
model_bucket = "models"
data_bucket = "data"


curr_model_version = 0

# Initialzing an empty df to store incoming real-time samples
# Retrain the XGB Regressor every 1000 real-time samples
buffer = pd.DataFrame()
buffer_size = 15
previous_sample = {}

# Creating the Kafka Client object and the Kafka topic
client = KafkaClient("localhost:9092")
topic = client.topics["hospital-data-topic"]

# Loading the mappings for categorical variables to their corresponding integer values
log_debug(f"Downloading mappings.json from MinIo")
minio_client.fget_object(
    data_bucket, f"mappings.json", os.path.join(os.getcwd(), "mappings.json")
)
with open(os.path.join(os.getcwd(), "mappings.json")) as fp:
    mappings = json.load(fp)

# Creating the Kafka consumer
consumer = topic.get_simple_consumer(
    consumer_group=b"default",
    auto_offset_reset=OffsetType.LATEST,
    reset_offset_on_start=True
)

# Initializing the XGBoost model
model = xgb.XGBRegressor()

# Getting the V0 XGB model from Minio object storage
response = minio_client.fget_object(
    model_bucket, "xgb_model_v0.json", os.path.join(os.getcwd(), "xgb_model_v0.json")
)

# Loading the model
model.load_model(os.path.join(os.getcwd(), "xgb_model_v0.json"))

for msg in consumer:
    # Decoding the JSON message coming from the producer
    sample = json.loads(msg.value.decode("utf-8"))
    log_info(f"Received message: {sample}")

    # Converting the timestamp to a datetime object to extract temporal features
    timestamp = datetime.strptime(sample["timestamp"], "%Y-%m-%d %H:%M:%S")

    # Adding the temporal lag features to the sample
    ground_truth_key = f"ground_truth:{sample['hospital_name']}"
    key_exists = execute_with_retry(redisClient.exists, ground_truth_key)

    # the key does not exist which means that the hospital data has never been seen before
    if not key_exists:
        # initialize the lag features to 0
        lags = [0.0] * 12
        execute_with_retry(redisClient.rpush, ground_truth_key, *lags)
    else:
        # get the ground truth values stored in redis
        lags = redisClient.lrange(ground_truth_key, 0, -1)
        lags = execute_with_retry(redisClient.lrange, ground_truth_key, 0, -1)
        lags = [float(lag) for lag in lags]

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
    lat, lng = sample["lat"], sample["lng"]
    city, address, state, hospital_name = (
        sample["city"],
        sample["address"],
        sample["state"],
        sample["hospital_name"],
    )

    # Deleting the columns not required for model predictions
    for key in [
        "lat",
        "lng",
        "city",
        "state",
        "address",
        "timestamp",
        "subtotal_acute_utilization",
    ]:
        del sample[key]

    # Mapping all the categorical variables to integer values
    for col in sample.keys():
        if col in mappings:
            sample[col] = mappings[col][sample[col]]

    if hospital_name not in previous_sample:
        previous_sample[hospital_name] = None

    # Align target with the previous sample for this hospital
    if previous_sample[hospital_name]:
        # Set the target for the last sample as the current `simulated_utilization`
        previous_sample[hospital_name]["target"] = sample["simulated_utilization"]

        # Add the previous sample to the buffer
        prev_sample = pd.DataFrame(previous_sample[hospital_name], index=["index"])
        buffer = pd.concat([buffer, prev_sample], axis=0)

    # Update the last sample for this hospital
    previous_sample[hospital_name] = sample.copy()

    # If buffer limit has been reached, retrain the model, clear the buffer and
    # store retrained model in the MinIO object storage
    if len(buffer) == buffer_size:

        log_info("Retraining the XGBRegressor Model")

        # Convert the buffer to a DataFrame
        train_data = buffer.copy()
        train_data.set_index(["index"], inplace=True)

        # Separate features and target variable
        X_train = train_data.drop(columns=["target"])
        y_train = train_data["target"]

        # Convert data to DMatrix
        dtrain = xgb.DMatrix(X_train, label=y_train)

        # Update the model incrementally
        model_booster = model.get_booster()
        model_booster.update(dtrain, iteration=1)

        # Store the retrained model in MinIO object storage
        curr_model_version += 1
        model_filename = f"xgb_model_v{curr_model_version}.json"
        model_booster.save_model(model_filename)
        minio_client.fput_object(model_bucket, model_filename, model_filename)
        log_info("Retraining model complete. Storing updated model in MinIO")

        # Clearing the buffer
        buffer = pd.DataFrame()

    # Creating a dataframe of the current sample
    sample_df = pd.DataFrame(sample, index=["index"])
    sample_df.set_index(["index"], inplace=True)

    # Predict the utilization for the next hour
    predicted_utilization = float(model.predict(sample_df)[0])

    log_info(f"Predicted utilization: {predicted_utilization}")

    # Store the predicted utilization in Redis cache
    predicted_utilization_key = f"pred_utilization:{hospital_name}"
    execute_with_retry(
        redisClient.set, predicted_utilization_key, predicted_utilization
    )

    # consumer.commit_offsets()

    # Add the ground truth utilization to the temporal lags
    execute_with_retry(
        redisClient.rpush, ground_truth_key, sample["simulated_utilization"]
    )
    # Remove the oldest lag
    execute_with_retry(redisClient.lpop, ground_truth_key)

    consumer.commit_offsets()
