#!/usr/bin/env python3

from minio import Minio
import os

minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

client = Minio(minioHost,
               secure=False,
               access_key=minioUser,
               secret_key=minioPasswd)

bucketname='models'

if not client.bucket_exists(bucketname):
    print(f"Create bucket {bucketname}")
    client.make_bucket(bucketname)

buckets = client.list_buckets()

for bucket in buckets:
    print(f"Bucket {bucket.name}, created {bucket.creation}")

try:
    objects = client.list_objects(bucketname)
    is_empty = not any(objects)

    if is_empty:
        print(f"Bucket {bucketname} is empty. Add file xgb_model_v0.json")
        client.fput_object(bucketname, "xgb_model_v0.json", os.path.join(os.getcwd(), "xgb_model.json"))
    else:
        print(f"Objects in {bucketname} are:")
        for obj in objects:
            print(obj.object_name)
except Exception as e:
    print("Error when adding files the first time")
    print(str(e))
        
print(f"Objects in {bucketname} are now:")
for thing in client.list_objects(bucketname, recursive=True):
    print(thing.object_name)