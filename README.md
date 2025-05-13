# Piscada task 

A distributed system for processing and monitoring sensor data.

## Services

- data_ingestion: Generates and publishes sensor readings
- processing: Processes incoming sensor data
- historian: Stores historical sensor data
- alerting: Handles alert conditions
- my-web-app: Web interface for data visualization
- discord: Discord bot for notifications

## Setup

Start services using Docker Compose:
   ```
   docker-compose up
   ```

## Testing Individual Services

To test a service individually:

1. Copy the environment file:
   ```
   cp .env.sample .env
   ```

2. Update the necessary variables in `.env` for the service you want to test

3. Install the dependencies
   ```
   pip3 install -r requirements.txt
   ```

4. Run the service directly:
   ```
   python main.py
   ```

For example, to test the data ingestion service:
   ```
   cd services/data_ingestion/
   python main.py
   ```

