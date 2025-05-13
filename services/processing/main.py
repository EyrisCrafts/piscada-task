from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
from datetime import datetime
import sensor_pb2
import nats
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

print(f"the influxdb token is {INFLUXDB_TOKEN}")

async def process_message(msg, influx_write_api):
    try:
        reading = sensor_pb2.SensorReading()
        reading.ParseFromString(msg.data)

        point = Point("sensor_readings")
        
        point.tag("sensor_id", reading.sensor_id)
        point.tag("building_id", reading.building_id)
        point.tag("floor", reading.floor)
        point.tag("room", reading.room)

        if reading.HasField("temperature"):
            point.tag("type", "temperature")
            point.field("value", reading.temperature.celsius)
        elif reading.HasField("humidity"):
            point.tag("type", "humidity")
            point.field("value", reading.humidity.percentage)
        elif reading.HasField("energy"):
            point.tag("type", "energy")
            point.field("value", reading.energy.kilowatts)

        point.time(reading.timestamp.ToDatetime())

        influx_write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        print(f"Stored reading from sensor {reading.sensor_id}")

    except Exception as e:
        print(f"Error processing message: {e}")

async def main():
    nc = await nats.connect(NATS_URL)
    print(f"Connected to NATS{NATS_URL}")

    influx_client = InfluxDBClient(
        url=INFLUXDB_URL,
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG
    )
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)
    print(f"Connected to InfluxDB at {INFLUXDB_URL}")

    async def subscribe_handler(msg):
        await process_message(msg, write_api)

    await nc.subscribe("sensors.*", cb=subscribe_handler)
    print("Subscribed to sensors.*")

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())