# Using Custom HuggingFace Collections in Legal-Search-RAG

This guide explains how to create custom collections with HuggingFace embeddings and upload documents to them.

## Overview of Changes

The following functionality has been added:

1. Create custom collections with HuggingFace embeddings using `create_hf_collection.py`
2. Upload documents to a specific collection using the `collection_name` parameter
3. Search within custom collections using the `collection_name` parameter

All functionality works both locally and in deployed environments.

## Prerequisites

Ensure you have:

1. A RunPod embedding endpoint configured with legal-bert-base-uncased
2. Environment variables set in `.env`:
   ```
   RUNPOD_API_KEY=your_runpod_api_key
   RUNPOD_EMBEDDING_ENDPOINT_ID=your_endpoint_id
   HF_EMBEDDING_MODEL=nlpaueb/legal-bert-base-uncased
   ```
3. API authorization token (if required)

## Creating and Using Custom Collections

### Option 1: Using the All-in-One Script

The easiest way to create a collection and upload documents:

```bash
# Make scripts executable
chmod +x scripts/create_hf_collection.py scripts/upload_to_hf_collection.sh

# Create collection and upload documents (local API)
./scripts/upload_to_hf_collection.sh \
  -n my_legal_collection \
  -u http://localhost:8000/api/documents/upload \
  -f "/path/to/documents/*.pdf" \
  -t your_api_token

# For a deployed API
./scripts/upload_to_hf_collection.sh \
  -n my_legal_collection \
  -u https://your-deployed-api.com/api/documents/upload \
  -f "/path/to/documents/*.pdf" \
  -t your_api_token
```

Parameters:
- `-n, --name`: Collection name
- `-u, --url`: API endpoint URL
- `-f, --files`: Files to upload (wildcards supported in quotes)
- `-t, --token`: Auth token (optional if API_TOKEN is in .env)
- `--force`: Force collection recreation if it exists

### Option 2: Step-by-Step Approach

#### 1. Create a Custom Collection

```bash
# Create with default name (legal_docs_hf)
python scripts/create_hf_collection.py

# Create with custom name
python scripts/create_hf_collection.py --name my_custom_collection

# Force recreation of existing collection
python scripts/create_hf_collection.py --name my_custom_collection --force
```

#### 2. Upload Documents to the Collection

```bash
# Upload to custom collection (via curl)
curl -X POST "http://localhost:8000/api/documents/upload?collection_name=my_custom_collection" \
  -H "Authorization: Bearer your_api_token" \
  -F "file=@/path/to/document.pdf"

# Using the upload script
./scripts/upload_docs.sh \
  -u "http://localhost:8000/api/documents/upload?collection_name=my_custom_collection" \
  -f "/path/to/document.pdf" \
  -t your_api_token
```

#### 3. Search Within the Custom Collection

```bash
# Search with modern endpoint
curl -X POST "http://localhost:8000/api/search?collection_name=my_custom_collection" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_token" \
  -d '{"query": "legal precedent", "limit": 5}'

# Search with legacy endpoint
curl -X POST "http://localhost:8000/api/search/api?collection_name=my_custom_collection" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_token" \
  -d '{
    "query_text": "legal precedent",
    "n_results": 5,
    "min_similarity": 0.7
  }'
```

## Deployment Process

To use this in a deployed environment:

1. **Deploy the API** with the code changes
2. **Create collections** either directly on the server or by running the script against your deployed API
3. **Upload documents** using the script targeting your deployed API URL with the collection name parameter
4. **Search** using the deployed API URL with the collection name parameter

## Troubleshooting

### Common Issues

1. **Collection not found**: Ensure the collection name is spelled correctly and exists
   ```bash
   # List collections
   python -c "import chromadb; client = chromadb.PersistentClient('./data/chroma'); print([c.name for c in client.list_collections()])"
   ```

2. **No results from search**: Verify documents were uploaded to the correct collection
   ```bash
   # Check collection count
   python -c "import chromadb; client = chromadb.PersistentClient('./data/chroma'); collection = client.get_collection('my_custom_collection'); print(f'Documents in collection: {collection.count()}')"
   ```

3. **RunPod errors**: Check RunPod endpoint health
   ```bash
   curl --request GET \
     --url https://api.runpod.ai/v2/{endpoint_id}/health \
     --header 'accept: application/json' \
     --header 'Authorization: Bearer ${RUNPOD_API_KEY}'
   ```

## Technical Details

The implementation works by:

1. The `create_hf_collection.py` script creates a ChromaDB collection with the HuggingFaceEmbeddingFunction
2. When uploading documents, the `collection_name` is passed through API calls to the `process_chunks` function
3. The `process_chunks` function uses the specified collection or falls back to the default collection
4. When searching, the `collection_name` is passed to `get_collection` to query the right collection

This architecture allows total flexibility in managing multiple document collections with different embedding models or for different document sets.
