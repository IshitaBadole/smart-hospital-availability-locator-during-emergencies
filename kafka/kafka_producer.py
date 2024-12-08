import json
import logging
import time
import os
import numpy as np
import pandas as pd
from pykafka import KafkaClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# Simulate utilization using trends, noise, and random events
def simulate_utilization(num_records):
    # Linear trend for utilization over time
    trend = 75 + 0.1 * np.arange(num_records)

    # Random noise
    noise = np.random.normal(0, 10, size=num_records)

    # Event-driven spikes (simulate a surge during a specific time window)
    event_spike = np.zeros(num_records)
    event_spike[720:780] = 30  # Spike during a specific period (12:00 PM to 1:00 PM)

    # Combine trend, noise, and spikes
    utilization = trend + noise + event_spike
    # Ensure values are between 0 and 100
    return np.clip(utilization, 0, 100)


def main():
    # As a start, work with only five hospitals
    num_of_hospitals = 5

    client = KafkaClient("localhost:9092")
    topic = client.topics["hospital-data-topic"]

    # Try removing min_queeued and linger_ms
    producer = topic.get_producer(
        min_queued_messages=num_of_hospitals, linger_ms=60 * 1000
    )

    # Read the static hospital data
    hospital_data = pd.read_csv(os.path.join(os.getcwd(), "data", "final_hospital_data.csv"), index_col=0)

    hospital_data = hospital_data.head(n=num_of_hospitals)

    # Define the start and end times for the simulation
    start_time = pd.Timestamp("2023-01-01 00:00:00")
    end_time = start_time + pd.Timedelta(days=1)

    while True:
        # Generate minute-level time range
        time_range = pd.date_range(start=start_time, end=end_time, freq="h")

        # Generate simulated data for the time-range accounting for trend over the time range
        simulated_data = []

        # For each hospital, generate simulated utilization for timestamps in the time range
        for idx, row in hospital_data.iterrows():
            num_records = len(time_range)

            print(
                f"Simulate utilization for hospital: {hospital_data.iloc[idx]['hospital_name']}"
            )
            utilization = simulate_utilization(num_records)

            # Repeat the hospital's static features for each timestamp
            hospital_static_features = {
                col: [row[col]] * num_records for col in hospital_data.columns
            }
            simulated_hospital_data = pd.DataFrame(hospital_static_features)

            # Add timestamps and simulated utilization. Making timestamp a string as pandas
            # datetime is not JSON serializable
            simulated_hospital_data["timestamp"] = time_range.strftime("%Y-%m-%d %H:%M:%S")
            simulated_hospital_data["simulated_utilization"] = utilization

            simulated_data.append(simulated_hospital_data)

        # Combine all hospital data into a single DataFrame
        simulated_data_df = pd.concat(simulated_data, ignore_index=True)

        # Sort the dataframe by timestamp to simulate sending real-time messages
        simulated_data_df = simulated_data_df.sort_values(by="timestamp").reset_index()
        
        for idx, row in simulated_data_df.iterrows():
            # Each message contains simulated data for one hospital at one timestamp
            message = row.to_dict()

            # logger.debug(row)
            print(f"[{idx}] Sending utilization for {message['hospital_name']} at {message['timestamp']}")
            producer.produce(json.dumps(message).encode("utf-8"))

            # Wait for 1 minute after sending num_of_hospitals data
            # Assuming that 1 minute is equivalent to 1 hour for demonstration purposes
            if (idx + 1) % num_of_hospitals == 0:
                time.sleep(10)
                print()

        start_time = end_time
        end_time = end_time + pd.Timedelta(days=1)


if __name__ == "__main__":
    main()
