# Testing Your RunPod vLLM Integration

This guide will walk you through testing the RunPod vLLM integration for Mixtral-8x7B.

## Prerequisites

1. A RunPod account with API key
2. A deployed RunPod vLLM endpoint with Mixtral-8x7B
3. Python 3.7+ with required dependencies:
   - httpx
   - python-dotenv
   - asyncio

## Step 1: Configure Environment Variables

Create a `.env` file with the following variables:

```
# RunPod Settings
USE_RUNPOD=true
RUNPOD_API_KEY=your_runpod_api_key
RUNPOD_MIXTRAL_ENDPOINT_ID=your_endpoint_id

# Required for OpenAI fallback
OPENAI_API_KEY=your_openai_api_key
```

Make sure to replace:
- `your_runpod_api_key` with your RunPod API key
- `your_endpoint_id` with your RunPod endpoint ID (e.g., nlwx0t95z8sw2f)

## Step 2: Run the Tests

The test suite provides multiple testing options:

```bash
# Run all tests
python test_runpod.py

# Run only the direct API test (no app dependencies)
python test_runpod.py --direct

# Run only the factory integration test
python test_runpod.py --factory

# Run only the multiple queries test
python test_runpod.py --multiple

# Enable debug logging for more verbose output
python test_runpod.py --debug
```

The test script will:
1. Verify your environment variables are set correctly
2. Connect to your RunPod endpoint
3. Run the selected tests
4. Display a summary of test results

## Step 3: Test the API Integration

After confirming the client works, you can test the API integration:

1. Start the API server:
   ```bash
   python api.py
   ```

2. Send a test request to the `/query/rag` endpoint:
   ```bash
   curl -X POST "http://localhost:8000/query/rag" \
     -H "Content-Type: application/json" \
     -d '{"query":"What does the law say about copyright?", "limit":3, "max_tokens":500, "temperature":0.7}'
   ```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Error: "RunPod API error: 401 - Unauthorized"
   - Solution: Check your RUNPOD_API_KEY

2. **Endpoint Not Found**:
   - Error: "RunPod API error: 404 - Not Found"
   - Solution: Verify your RUNPOD_MIXTRAL_ENDPOINT_ID

3. **Timeout Errors**:
   - Error: "Request timed out after 120 seconds"
   - Solution: Increase timeout in the RunPod client

4. **Import Errors**:
   - Error: "No module named 'app.core.config'"
   - Solution: Make sure the directory structure is correct and Python path is set
   - For direct testing only, use the `--direct` flag to bypass app imports

### RunPod Dashboard

Always check the RunPod dashboard for endpoint status and logs. If your endpoint is showing "Ready" but requests fail, check the logs for any issues with the model loading or GPU memory.
