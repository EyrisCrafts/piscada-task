from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
import uuid
from datetime import datetime
from typing import Optional
import sensor_pb2 as sensor_pb2
import alert_pb2 as alert_pb2
import nats
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS, WriteApi
from nats.aio.client import Client as NATS
from nats.aio.msg import Msg

from google.protobuf.timestamp_pb2 import Timestamp

NATS_URL: str = os.getenv("NATS_URL", "nats://localhost:4222")
INFLUXDB_URL: str = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN: Optional[str] = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG: Optional[str] = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET: Optional[str] = os.getenv("INFLUXDB_BUCKET")

TEMP_MIN: float = float(os.getenv("TEMP_MIN", "24.0"))
TEMP_MAX: float = float(os.getenv("TEMP_MAX", "26.0"))
HUMIDITY_MIN: float = float(os.getenv("HUMIDITY_MIN", "35.0"))
HUMIDITY_MAX: float = float(os.getenv("HUMIDITY_MAX", "70.0"))
ENERGY_MAX: float = float(os.getenv("ENERGY_MAX", "4.0"))


async def check_thresholds(reading: sensor_pb2.SensorReading, influx_write_api: WriteApi, nc: NATS) -> None:
    try:
        alert: Optional[str] = None

        
        if reading.HasField("temperature"):
            value = reading.temperature.celsius
            if value < TEMP_MIN:
                alert = f"Temperature too low: {value}°C"
            elif value > TEMP_MAX:
                alert = f"Temperature too high: {value}°C"
        
        elif reading.HasField("humidity"):
            value = reading.humidity.percentage
            if value < HUMIDITY_MIN:
                alert = f"Humidity too low: {value}%"
            elif value > HUMIDITY_MAX:
                alert = f"Humidity too high: {value}%"
        
        elif reading.HasField("energy"):
            value = reading.energy.kilowatts
            if value > ENERGY_MAX:
                alert = f"High energy consumption: {value}kW"

        if alert != None:
            
            alert_id = str(uuid.uuid4())
            point: Point = Point("alerts")
            point.tag("alert_id", alert_id)
            point.tag("sensor_id", reading.sensor_id)
            point.tag("building_id", reading.building_id)
            point.tag("floor", reading.floor)
            point.tag("room", reading.room)
            point.field("message", alert)
            point.time(reading.timestamp.ToDatetime())

            influx_write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
            try:
                alert_protobuf = alert_pb2.Alert()

                alert_protobuf.alert_id = alert_id
                alert_protobuf.sensor_id = reading.sensor_id
                alert_protobuf.building_id = reading.building_id
                alert_protobuf.message = alert
                timestamp = Timestamp()
                timestamp.FromDatetime(datetime.now())
                alert_protobuf.timestamp.CopyFrom(timestamp)

                full_alert = f"[{reading.building_id} - Floor {reading.floor} - Room {reading.room}] {alert}"
                print(f"Alert generated for sensor {reading.sensor_id}: {full_alert}")
                
                await nc.publish("alerts", alert_protobuf.SerializeToString())
            except:
                print("Error publishing alert to Nats")
            

    except Exception as e:
        print(f"Error processing alert: {e}")

async def process_message(msg: Msg, influx_write_api: WriteApi, nc: NATS) -> None:
    try:
        reading: sensor_pb2.SensorReading = sensor_pb2.SensorReading()
        reading.ParseFromString(msg.data)
        
        await check_thresholds(reading, influx_write_api, nc)

    except Exception as e:
        print(f"Error processing message: {e}")

async def main() -> None:
    nc: NATS = await nats.connect(NATS_URL)
    print(f"Connected to NATS at {NATS_URL}")

    influx_client: InfluxDBClient = InfluxDBClient(
        url=INFLUXDB_URL,
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG
    )
    write_api: WriteApi = influx_client.write_api(write_options=SYNCHRONOUS)
    print(f"Connected to InfluxDB at {INFLUXDB_URL}")

    async def subscribe_handler(msg: Msg) -> None:
        await process_message(msg, write_api, nc)

    await nc.subscribe("sensors.*", cb=subscribe_handler)
    print("Subscribed to sensors.*")

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
