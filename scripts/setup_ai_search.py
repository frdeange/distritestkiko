#!/usr/bin/env python3
"""
Script to set up Azure AI Search index from Blob Storage.
Creates: data source, index, and indexer.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/workspaces/DistriPartnerSimplePlatform/.env")

SEARCH_ENDPOINT = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_AI_SEARCH_KEY")
STORAGE_CONN = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

API_VERSION = "2024-07-01"
INDEX_NAME = "support-knowledge-base"
DATASOURCE_NAME = "support-kb-datasource"
INDEXER_NAME = "support-kb-indexer"

headers = {
    "Content-Type": "application/json",
    "api-key": SEARCH_KEY
}

def create_datasource():
    """Create data source pointing to blob storage."""
    print("Creating data source...")
    url = f"{SEARCH_ENDPOINT}/datasources/{DATASOURCE_NAME}?api-version={API_VERSION}"
    
    payload = {
        "name": DATASOURCE_NAME,
        "type": "azureblob",
        "credentials": {
            "connectionString": STORAGE_CONN
        },
        "container": {
            "name": "support-knowledge-base"
        }
    }
    
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"  ✅ Data source created: {DATASOURCE_NAME}")
        return True
    else:
        print(f"  ❌ Error: {response.status_code} - {response.text}")
        return False

def create_index():
    """Create search index with fields for markdown documents."""
    print("Creating index...")
    url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}?api-version={API_VERSION}"
    
    payload = {
        "name": INDEX_NAME,
        "fields": [
            {
                "name": "id",
                "type": "Edm.String",
                "key": True,
                "searchable": False,
                "filterable": False,
                "sortable": False,
                "facetable": False
            },
            {
                "name": "content",
                "type": "Edm.String",
                "searchable": True,
                "filterable": False,
                "sortable": False,
                "facetable": False,
                "analyzer": "standard.lucene"
            },
            {
                "name": "metadata_storage_path",
                "type": "Edm.String",
                "searchable": False,
                "filterable": True,
                "sortable": False,
                "facetable": False
            },
            {
                "name": "metadata_storage_name",
                "type": "Edm.String",
                "searchable": True,
                "filterable": True,
                "sortable": False,
                "facetable": False
            },
            {
                "name": "metadata_storage_content_type",
                "type": "Edm.String",
                "searchable": False,
                "filterable": True,
                "sortable": False,
                "facetable": False
            }
        ]
    }
    
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"  ✅ Index created: {INDEX_NAME}")
        return True
    else:
        print(f"  ❌ Error: {response.status_code} - {response.text}")
        return False

def create_indexer():
    """Create indexer to populate the index from blob storage."""
    print("Creating indexer...")
    url = f"{SEARCH_ENDPOINT}/indexers/{INDEXER_NAME}?api-version={API_VERSION}"
    
    payload = {
        "name": INDEXER_NAME,
        "dataSourceName": DATASOURCE_NAME,
        "targetIndexName": INDEX_NAME,
        "parameters": {
            "configuration": {
                "parsingMode": "text",
                "dataToExtract": "contentAndMetadata"
            }
        },
        "fieldMappings": [
            {
                "sourceFieldName": "metadata_storage_path",
                "targetFieldName": "id",
                "mappingFunction": {
                    "name": "base64Encode"
                }
            }
        ],
        "schedule": None
    }
    
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"  ✅ Indexer created: {INDEXER_NAME}")
        return True
    else:
        print(f"  ❌ Error: {response.status_code} - {response.text}")
        return False

def run_indexer():
    """Run the indexer to index documents."""
    print("Running indexer...")
    url = f"{SEARCH_ENDPOINT}/indexers/{INDEXER_NAME}/run?api-version={API_VERSION}"
    
    response = requests.post(url, headers=headers)
    if response.status_code in [200, 202]:
        print(f"  ✅ Indexer started")
        return True
    else:
        print(f"  ❌ Error: {response.status_code} - {response.text}")
        return False

def check_indexer_status():
    """Check indexer status."""
    print("Checking indexer status...")
    url = f"{SEARCH_ENDPOINT}/indexers/{INDEXER_NAME}/status?api-version={API_VERSION}"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        status = response.json()
        last_result = status.get("lastResult", {})
        print(f"  Status: {last_result.get('status', 'unknown')}")
        print(f"  Documents processed: {last_result.get('itemsProcessed', 0)}")
        print(f"  Documents failed: {last_result.get('itemsFailed', 0)}")
        return True
    else:
        print(f"  ❌ Error: {response.status_code}")
        return False

def test_search():
    """Test search on the index."""
    print("\nTesting search...")
    url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}/docs/search?api-version={API_VERSION}"
    
    payload = {
        "search": "Azure AI Foundry",
        "top": 3,
        "select": "metadata_storage_name,content"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        results = response.json()
        docs = results.get("value", [])
        print(f"  Found {len(docs)} documents")
        for doc in docs:
            name = doc.get("metadata_storage_name", "unknown")
            content_preview = doc.get("content", "")[:100]
            print(f"    - {name}: {content_preview}...")
        return True
    else:
        print(f"  ❌ Error: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  Azure AI Search Setup for Support Knowledge Base")
    print("=" * 60)
    print(f"  Endpoint: {SEARCH_ENDPOINT}")
    print(f"  Index: {INDEX_NAME}")
    print("=" * 60 + "\n")
    
    # Create resources
    if not create_datasource():
        print("Failed to create data source")
    
    if not create_index():
        print("Failed to create index")
    
    if not create_indexer():
        print("Failed to create indexer")
    
    # Run indexer
    run_indexer()
    
    # Wait a moment and check status
    import time
    print("\nWaiting 10 seconds for indexing...")
    time.sleep(10)
    
    check_indexer_status()
    test_search()
    
    print("\n" + "=" * 60)
    print("  Setup complete!")
    print("=" * 60)
