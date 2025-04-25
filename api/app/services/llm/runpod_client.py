"""
RunPod vLLM client adapter that provides an interface similar to OpenAI.

This client connects to a RunPod vLLM endpoint and handles all communication,
providing a drop-in replacement for OpenAI's API client.
"""

import os
import json
import time
import httpx
import logging
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field  # Import Pydantic

# Configure logging
logger = logging.getLogger(__name__)


# --- Define Pydantic models to mimic OpenAI response structure ---
class Message(BaseModel):
    role: str
    content: Optional[str] = None


class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = None


class Usage(BaseModel):
    prompt_tokens: Optional[int] = 0
    completion_tokens: Optional[int] = 0
    total_tokens: Optional[int] = 0


class ChatCompletion(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage
    error: Optional[Dict] = None  # Added field for potential errors


# -----------------------------------------------------------------


class RunPodClient:
    """Client for interacting with RunPod vLLM endpoints.

    This client provides an interface similar to OpenAI's API client,
    making it easier to switch between the two.
    """

    def __init__(
        self,
        api_key: str,
        endpoint_id: str,
        model_name: str = "mistralai/Mixtral-8x7B-v0.1",
        timeout: int = 120,
    ):
        """Initialize the RunPod client.

        Args:
            api_key: RunPod API key
            endpoint_id: RunPod endpoint ID
            model_name: Name of the model to use (mostly for record-keeping)
            timeout: Request timeout in seconds
        """
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
        top_p: float = 0.95,
        stream: bool = False,
        frequency_penalty: float = 0,
        presence_penalty: float = 0,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs,
    ) -> ChatCompletion:
        """Create a chat completion using RunPod vLLM endpoint.

        Returns:
            ChatCompletion: An object mimicking OpenAI's response structure.
        """
        try:
            logger.info(
                f"Sending request to RunPod endpoint {self.endpoint_id} with "
                f"{len(messages)} messages, temp={temperature}, max_tokens={max_tokens}"
            )

            payload = {
                "input": {
                    "messages": messages,
                    "stream": stream,
                    "sampling_params": {
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "top_p": top_p,
                        "frequency_penalty": frequency_penalty,
                        "presence_penalty": presence_penalty,
                    },
                }
            }

            if stop:
                payload["input"]["sampling_params"]["stop"] = (
                    stop if isinstance(stop, list) else [stop]
                )

            endpoint = "stream" if stream else "runsync"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/{endpoint}", headers=self.headers, json=payload
                )

                if response.status_code != 200:
                    logger.error(
                        f"RunPod API error: {response.status_code} - {response.text}"
                    )
                    # Return a ChatCompletion object indicating the error
                    return ChatCompletion(
                        id=f"error-{int(time.time())}",
                        created=int(time.time()),
                        model=self.model_name,
                        choices=[],
                        usage=Usage(),
                        error={
                            "message": f"RunPod API error: {response.text}",
                            "type": "api_error",
                            "status": response.status_code,
                        },
                    )

                result = response.json()

                if stream:
                    raise NotImplementedError(
                        "Streaming not fully implemented in RunPodClient adapter"
                    )

                output = result.get("output", {})
                usage_data = output.get("usage", {})

                # Construct the ChatCompletion object
                completion = ChatCompletion(
                    id=result.get(
                        "id", f"runpod-{self.endpoint_id}-{int(time.time())}"
                    ),
                    created=result.get("created", int(time.time())),
                    model=self.model_name,  # Use the configured model name
                    choices=[
                        Choice(
                            index=0,
                            message=Message(
                                role="assistant", content=output.get("text", "")
                            ),
                            finish_reason="stop",  # Assuming stop for now
                        )
                    ],
                    usage=Usage(
                        prompt_tokens=usage_data.get("prompt_tokens", 0),
                        completion_tokens=usage_data.get("completion_tokens", 0),
                        total_tokens=usage_data.get("total_tokens", 0),
                    ),
                )

                return completion

        except Exception as e:
            logger.exception(f"Error in RunPod client: {str(e)}")
            # Return a ChatCompletion object indicating the error
            return ChatCompletion(
                id=f"error-{int(time.time())}",
                created=int(time.time()),
                model=self.model_name,
                choices=[],
                usage=Usage(),
                error={
                    "message": f"RunPod client error: {str(e)}",
                    "type": "client_error",
                },
            )

    async def completions_create(self, *args, **kwargs):
        # Simplified: Currently just wraps chat_completions_create
        # Ideally, this would also return an object compatible with OpenAI's legacy Completion object
        # For now, we return the ChatCompletion object from the chat method
        logger.warning(
            "RunPodClient.completions_create currently uses chat completion logic and returns ChatCompletion object"
        )
        return await self.chat_completions_create(*args, **kwargs)
