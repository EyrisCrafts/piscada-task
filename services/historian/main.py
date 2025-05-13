from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime, timedelta
from typing import List, Optional
import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from influxdb_client import InfluxDBClient
from fastapi.middleware.cors import CORSMiddleware

# Configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

# Initialize InfluxDB client
influx_client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)
query_api = influx_client.query_api()

@strawberry.type
class AlertReading:
    alert_id: str
    sensor_id: str
    building_id: str
    floor: str
    room: str
    timestamp: datetime
    message: Optional[str]

@strawberry.type
class AlertCount:
    count: int


@strawberry.type
class SensorReading:
    sensor_id: str
    building_id: str
    floor: str
    room: str
    timestamp: datetime
    value: float
    type: str

@strawberry.type
class AggregatedReading:
    sensor_id: str
    building_id: str
    floor: str
    room: str
    start_time: datetime
    end_time: datetime
    min_value: float
    max_value: float
    avg_value: float
    type: str

@strawberry.type
class Query:
    @strawberry.field
    def sensor_readings(
        self,
        sensor_id: Optional[str] = None,
        building_id: Optional[str] = None,
        floor: Optional[str] = None,
        room: Optional[str] = None,
        type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[SensorReading]:
        # Build Flux query
        query = f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -1h)'
        if start_time:
            query = f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: {start_time.isoformat()}Z'
            if end_time:
                query += f', stop: {end_time.isoformat()}Z'
            query += ')'
        
        query += ' |> filter(fn: (r) => r["_measurement"] == "sensor_readings")'

        if sensor_id:
            query += f' |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")'
        if building_id:
            query += f' |> filter(fn: (r) => r["building_id"] == "{building_id}")'
        if floor:
            query += f' |> filter(fn: (r) => r["floor"] == "{floor}")'
        if room:
            query += f' |> filter(fn: (r) => r["room"] == "{room}")'
        if type:
            query += f' |> filter(fn: (r) => r["type"] == "{type}")'

        result = query_api.query(query)

        readings = []
        for table in result:
            for record in table.records:
                readings.append(
                    SensorReading(
                        sensor_id=record.values.get("sensor_id"),
                        building_id=record.values.get("building_id"),
                        floor=record.values.get("floor"),
                        room=record.values.get("room"),
                        timestamp=record.get_time(),
                        value=record.get_value(),
                        type=record.values.get("type")
                    )
                )
        return readings

    @strawberry.field
    def aggregated_readings(
        self,
        window: str = "1h",
        sensor_id: Optional[str] = None,
        building_id: Optional[str] = None,
        floor: Optional[str] = None,
        room: Optional[str] = None,
        type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[AggregatedReading]:
        # Build Flux query with aggregation
        if start_time:
            query = f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: {start_time.isoformat()}Z'
            if end_time:
                query += f', stop: {end_time.isoformat()}Z'
            query += ')'
        else:
            query = f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -{window})'

        query += ' |> filter(fn: (r) => r["_measurement"] == "sensor_readings")'
        query += ' |> filter(fn: (r) => r["_field"] == "value")'

        if sensor_id:
            query += f' |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")'
        if building_id:
            query += f' |> filter(fn: (r) => r["building_id"] == "{building_id}")'
        if floor:
            query += f' |> filter(fn: (r) => r["floor"] == "{floor}")'
        if room:
            query += f' |> filter(fn: (r) => r["room"] == "{room}")'
        if type:
            query += f' |> filter(fn: (r) => r["type"] == "{type}")'

        
        query += f'''
        |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
        |> group()
        '''

        # Execute query
        result = query_api.query(query)

        total = {
            "min": float("inf"),
            "max": float("-inf"),
            "sum": 0.0,
            "count": 0,
            "start_time": None,
            "end_time": None,
        }

        for table in result:
            for record in table.records:
                value = record.get_value()
                total["min"] = min(total["min"], value)
                total["max"] = max(total["max"], value)
                total["sum"] += value
                total["count"] += 1
                if not total["start_time"]:
                    total["start_time"] = record.get_time()

        if total["count"] > 0:
            avg = total["sum"] / total["count"]
            return [
                AggregatedReading(
                    sensor_id="all",
                    building_id="all",
                    floor="all",
                    room="all",
                    start_time=total["start_time"],
                    end_time=total["start_time"] + timedelta(hours=1),
                    min_value=total["min"],
                    max_value=total["max"],
                    avg_value=avg,
                    type=type or "all"
                )
            ]
        else:
            return []


    @strawberry.field
    def alert_readings(
        self,
        alert_id: Optional[str] = None,
        sensor_id: Optional[str] = None,
        building_id: Optional[str] = None,
        floor: Optional[str] = None,
        room: Optional[str] = None,
        type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[AlertReading]:
        # Build Flux query
        query = f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -1h)'
        if start_time:
            query = f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: {start_time.isoformat()}Z'
            if end_time:
                query += f', stop: {end_time.isoformat()}Z'
            query += ')'
        
        query += ' |> filter(fn: (r) => r["_measurement"] == "alerts")'

        if alert_id:
            query += f' |> filter(fn: (r) => r["alert_id"] == "{alert_id}")'
        if sensor_id:
            query += f' |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")'
        if building_id:
            query += f' |> filter(fn: (r) => r["building_id"] == "{building_id}")'
        if floor:
            query += f' |> filter(fn: (r) => r["floor"] == "{floor}")'
        if room:
            query += f' |> filter(fn: (r) => r["room"] == "{room}")'
        if type:
            query += f' |> filter(fn: (r) => r["type"] == "{type}")'

        result = query_api.query(query)

           
        readings = []
        for table in result:
            for record in table.records:
                if record.get_field() == "message":
                    message = record.get_value()
                    if message:  # skip if None or empty
                        readings.append(
                            AlertReading(
                                alert_id=record.values.get("alert_id"),
                                sensor_id=record.values.get("sensor_id"),
                                building_id=record.values.get("building_id"),
                                floor=record.values.get("floor"),
                                room=record.values.get("room"),
                                message=message,
                                timestamp=record.get_time(),
                            )
                        )

        return readings

    @strawberry.field
    def alert_count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> AlertCount:
        if start_time:
            query = f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: {start_time.isoformat()}Z'
            if end_time:
                query += f', stop: {end_time.isoformat()}Z'
            query += ')'
        else:
            query = f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -1h)'

        query += '''
            |> filter(fn: (r) => r["_measurement"] == "alerts")
            |> filter(fn: (r) => r["_field"] == "message")
            |> count()
        '''

        result = query_api.query(query)

        total = 0
        for table in result:
            for record in table.records:
                total += record.get_value()

        return AlertCount(count=total)

    
schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or ["*"] for dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(graphql_app, prefix="/graphql")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
