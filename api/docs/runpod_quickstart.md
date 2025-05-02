# RunPod Privacy-Focused Implementation Quickstart

This document provides a quick guide to set up and validate the privacy-focused implementation of the Legal Search RAG system using RunPod.

## Overview

Our implementation eliminates all OpenAI dependencies in favor of self-hosted models on RunPod:

1. **Embedding Generation**: Uses the legal-bert-base-uncased model on RunPod serverless
2. **LLM Inference**: Uses the Mixtral-8x7B-v0.1 model on RunPod serverless
3. **Vector Database**: Uses ChromaDB with our custom RunPod-based embedding function

## Prerequisites

* RunPod account with API key
* Two RunPod serverless endpoints (see below)
* The following environment variables set:
  * `RUNPOD_API_KEY` - Your RunPod API key
  * `RUNPOD_MIXTRAL_ENDPOINT_ID` - Endpoint ID for the LLM
  * `RUNPOD_EMBEDDING_ENDPOINT_ID` - Endpoint ID for the embedding model

## Setting Up RunPod Endpoints

### 1. Embedding Endpoint

This endpoint will generate embeddings using the legal-bert-base-uncased model.

1. Go to RunPod Serverless → Create Endpoint
2. Select a suitable GPU (A10 or better recommended)
3. Choose "Docker Image" as template type
4. Enter the Docker image URL for your embedding handler:
   ```
   yourdockerrepo/legal-embeddings:latest
   ```
5. Add the following environment variable:
   * `HF_EMBEDDING_MODEL`: nlpaueb/legal-bert-base-uncased
6. Set memory requirements to at least 4GB
7. Create the endpoint and note the endpoint ID

### 2. LLM Endpoint

This endpoint will run the Mixtral model for inference.

1. Go to RunPod Serverless → Create Endpoint
2. Select a suitable GPU (A100 or better recommended for Mixtral)
3. Choose "vLLM" as the template type
4. Select "mistralai/Mixtral-8x7B-v0.1" as the model
5. Set memory requirements to at least 80GB
6. Create the endpoint and note the endpoint ID

## Environment Setup

Create a `.env` file in the project root with the following contents:

```
# RunPod Configuration
RUNPOD_API_KEY=your_runpod_api_key
RUNPOD_MIXTRAL_ENDPOINT_ID=your_mixtral_endpoint_id
RUNPOD_EMBEDDING_ENDPOINT_ID=your_embedding_endpoint_id
HF_EMBEDDING_MODEL=nlpaueb/legal-bert-base-uncased
USE_RUNPOD=true

# ChromaDB Configuration
COLLECTION_NAME=legal_docs
CHROMA_DIR=./data/chroma

# Other Settings
LOG_LEVEL=INFO
```

## Testing the Implementation

We've provided several test scripts to verify the implementation:

### 1. Basic Integration Test

```bash
python test_privacy_integration.py
```

This script tests both embedding generation and LLM inference to ensure everything is working correctly.

### 2. Network Isolation Test

```bash
python test_network_isolation.py
```

This script monitors network traffic to ensure no calls are made to external APIs like OpenAI.

### 3. Performance Benchmark

```bash
python test_performance.py
```

This script benchmarks the performance of the RunPod implementation, measuring latency, throughput, and cost characteristics.

## Component Architecture

```
┌───────────────────┐     ┌─────────────────────┐     ┌────────────────┐
│                   │     │                     │     │                │
│  Legal Documents  │────▶│  Document Chunking  │────▶│  ChromaDB      │
│                   │     │                     │     │  with HF       │
└───────────────────┘     └─────────────────────┘     │  Embeddings    │
                                                      │                │
                                                      └────────┬───────┘
                                                               │
                          ┌─────────────────────┐             │
                          │                     │             │
                          │  User Query         │             │
                          │                     │             │
                          └──────────┬──────────┘             │
                                     │                        │
                                     ▼                        ▼
                          ┌─────────────────────┐     ┌────────────────┐
                          │                     │     │                │
                          │  Query Embedding    │────▶│  Vector        │
                          │  (RunPod)           │     │  Similarity    │
                          │                     │     │  Search        │
                          └─────────────────────┘     │                │
                                                      └────────┬───────┘
                                                               │
                                                               │
                                                               ▼
                                                      ┌────────────────┐
                                                      │                │
                                                      │  LLM Response  │
                                                      │  (RunPod)      │
                                                      │                │
                                                      └────────────────┘
```

## Code Examples

### Creating Embeddings

```python
from app.services.database.embedding_function import HuggingFaceEmbeddingFunction

# Create embedding function
ef = HuggingFaceEmbeddingFunction()

# Generate embeddings
texts = ["This is a legal document about data privacy."]
embeddings = ef(texts)
```

### Using ChromaDB with the Custom Embedding Function

```python
import chromadb
from app.services.database.embedding_function import HuggingFaceEmbeddingFunction

# Create client
client = chromadb.PersistentClient(path="./data/chroma")

# Create collection with custom embedding function
ef = HuggingFaceEmbeddingFunction()
collection = client.get_or_create_collection(
    name="legal_docs",
    embedding_function=ef
)

# Add documents
collection.add(
    documents=["This is a document about GDPR."],
    ids=["doc1"],
    metadatas=[{"source": "EU regulations"}]
)

# Query
results = collection.query(
    query_texts=["What are the data privacy regulations?"],
    n_results=3
)
```

### Using the LLM Client

```python
import asyncio
from app.services.llm.factory import get_llm_client

async def generate_response():
    # Get LLM client
    llm_client = get_llm_client()

    # Generate a response
    response = await llm_client.chat_completions_create(
        model=llm_client.model_name,
        messages=[
            {"role": "system", "content": "You are a legal assistant."},
            {"role": "user", "content": "Explain GDPR briefly."}
        ],
        temperature=0.7,
        max_tokens=150
    )

    # Print the response
    print(response.choices[0].message.content)

# Run the async function
asyncio.run(generate_response())
```

## Troubleshooting

### Common Issues and Solutions

1. **RunPod API Error**: Check your API key and endpoint IDs are correct in the .env file.

2. **Memory Issues with Mixtral**: Ensure your RunPod endpoint has enough memory (80GB+) for the Mixtral-8x7B model.

3. **Slow Performance**: Embeddings and LLM inference on RunPod include cold start times. For production, keep endpoints warm by setting min_workers > 0.

4. **ChromaDB Collection Errors**: If you previously used OpenAI embeddings, create a new collection as embedding dimensions will differ.

## Next Steps

After setting up and validating the privacy-focused implementation, you can:

1. Optimize embedding parameters for the legal domain
2. Fine-tune the LLM for improved legal knowledge
3. Implement caching for frequently used queries
4. Set up monitoring and alerting for the RunPod endpoints

For any questions or issues, please contact the development team.
