import json
import os
import sys

from azure.eventhub import EventData, EventHubProducerClient
from dotenv import load_dotenv

# Grab credentials from .env file
load_dotenv()

# Grab config from the environment
CONNECTION_STR = os.getenv("AZURE_CONNECTION_STRING")
EVENT_HUB_NAME = os.getenv("EVENT_HUB_NAME")

# Make sure we have credentials before trying to connect
if not CONNECTION_STR:
    print("❌ Error: AZURE_CONNECTION_STRING is missing from .env")
    sys.exit(1)

if not EVENT_HUB_NAME:
    print("❌ Error: EVENT_HUB_NAME is missing from .env")
    sys.exit(1)


def send_heartbeat():
    print(f"🔌 Connecting to hub: {EVENT_HUB_NAME}...")

    # Initialize the client
    producer = EventHubProducerClient.from_connection_string(
        conn_str=CONNECTION_STR, eventhub_name=EVENT_HUB_NAME
    )

    # 'with' block auto-closes connection when done
    with producer:
        # Simple payload to verify the pipe is working
        payload = {
            "event": "HEARTBEAT",
            "status": "OK",
            "message": "Secure connection established via env vars",
        }

        # Batching is required even for single messages in Azure SDK
        batch = producer.create_batch()
        batch.add(EventData(json.dumps(payload)))

        # Fire it off
        producer.send_batch(batch)

        print("✅ Success! Heartbeat sent.")
        print("   Check the 'Incoming Requests' graph in Azure Portal to confirm.")


if __name__ == "__main__":
    try:
        send_heartbeat()
        input("\n[Press Enter to close]")  # Keep terminal open on Windows
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(
            "\nDev Tip: Check if your IP is blocked or if the connection string includes the EntityPath."
        )
