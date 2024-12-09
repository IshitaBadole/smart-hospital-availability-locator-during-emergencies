import json
from pykafka import KafkaClient
from pykafka.common import OffsetType
import xgboost as xgb
from datetime import datetime
import pandas as pd
import os
from minio import Minio

# Initializing minio variables
minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

# Creating a minio client object
minio_client = Minio(minioHost,
               secure=False,
               access_key=minioUser,
               secret_key=minioPasswd)

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
    # TODO: This should be coming from Redis with all the lag features for each hospital initialized
    # to 0 in the redis cache
    for i in range(1, 13):
        sample[f"lag_{i}"] = 0

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

    print("Predicted utilization: ", model.predict(sample_df))
    print()

    # consumer.commit_offsets()


    # TODO : Get the latest version of the model from MinIO object storage
    # TODO : Add the Redis cache and retraining logic 


    

