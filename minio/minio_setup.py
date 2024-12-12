#!/usr/bin/env python3

import os
from minio import Minio

minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

def put_object(bucketname, bucket_filename, local_filepath, content_type="application/octet-stream"):

    client = Minio(minioHost,
               secure=False,
               access_key=minioUser,
               secret_key=minioPasswd)

    if not client.bucket_exists(bucketname):
        print(f"Create bucket {bucketname}")
        client.make_bucket(bucketname)

    try:
        objects = client.list_objects(bucketname)
        object_exists = bucket_filename in [obj.object_name for obj in objects]

        if not object_exists:
            print(f"Bucket {bucketname} is empty. Add file {bucket_filename}")
            client.fput_object(bucketname, 
                               bucket_filename, 
                               local_filepath,
                               content_type=content_type)
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

put_object("models", "xgb_model_v0.json", os.path.join(os.getcwd(), "models", "xgb_model.json"))
put_object("data", "hospital_data.csv", os.path.join(os.getcwd(), "data", "final_hospital_data.csv"), content_type="application/csv")
put_object("data", "mappings.json", os.path.join(os.getcwd(), "data", "mappings.json"), content_type="application/json")