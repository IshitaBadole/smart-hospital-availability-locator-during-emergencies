from kafka import KafkaProducer
from kafka.errors import KafkaError
import logging as log
import json
import random

producer = KafkaProducer(bootstrap_servers=['127.0.0.1:9092'], 
                         api_version=(0,9), 
                         value_serializer=lambda m: json.dumps(m).encode('ascii'))


# Dataset columns
#  #   Column                                                Non-Null Count  Dtype  
# ---  ------                                                --------------  -----  
#  0   hospital_name                                         4633 non-null   object 
#  1   hospital_ownership                                    4633 non-null   object 
#  2   hospital_type                                         4633 non-null   object 
#  3   lat                                                   4633 non-null   float64
#  4   lng                                                   4633 non-null   float64
#  5   address                                               4633 non-null   object 
#  6   city                                                  4633 non-null   object 
#  7   emergency_services                                    4633 non-null   bool   
#  8   source_year                                           4633 non-null   int64  
#  9   days_in_period                                        4633 non-null   int64  
#  10  subtotal_acute_utilization                            4633 non-null   float64
#  11  subtotal_acute_bed_days_1400                          4633 non-null   float64
#  12  hospital_overall_rating                               4633 non-null   object 
#  13  mortality_national_comparison                         4633 non-null   object 
#  14  safety_of_care_national_comparison                    4633 non-null   object 
#  15  readmission_national_comparison                       4633 non-null   object 
#  16  patient_experience_national_comparison                4633 non-null   object 
#  17  effectiveness_of_care_national_comparison             4633 non-null   object 
#  18  timeliness_of_care_national_comparison                4633 non-null   object 
#  19  efficient_use_of_medical_imaging_national_comparison  4633 non-null   object 
#  20  Beds Availability                                     4633 non-null   bool 

# list of hospitals data 
# each element is a dictionary of hospital and it's fixed information
hospitals_data = [{
    "hospital_name": "A",
    "hospital_ownership": "",
    "hospital_type": "",
    "lat": "",
    "lng": "",
    "address": "",
    "city": "",
    "emergency_services": "",
    "hospital_overall_rating": "",
    "mortality_national_comparison": "",
    "safety_of_care_national_comparison": "",
    "readmission_national_comparison": "",
    "patient_experience_national_comparison": "",
    "effectiveness_of_care_national_comparison": "",
    "timeliness_of_care_national_comparison": "",
    "efficient_use_of_medical_imaging_national_comparison": "",
    "Beds Availability": ""
},
{
    "hospital_name": "B",
    "hospital_ownership": "",
    "hospital_type": "",
    "lat": "",
    "lng": "",
    "address": "",
    "city": "",
    "emergency_services": "",
    "hospital_overall_rating": "",
    "mortality_national_comparison": "",
    "safety_of_care_national_comparison": "",
    "readmission_national_comparison": "",
    "patient_experience_national_comparison": "",
    "effectiveness_of_care_national_comparison": "",
    "timeliness_of_care_national_comparison": "",
    "efficient_use_of_medical_imaging_national_comparison": "",
    "Beds Availability": ""
},
{
    "hospital_name": "C",
    "hospital_ownership": "",
    "hospital_type": "",
    "lat": "",
    "lng": "",
    "address": "",
    "city": "",
    "emergency_services": "",
    "hospital_overall_rating": "",
    "mortality_national_comparison": "",
    "safety_of_care_national_comparison": "",
    "readmission_national_comparison": "",
    "patient_experience_national_comparison": "",
    "effectiveness_of_care_national_comparison": "",
    "timeliness_of_care_national_comparison": "",
    "efficient_use_of_medical_imaging_national_comparison": "",
    "Beds Availability": ""
}]
# Randomly choose a hospital
hospital_data = random.choice(hospitals_data)

# Generate simulated utilization data
timing_data = {
    "source_year": 2024,
    "days_in_period": 365,
    "subtotal_acute_utilization": float(random.randrange(0, 100)),
    "subtotal_acute_bed_days_1400": float(random.randrange(800, 50000))
}

# Construct the message to contain hospital data with simulated utilization data
message = hospital_data | timing_data

# Log the message on the producer side
log.info(message)

# Asynchronous by default
future = producer.send('json-topic', message)

# Block for 'synchronous' sends
try:
    record_metadata = future.get(timeout=10)
except KafkaError:
    # Decide what to do if produce request failed...
    log.exception()
    pass

# Successful result returns assigned partition and offset
print (record_metadata.topic)
print (record_metadata.partition)
print (record_metadata.offset)


