"""
Client for interacting with a RunPod Serverless endpoint dedicated to generating embeddings.
"""

import httpx
import time
import asyncio
import secrets
import random
from typing import List, Optional, Dict, Any, Union
from app.core.struct_logger import log


class RunPodEmbeddingClient:
    """Client to send text to a RunPod embedding endpoint and get vectors back."""

    def __init__(
        self,
        api_key: str,
        endpoint_id: str,
        model_name: str,  # For logging/reference
        timeout: int = 180,  # Increased timeout for potentially large batches
        max_retries: int = 15,  # Increased from 5 to 15
        poll_interval: float = 2.0,
    ):
        """Initialize the RunPod embedding client.

        Args:
            api_key: RunPod API key.
            endpoint_id: The specific ID of the RunPod embedding endpoint.
            model_name: The name of the embedding model being used (e.g., nlpaueb/legal-bert-base-uncased).
            timeout: Request timeout in seconds.
            max_retries: Maximum number of polling retries for queued jobs.
            poll_interval: Initial time in seconds between polling attempts.
        """
        if not api_key:
            raise ValueError("RunPod API key is required.")
        if not endpoint_id:
            raise ValueError("RunPod embedding endpoint ID is required.")

        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.model_name = model_name
        self.timeout = timeout
        self.base_url = f"https://api.runpod.ai/v2/{self.endpoint_id}"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.max_retries = max_retries
        self.poll_interval = poll_interval

        # Cache for job results to avoid duplicate processing
        self._job_cache: Dict[str, Optional[Dict[str, Any]]] = {}

        log.info(
            "RunPod Embedding Client initialized",
            endpoint_id=self.endpoint_id,
            model_name=self.model_name,
            max_retries=self.max_retries,
            timeout=self.timeout,
        )

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using the RunPod endpoint."""
        if not texts:
            return []

        # Generate a cache key based on the content
        cache_key = hash(tuple(texts))
        if cache_key in self._job_cache:
            log.info(f"Returning cached embeddings for {len(texts)} texts")
            return self._job_cache[cache_key]

        payload = {"input": {"texts": texts}}
        # Use runsync for potentially long-running embedding tasks
        endpoint_url = f"{self.base_url}/runsync"

        log.debug(
            f"Sending {len(texts)} texts to RunPod embedding endpoint",
            endpoint_id=self.endpoint_id,
        )

        try:
            # First attempt to use a streaming approach for more resilience
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    response = await client.post(
                        endpoint_url, headers=self.headers, json=payload
                    )
                    response.raise_for_status()
                    result = response.json()
                except (httpx.HTTPStatusError, httpx.RequestError) as e:
                    log.warning(
                        f"Initial request to RunPod failed, retrying with different approach: {str(e)}",
                        endpoint_id=self.endpoint_id,
                    )
                    # Fall back to async endpoint if runsync has issues
                    result = await self._send_async_request(payload, client)

            # Handle job queuing with polling
            if result.get("status") == "IN_QUEUE":
                log.info(
                    "RunPod embedding job queued, polling for completion",
                    endpoint_id=self.endpoint_id,
                    job_id=result.get("id"),
                )

                # Poll for completion
                job_id = result.get("id")
                result = await self._poll_job_status(job_id, client=None)

            # Handle potential RunPod execution failures
            if result.get("status") == "FAILED":
                error_details = result.get("error", "Unknown error from RunPod worker.")
                log.error(
                    "RunPod embedding job failed",
                    endpoint_id=self.endpoint_id,
                    runpod_status=result.get("status"),
                    runpod_error=error_details,
                )

                # Try one more time with async endpoint if sync failed
                log.info("Retrying with async endpoint after sync failure")
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    result = await self._send_async_request(payload, client)
                    if result.get("status") == "IN_QUEUE":
                        job_id = result.get("id")
                        result = await self._poll_job_status(job_id, client=None)

                if result.get("status") == "FAILED":
                    error_details = result.get(
                        "error", "Unknown error from RunPod worker."
                    )
                    raise RuntimeError(
                        f"RunPod embedding job failed after retry: {error_details}"
                    )

            # We expect status COMPLETED for runsync
            if result.get("status") != "COMPLETED":
                log.warning(
                    "RunPod embedding job status unexpected",
                    endpoint_id=self.endpoint_id,
                    runpod_status=result.get("status"),
                    runpod_result=result,  # Log full result for debugging
                )
                # Attempt to extract output anyway, but log warning

            # Extract embeddings from response with multiple fallbacks
            embeddings = await self._extract_embeddings_from_response(result)

            # Cache the results
            self._job_cache[cache_key] = embeddings

            log.debug(f"Received {len(embeddings)} embeddings from RunPod.")
            return embeddings

        except httpx.HTTPStatusError as e:
            log.error(
                "HTTP error calling RunPod embedding endpoint",
                status_code=e.response.status_code,
                response_text=e.response.text,
                endpoint_id=self.endpoint_id,
                exc_info=True,
            )
            # Return fallback embeddings when we can't connect
            dimension = 768
            return [[0.0] * dimension for _ in range(len(texts))]
        except httpx.RequestError as e:
            log.error(
                "Request error calling RunPod embedding endpoint",
                endpoint_id=self.endpoint_id,
                error=str(e),
                exc_info=True,
            )
            # Return fallback embeddings when we can't connect
            dimension = 768
            return [[0.0] * dimension for _ in range(len(texts))]
        except Exception as e:
            log.error(
                "Unexpected error in RunPod embedding client",
                endpoint_id=self.endpoint_id,
                error=str(e),
                exc_info=True,
            )
            # Return fallback embeddings
            dimension = 768
            return [[0.0] * dimension for _ in range(len(texts))]

    async def _send_async_request(
        self, payload: Dict[str, Any], client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """Send request using the async endpoint instead of runsync."""
        endpoint_url = f"{self.base_url}/run"
        response = await client.post(endpoint_url, headers=self.headers, json=payload)
        response.raise_for_status()
        result = response.json()

        # Async endpoint always returns a job ID that needs polling
        if "id" in result:
            job_id = result.get("id")
            return await self._poll_job_status(job_id, client)

        # Fallback if no job ID
        return result

    async def _poll_job_status(self, job_id: str, client=None) -> dict:
        """Poll for job status until completion or max retries.

        Args:
            job_id: The RunPod job ID to poll
            client: Optional httpx client to reuse. If None, creates a new client.

        Returns:
            The final job status response

        Raises:
            RuntimeError: If polling exceeds max retries
        """
        should_close_client = False
        if client is None:
            client = httpx.AsyncClient(timeout=self.timeout)
            should_close_client = True

        poll_url = f"https://api.runpod.ai/v2/{self.endpoint_id}/status/{job_id}"
        retries = 0

        try:
            while retries < self.max_retries:
                try:
                    response = await client.get(poll_url, headers=self.headers)
                    response.raise_for_status()
                    status_data = response.json()

                    # Check if job is complete
                    if status_data.get("status") in ["COMPLETED", "FAILED"]:
                        log.info(
                            f"RunPod job {status_data.get('status')}",
                            endpoint_id=self.endpoint_id,
                            job_id=job_id,
                        )
                        return status_data

                    # Check if there's a delayTime hint from RunPod
                    delay_time = status_data.get("delayTime", None)

                    retries += 1

                    # Use exponential backoff with jitter
                    wait_time = min(
                        30.0,  # Cap at 30 seconds
                        self.poll_interval
                        * (2 ** (retries - 1))
                        * (0.5 + secrets.SystemRandom().random()),
                    )

                    # If RunPod provides a delay hint, use it if it's longer
                    if delay_time is not None and isinstance(delay_time, (int, float)):
                        wait_time = max(
                            wait_time, float(delay_time) / 1000.0
                        )  # Convert ms to s

                    log.debug(
                        f"Job still processing (attempt {retries}/{self.max_retries}, waiting {wait_time:.1f}s)",
                        endpoint_id=self.endpoint_id,
                        job_id=job_id,
                        status=status_data.get("status"),
                        wait_time=wait_time,
                    )

                    # Wait before polling again
                    await asyncio.sleep(wait_time)

                except (httpx.HTTPStatusError, httpx.RequestError) as e:
                    # If we get an error during polling, backoff and retry
                    retries += 1
                    wait_time = min(30.0, self.poll_interval * (2**retries))
                    log.warning(
                        f"Error polling job status (attempt {retries}/{self.max_retries}): {str(e)}",
                        wait_time=wait_time,
                    )
                    await asyncio.sleep(wait_time)

            # If we reach here, we've exceeded max_retries
            # Instead of failing, let's try one last direct status check with a longer timeout
            log.warning(
                f"Polling exceeded maximum retries ({self.max_retries}) for job {job_id}, making final attempt",
                endpoint_id=self.endpoint_id,
            )

            # Last chance - longer timeout, direct call
            try:
                final_client = httpx.AsyncClient(timeout=self.timeout * 2)
                response = await final_client.get(poll_url, headers=self.headers)
                response.raise_for_status()
                final_status = response.json()

                if final_status.get("status") in ["COMPLETED", "FAILED"]:
                    log.info(
                        f"Final attempt successful - RunPod job {final_status.get('status')}",
                        endpoint_id=self.endpoint_id,
                        job_id=job_id,
                    )
                    return final_status
            except Exception as e:
                log.error(f"Final attempt failed: {str(e)}")

            # If we get here, all attempts have failed
            raise RuntimeError(
                f"Polling exceeded maximum retries ({self.max_retries}) for job {job_id}"
            )

        finally:
            if should_close_client:
                await client.aclose()

    async def _extract_embeddings_from_response(
        self, result: Dict[str, Any]
    ) -> List[List[float]]:
        """Extract embeddings from RunPod response with multiple fallbacks."""
        # For logging/debugging
        dimension = 768  # Default dimension for legal-bert

        # Standard location
        output = result.get("output", {})

        # Sometimes the output might be directly in the result for completed jobs
        if not output and isinstance(result.get("output"), dict):
            output = result.get("output")

        # Try to get embeddings from standard location
        embeddings = output.get("embeddings")

        # If not found, try alternative locations
        if embeddings is None:
            log.warning(
                "'embeddings' key not found in standard location, trying alternatives",
                endpoint_id=self.endpoint_id,
                output_keys=list(output.keys())
                if isinstance(output, dict)
                else "not a dict",
            )

            # Case 1: Embeddings directly in output (as a list)
            if (
                isinstance(output, list)
                and len(output) > 0
                and isinstance(output[0], list)
            ):
                log.info("Found embeddings directly in output list")
                embeddings = output

            # Case 2: Embeddings in a nested structure
            elif isinstance(output, dict):
                # Try common variations
                for key in ["embedding", "vectors", "results", "data", "values"]:
                    if key in output and isinstance(output[key], list):
                        log.info(f"Found embeddings under key '{key}'")
                        embeddings = output[key]
                        break

            # Case 3: Look in the entire result for embeddings
            if embeddings is None:
                for key, value in result.items():
                    if (
                        isinstance(value, list)
                        and len(value) > 0
                        and isinstance(value[0], list)
                    ):
                        log.info(f"Found embeddings under root key '{key}'")
                        embeddings = value
                        break

            # Case 4: Generated placeholder embeddings as a last resort
            if embeddings is None:
                log.error(
                    "Could not find embeddings in response, returning fallback embeddings",
                    endpoint_id=self.endpoint_id,
                    result=result,
                )

                # Generate fallback embeddings with proper dimension
                return (
                    [[0.0] * dimension]
                    if not hasattr(self, "text_count") or not self.text_count
                    else [[0.0] * dimension for _ in range(self.text_count)]
                )

        # Validate format
        if not isinstance(embeddings, list):
            log.error(
                "RunPod response embeddings not in expected format (not a list)",
                endpoint_id=self.endpoint_id,
                output_type=type(embeddings).__name__,
            )
            return [[0.0] * dimension]

        if not embeddings:
            log.error(
                "RunPod returned empty embeddings list", endpoint_id=self.endpoint_id
            )
            return [[0.0] * dimension]

        if not isinstance(embeddings[0], list):
            log.error(
                "RunPod response embeddings not in expected format (not a list of lists)",
                endpoint_id=self.endpoint_id,
                first_item_type=type(embeddings[0]).__name__,
            )

            # Try to normalize the format if possible
            if isinstance(embeddings, list) and len(embeddings) > 0:
                # Single embedding returned as a flat list, wrap it
                log.info("Converting single flat embedding to list of lists")
                try:
                    return [embeddings]
                except Exception as e:
                    log.error(f"Failed to convert embedding format: {str(e)}")
                    return [[0.0] * dimension]

            return [[0.0] * dimension]

        # Last validation check
        if hasattr(embeddings, "__iter__") and not isinstance(
            embeddings, (str, bytes, dict)
        ):
            try:
                embeddings_list = list(embeddings)
                return embeddings_list
            except Exception as e:
                log.error(f"Failed to convert embeddings to list: {str(e)}")
                return [[0.0] * dimension]

        return embeddings
