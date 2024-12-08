import json
from pykafka import KafkaClient
from pykafka.common import OffsetType
import xgboost as xgb
from datetime import datetime
import pandas as pd

client = KafkaClient("localhost:9092")
topic = client.topics['hospital-data-topic']
consumer = topic.get_simple_consumer(consumer_group=b"default",
    auto_offset_reset=OffsetType.LATEST,
    reset_offset_on_start=False,
    auto_commit_enable=True)

model = xgb.XGBRegressor()

# TODO: get the model json from minio object storage
model.load_model("../models/xgb_model.json")

for msg in consumer:
    sample = json.loads(msg.value.decode('utf-8'))

    timestamp = datetime.strptime(sample['timestamp'], "%Y-%m-%d %H:%M:%S")

    # Add time-based features
    sample["hour"] = timestamp.hour
    sample["day_of_week"] = timestamp.weekday()
    sample["day_of_month"] = timestamp.day
    sample["month"] = timestamp.month
    sample["year"] = timestamp.year

    lat, lng = sample['lat'], sample['lng']
    city, address = sample['city'], sample['address']

    for key in ["lat", "lng", "city", "address", "timestamp", "subtotal_acute_utilization"]:
        del sample[key]

    for i in range(1, 13):
        sample[f"lag_{i}"] = 0

    sample_df = pd.DataFrame(sample, index=['index'])

    print("Predicted utilization: ", model.predict(sample_df))
    print()

    consumer.commit_offsets()


    

