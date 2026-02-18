#!/usr/bin/env python3
"""
Setup CosmosDB database and containers for the DistriPartner bot.

Creates:
  - Database: distripartner-bot
  - Container: bot-state          (partition: /id)             — SDK TurnState
  - Container: user-profiles      (partition: /aadObjectId)    — cached user profiles
  - Container: conversation-history (partition: /conversationId, TTL: 30 days)

Auth: DefaultAzureCredential (Managed Identity or local dev credentials).
Requires 'Cosmos DB Built-in Data Contributor' role on the CosmosDB account.

Usage:
    python scripts/setup_cosmos.py
"""

import os
import sys

from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Load env vars
load_dotenv()

COSMOS_ENDPOINT = os.getenv(
    "BOT_COSMOS_ENDPOINT",
    "https://distriplatform-cosmos.documents.azure.com:443/",
)
DATABASE_NAME = os.getenv("BOT_COSMOS_DATABASE", "distripartner-bot")
MSI_CLIENT_ID = os.getenv("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID")

# Container definitions
CONTAINERS = [
    {
        "name": "bot-state",
        "partition_key": "/id",
        "ttl": None,
        "description": "SDK TurnState (WorkflowStateItem)",
    },
    {
        "name": "user-profiles",
        "partition_key": "/aadObjectId",
        "ttl": None,
        "description": "Cached user profiles from get_member API",
    },
    {
        "name": "conversation-history",
        "partition_key": "/conversationId",
        "ttl": 30 * 24 * 60 * 60,  # 30 days
        "description": "Message log (user + assistant) with auto-purge",
    },
]


def main():
    print(f"CosmosDB Setup")
    print(f"  Endpoint:  {COSMOS_ENDPOINT}")
    print(f"  Database:  {DATABASE_NAME}")
    print()

    if not COSMOS_ENDPOINT:
        print("ERROR: BOT_COSMOS_ENDPOINT is not set.")
        sys.exit(1)

    # Authenticate
    print("Authenticating with DefaultAzureCredential...")
    credential = DefaultAzureCredential(
        managed_identity_client_id=MSI_CLIENT_ID or None
    )
    client = CosmosClient(url=COSMOS_ENDPOINT, credential=credential)
    print("  OK\n")

    # Create database
    print(f"Creating database '{DATABASE_NAME}'...")
    try:
        db = client.create_database_if_not_exists(DATABASE_NAME)
        print(f"  Database ready.\n")
    except Exception as e:
        print(f"  ERROR creating database: {e}")
        sys.exit(1)

    # Create containers
    for container_def in CONTAINERS:
        name = container_def["name"]
        pk = container_def["partition_key"]
        ttl = container_def["ttl"]
        desc = container_def["description"]

        print(f"Creating container '{name}'...")
        print(f"  Partition key: {pk}")
        print(f"  TTL: {ttl if ttl else 'disabled'}")
        print(f"  Purpose: {desc}")

        try:
            kwargs = {
                "id": name,
                "partition_key": PartitionKey(path=pk),
            }
            if ttl is not None:
                kwargs["default_ttl"] = ttl

            container = db.create_container_if_not_exists(**kwargs)
            print(f"  Container ready.\n")
        except Exception as e:
            print(f"  ERROR: {e}\n")

    # Verify
    print("Verification — listing containers:")
    for container_props in db.list_containers():
        print(f"  - {container_props['id']} (partition: {container_props.get('partitionKey', {}).get('paths', ['?'])})")

    print("\nSetup complete.")


if __name__ == "__main__":
    main()
