# RunPod vLLM Integration for Mixtral-8x7B

This document explains how to use RunPod's vLLM service as a drop-in replacement for OpenAI in our legal search RAG application.

## Overview

We've implemented a seamless way to switch between OpenAI and RunPod vLLM for LLM inference, allowing you to use Mixtral-8x7B or other models hosted on RunPod while keeping the same API interface.

## Setup Instructions

### 1. Create a RunPod vLLM Endpoint

1. Log in to your [RunPod account](https://www.runpod.io/console/serverless)
2. Go to Serverless > + New Endpoint
3. Configure your endpoint:
   - Name: `mixtral-endpoint` or any name of your choice
   - Select appropriate GPU (A100 or H100 recommended)
   - Container Image: `runpod/worker-v1-vllm:stable-cuda12.1.0`
   - Environment Variables:
     - `MODEL_NAME`: `mistralai/Mixtral-8x7B-v0.1`
     - `HF_TOKEN`: Your Hugging Face API token (for gated models)
4. Deploy the endpoint and note the Endpoint ID

### 2. Update Environment Variables

Add the following to your `.env` file:

```
# RunPod Settings
USE_RUNPOD=true
RUNPOD_API_KEY=your_runpod_api_key
RUNPOD_MIXTRAL_ENDPOINT_ID=your_runpod_endpoint_id
```

### 3. Restart Your Application

Restart your FastAPI application to apply the changes.

## How It Works

1. We use a factory pattern to choose between OpenAI and RunPod clients
2. The RunPod client adapter provides the same interface as OpenAI
3. The existing code works without changes by using this adapter

## Testing

You can verify the integration by:

1. Setting `USE_RUNPOD=true` in your `.env` file
2. Checking the logs - you should see "Using RunPod vLLM client for LLM inference"
3. Making a request to the `/query/rag` endpoint
4. Confirming the response is from Mixtral-8x7B


## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify your RunPod API key is correct
2. **Model Loading Errors**: Ensure your Hugging Face token has access to the model
3. **Timeout Errors**: Increase the client timeout in `runpod_client.py` if needed

### Logs to Check

- Application logs for client initialization messages
- RunPod serverless dashboard for endpoint errors
- RunPod worker logs for detailed model loading issues

## Reference

- [RunPod vLLM Documentation](https://docs.runpod.io/serverless/vllm/get-started)
- [Mixtral-8x7B Model](https://huggingface.co/mistralai/Mixtral-8x7B-v0.1)
