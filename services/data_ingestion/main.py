import asyncio
import os
import random
from datetime import datetime
import sensor_pb2
from google.protobuf.timestamp_pb2 import Timestamp
import nats

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
BUILDINGS = ["Building_A", "Building_B"]
FLOORS = ["1", "2", "3"]
ROOMS = ["101", "102", "103", "201", "202", "203", "301", "302", "303"]
SENSOR_TYPES = ["temperature", "humidity", "energy"]

async def generate_sensor_reading():
    building_id = random.choice(BUILDINGS)
    floor = random.choice(FLOORS)
    room = random.choice(ROOMS)
    sensor_type = random.choice(SENSOR_TYPES)
    sensor_id = f"{building_id}_{floor}_{room}_{sensor_type}"

    reading = sensor_pb2.SensorReading()
    reading.sensor_id = sensor_id
    reading.building_id = building_id
    reading.floor = floor
    reading.room = room

    timestamp = Timestamp()
    timestamp.FromDatetime(datetime.utcnow())
    reading.timestamp.CopyFrom(timestamp)

    if sensor_type == "temperature":
        temp = reading.temperature
        temp.celsius = random.uniform(18.0, 28.0)
    elif sensor_type == "humidity":
        humidity = reading.humidity
        humidity.percentage = random.uniform(30.0, 70.0)
    else:
        energy = reading.energy
        energy.kilowatts = random.uniform(0.5, 5.0)

    return reading, sensor_type

async def main():
    nc = await nats.connect(NATS_URL)
    print(f"Connected to NATS at {NATS_URL}")

    while True:
        try:
            reading, sensor_type = await generate_sensor_reading()
            subject = f"sensors.{sensor_type}"
            await nc.publish(subject, reading.SerializeToString())
            if sensor_type == "temperature":
                print(f"Published {sensor_type} reading of {reading.temperature.celsius:.1f}°C for sensor {reading.sensor_id} in {reading.building_id}, floor {reading.floor}, room {reading.room}")
            elif sensor_type == "humidity":
                print(f"Published {sensor_type} reading of {reading.humidity.percentage:.1f}% for sensor {reading.sensor_id} in {reading.building_id}, floor {reading.floor}, room {reading.room}")
            else:
                print(f"Published {sensor_type} reading of {reading.energy.kilowatts:.2f}kW for sensor {reading.sensor_id} in {reading.building_id}, floor {reading.floor}, room {reading.room}")
            
            await asyncio.sleep(random.uniform(1, 2))
        except Exception as e:
            print(f"Error publishing message: {e}")
            await asyncio.sleep(5) 

if __name__ == "__main__":
    asyncio.run(main())