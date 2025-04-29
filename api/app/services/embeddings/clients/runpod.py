"""
Client for interacting with a RunPod Serverless endpoint dedicated to generating embeddings.
"""

import httpx
from typing import List, Optional
from app.core.struct_logger import log


class RunPodEmbeddingClient:
    """Client to send text to a RunPod embedding endpoint and get vectors back."""

    def __init__(
        self,
        api_key: str,
        endpoint_id: str,
        model_name: str,  # For logging/reference
        timeout: int = 120,  # Increased timeout for potentially large batches
    ):
        """Initialize the RunPod embedding client.

        Args:
            api_key: RunPod API key.
            endpoint_id: The specific ID of the RunPod embedding endpoint.
            model_name: The name of the embedding model being used (e.g., nlpaueb/legal-bert-base-uncased).
            timeout: Request timeout in seconds.
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
        log.info(
            "RunPod Embedding Client initialized",
            endpoint_id=self.endpoint_id,
            model_name=self.model_name,
        )

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using the RunPod endpoint."""
        if not texts:
            return []

        payload = {"input": {"texts": texts}}
        # Use runsync for potentially long-running embedding tasks
        endpoint_url = f"{self.base_url}/runsync"

        log.debug(
            f"Sending {len(texts)} texts to RunPod embedding endpoint",
            endpoint_id=self.endpoint_id,
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint_url, headers=self.headers, json=payload
                )

            response.raise_for_status()  # Raise HTTPStatusError for bad responses (4xx or 5xx)

            result = response.json()

            # Handle potential RunPod execution delays or errors
            if result.get("status") == "FAILED":
                error_details = result.get("error", "Unknown error from RunPod worker.")
                log.error(
                    "RunPod embedding job failed",
                    endpoint_id=self.endpoint_id,
                    runpod_status=result.get("status"),
                    runpod_error=error_details,
                )
                raise RuntimeError(f"RunPod embedding job failed: {error_details}")

            # We expect status COMPLETED for runsync
            if result.get("status") != "COMPLETED":
                log.warning(
                    "RunPod embedding job status unexpected",
                    endpoint_id=self.endpoint_id,
                    runpod_status=result.get("status"),
                    runpod_result=result,  # Log full result for debugging
                )
                # Attempt to extract output anyway, but log warning

            output = result.get("output", {})
            embeddings = output.get("embeddings")

            if embeddings is None:
                log.error(
                    "'embeddings' key not found in RunPod response output",
                    endpoint_id=self.endpoint_id,
                    runpod_output=output,
                )
                raise ValueError(
                    "Invalid response format from RunPod embedding endpoint."
                )

            if not isinstance(embeddings, list) or (
                embeddings and not isinstance(embeddings[0], list)
            ):
                log.error(
                    "RunPod response 'embeddings' is not a list of lists",
                    endpoint_id=self.endpoint_id,
                    output_type=type(embeddings).__name__,
                )
                raise ValueError("Invalid embedding format received.")

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
            raise ConnectionError(
                f"RunPod API error: {e.response.status_code} - {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            log.error(
                "Request error calling RunPod embedding endpoint",
                endpoint_id=self.endpoint_id,
                error=str(e),
                exc_info=True,
            )
            raise ConnectionError(f"Could not connect to RunPod: {str(e)}") from e
        except Exception as e:
            log.error(
                "Unexpected error in RunPod embedding client",
                endpoint_id=self.endpoint_id,
                error=str(e),
                exc_info=True,
            )
            raise
