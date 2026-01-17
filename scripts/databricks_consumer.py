"""
Local consumer script for testing Azure Event Hub connection.
Prints incoming messages to the terminal for debugging.

For production, Databricks Delta Live Tables handles the actual consumption.
"""

import json
import os
import sys

from azure.eventhub import EventHubConsumerClient
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

CONNECTION_STR = os.getenv("AZURE_CONNECTION_STRING")
EVENT_HUB = os.getenv("EVENT_HUB_NAME", "vortex-topic")
CONSUMER_GROUP = "$Default"

# Make sure we have the connection string before trying to connect
if not CONNECTION_STR:
    print("❌ Error: AZURE_CONNECTION_STRING missing from .env file")
    print("   Add your Event Hub connection string to .env and try again")
    sys.exit(1)


def process_event(partition_context, event):
    """
    Runs on every new message. Decodes the payload and prints a quick summary.
    """
    raw_body = event.body_as_str(encoding="UTF-8")

    try:
        data = json.loads(raw_body)

        # Pull out the key fields (using .get() to handle weird/incomplete data)
        e_type = data.get("event_type", "UNKNOWN")
        archetype = data.get("user_archetype", "N/A")
        total = data.get("cart_total", 0.0)

        # Print it nice and aligned so the terminal output is easy to scan
        print(f"📦 [{e_type.upper():<16}] User: {archetype:<15} | Cart: ${total:8.2f}")

    except json.JSONDecodeError:
        print(f"⚠️  Skipping bad JSON: {raw_body[:50]}...")
    except Exception as e:
        print(f"❌ Something went wrong: {str(e)}")


def main():
    print(f"🔌 Connecting to: {EVENT_HUB}")
    print(f"   Consumer group: {CONSUMER_GROUP}")

    client = EventHubConsumerClient.from_connection_string(
        conn_str=CONNECTION_STR, consumer_group=CONSUMER_GROUP, eventhub_name=EVENT_HUB
    )

    try:
        with client:
            print("✅ Connected! Waiting for messages... (Ctrl+C to stop)")
            print("-" * 65)

            # starting_position=-1 means only show NEW messages (not old ones)
            client.receive(on_event=process_event, starting_position="-1")

    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    finally:
        print("✓ Done.")


if __name__ == "__main__":
    main()
