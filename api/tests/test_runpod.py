#!/usr/bin/env python3
"""
RunPod vLLM Integration Test Suite

This script provides comprehensive testing for RunPod vLLM integration:
1. Direct API testing - Tests connection to RunPod without app dependencies
2. Factory integration testing - Tests the LLM factory pattern integration
3. Multiple queries testing - Tests stability with multiple sequential queries

Usage:
    python test_runpod.py [--direct] [--factory] [--multiple]

    --direct    Run only the direct API test
    --factory   Run only the factory integration test
    --multiple  Run the multiple queries test

    No arguments runs all tests in sequence.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, List, Any, Optional

import httpx
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("runpod_test")

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


class RunPodClientDirect:
    """Simplified RunPod client for direct testing."""

    def __init__(
        self,
        api_key: str,
        endpoint_id: str,
        model_name: str = "mistralai/Mixtral-8x7B-v0.1",
        timeout: int = 120,
    ):
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.model_name = model_name
        self.timeout = timeout
        self.base_url = f"https://api.runpod.ai/v2/{endpoint_id}"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def chat_completions_create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> Dict[str, Any]:
        try:
            logger.info(f"Sending request to RunPod endpoint {self.endpoint_id}")

            payload = {
                "input": {
                    "messages": messages,
                    "stream": False,
                    "sampling_params": {
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                }
            }

            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/runsync", headers=self.headers, json=payload
                )

                if response.status_code != 200:
                    logger.error(
                        f"RunPod API error: {response.status_code} - {response.text}"
                    )
                    return {
                        "error": {
                            "message": f"RunPod API error: {response.text}",
                            "type": "api_error",
                            "status": response.status_code,
                        }
                    }

                result = response.json()
                logger.debug(f"Raw response: {json.dumps(result, indent=2)}")

                # Convert RunPod format to OpenAI-compatible format
                output = result.get("output", {})

                openai_compatible = {
                    "id": result.get("id", f"runpod-{self.endpoint_id}"),
                    "object": "chat.completion",
                    "created": result.get("created", int(time.time())),
                    "model": self.model_name,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": output.get("text", ""),
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": output.get("usage", {}).get(
                            "prompt_tokens", 0
                        ),
                        "completion_tokens": output.get("usage", {}).get(
                            "completion_tokens", 0
                        ),
                        "total_tokens": output.get("usage", {}).get("total_tokens", 0),
                    },
                }

                return openai_compatible

        except Exception as e:
            logger.exception(f"Error in RunPod client: {str(e)}")
            return {
                "error": {
                    "message": f"RunPod client error: {str(e)}",
                    "type": "client_error",
                }
            }


async def test_direct_api():
    """Test RunPod client directly without factory pattern."""
    logger.info("=== Starting Direct API Test ===")

    # Get API key and endpoint ID
    api_key = os.getenv("RUNPOD_API_KEY")
    endpoint_id = os.getenv("RUNPOD_MIXTRAL_ENDPOINT_ID")

    if not api_key or not endpoint_id:
        logger.error(
            "RUNPOD_API_KEY or RUNPOD_MIXTRAL_ENDPOINT_ID not set in .env file"
        )
        return False

    logger.info(f"Using endpoint ID: {endpoint_id}")

    # Create client
    client = RunPodClientDirect(api_key=api_key, endpoint_id=endpoint_id)

    # Test messages
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {
            "role": "user",
            "content": "What is the capital of France? Keep it very brief.",
        },
    ]

    # Send request
    logger.info("Sending test request to RunPod vLLM endpoint...")
    response = await client.chat_completions_create(
        model="mixtral", messages=messages, temperature=0.7, max_tokens=100
    )

    # Check for errors
    if "error" in response:
        logger.error(f"Error: {response['error']['message']}")
        return False

    # Print response
    logger.info("-" * 50)
    logger.info(f"Response: {response['choices'][0]['message']['content']}")
    logger.info(f"Total tokens: {response['usage']['total_tokens']}")
    logger.info("-" * 50)
    logger.info("Direct API test completed successfully!")

    return True


async def test_factory_integration():
    """Test the LLM factory pattern integration."""
    logger.info("=== Starting Factory Integration Test ===")

    try:
        # Import the factory
        from app.services.llm.factory import get_llm_client

        logger.info("Successfully imported LLM factory")

        # Get the client from factory
        client = get_llm_client()

        # Check client type
        client_type = client.__class__.__name__
        logger.info(f"Factory returned client: {client_type}")

        # Verify RunPod client is being used if configured
        if os.getenv("USE_RUNPOD", "").lower() == "true":
            if "RunPod" not in client_type:
                logger.error(
                    f"USE_RUNPOD=true but factory returned {client_type} instead of RunPodClient"
                )
                return False
            logger.info("✓ Factory correctly selected RunPod client")
        else:
            if "OpenAI" not in client_type:
                logger.warning(
                    f"USE_RUNPOD=false but factory returned {client_type} instead of AsyncOpenAI"
                )
            logger.info("✓ Factory correctly selected OpenAI client")

        # Test with the client
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {
                "role": "user",
                "content": "What is the capital of France? Keep it very brief.",
            },
        ]

        logger.info("Sending test request via factory client...")

        # Test with chat completions
        response = await client.chat.completions.create(
            model="mixtral"
            if "RunPod" in client_type
            else os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        # Print the response
        logger.info("-" * 50)
        logger.info(f"Response: {response.choices[0].message.content}")
        logger.info(f"Total tokens: {response.usage.total_tokens}")
        logger.info("-" * 50)
        logger.info("Factory integration test completed successfully!")

        return True
    except ImportError as e:
        logger.error(f"Failed to import LLM factory: {e}")
        logger.error("Make sure the app directory structure is correct")
        return False
    except Exception as e:
        logger.error(f"Error testing factory integration: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


async def test_multiple_queries():
    """Test multiple queries to verify stability."""
    logger.info("=== Starting Multiple Queries Test ===")

    try:
        # Use direct client for stability
        api_key = os.getenv("RUNPOD_API_KEY")
        endpoint_id = os.getenv("RUNPOD_MIXTRAL_ENDPOINT_ID")

        if not api_key or not endpoint_id:
            logger.error(
                "RUNPOD_API_KEY or RUNPOD_MIXTRAL_ENDPOINT_ID not set in .env file"
            )
            return False

        client = RunPodClientDirect(api_key=api_key, endpoint_id=endpoint_id)

        # Test questions
        questions = [
            "What is the capital of France?",
            "What is the largest planet in our solar system?",
            "Who wrote the novel '1984'?",
        ]

        all_successful = True

        for i, question in enumerate(questions):
            logger.info(f"Sending question {i + 1}/{len(questions)}: {question}")

            try:
                response = await client.chat_completions_create(
                    model="mixtral",
                    messages=[{"role": "user", "content": question}],
                    temperature=0.7,
                    max_tokens=100,
                )

                if "error" in response:
                    logger.error(
                        f"Error on question {i + 1}: {response['error']['message']}"
                    )
                    all_successful = False
                    continue

                logger.info(
                    f"Response {i + 1}: {response['choices'][0]['message']['content']}"
                )
                logger.info(f"Tokens used: {response['usage']['total_tokens']}")
                logger.info("-" * 30)
            except Exception as e:
                logger.error(f"Exception on question {i + 1}: {str(e)}")
                all_successful = False

        if all_successful:
            logger.info("Multiple queries test completed successfully!")
        else:
            logger.warning("Multiple queries test completed with some errors")

        return all_successful
    except Exception as e:
        logger.error(f"Error in multiple queries test: {e}")
        return False


async def run_tests(args):
    """Run the selected tests based on command line arguments."""
    results = {}

    # If no specific tests are selected, run all tests
    run_all = not (args.direct or args.factory or args.multiple)

    if args.direct or run_all:
        results["direct"] = await test_direct_api()

    if (args.factory or run_all) and results.get("direct", True):
        results["factory"] = await test_factory_integration()

    if (args.multiple or run_all) and results.get("direct", True):
        results["multiple"] = await test_multiple_queries()

    # Display summary
    logger.info("\n=== Test Summary ===")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name.capitalize()} test: {status}")

    # Return True only if all tests passed
    return all(results.values())


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test RunPod vLLM integration")
    parser.add_argument(
        "--direct", action="store_true", help="Run only the direct API test"
    )
    parser.add_argument(
        "--factory", action="store_true", help="Run only the factory integration test"
    )
    parser.add_argument(
        "--multiple", action="store_true", help="Run the multiple queries test"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Set debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Load environment variables
    load_dotenv()

    if not os.getenv("RUNPOD_API_KEY") or not os.getenv("RUNPOD_MIXTRAL_ENDPOINT_ID"):
        logger.error(
            "Missing required environment variables. Set these in your .env file:"
        )
        logger.error("- RUNPOD_API_KEY: Your RunPod API key")
        logger.error("- RUNPOD_MIXTRAL_ENDPOINT_ID: Your RunPod endpoint ID")
        sys.exit(1)

    if not os.getenv("USE_RUNPOD", "").lower() == "true":
        logger.warning("USE_RUNPOD is not set to 'true' in your .env file.")
        logger.warning(
            "Direct tests will work, but factory will use OpenAI instead of RunPod."
        )

    # Run tests
    success = asyncio.run(run_tests(args))

    if success:
        logger.info("All selected tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("One or more tests failed.")
        sys.exit(1)
