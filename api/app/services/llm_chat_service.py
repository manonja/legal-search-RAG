from typing import Any, Dict, Optional, Union

import requests
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.core.config import get_settings
from app.core.struct_logger import log

settings = get_settings()

REQUEST_TIMEOUT = 60


class ChatPromptResponse(BaseModel):
    """
    Model for chat prompt response.
    """

    content: str = Field(..., description="The generated text response")
    metadata: Dict[str, Any] = Field(..., description="Metadata about the response")


class LlmChatService:
    """
    Service for interacting with language models for chat completion.

    This service provides methods to send prompts to language models and process their responses.
    It handles the communication with the underlying LLM API and provides a consistent interface
    regardless of the specific LLM being used.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM Chat Service.
        """

        # Additional initialization could include setting up the client for specific LLM providers
        log.info("LlmChatService initialization: Checking LLM Health")
        health_response = requests.get(
            f"{get_settings().RUNPOD_LLM_URL}/health",
            headers=self._runpod_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        if health_response.status_code != 200:
            raise HTTPException(
                status_code=health_response.status_code, detail=health_response.text
            )
        log.info("LLM Chat Service initialized")

    def _runpod_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_settings().RUNPOD_API_KEY}",
        }

    def prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> ChatPromptResponse:
        """
        Send a prompt to the language model and get a response.

        Args:
            system_prompt: Instructions that guide the model's behavior.
            user_prompt: The actual user query or message.
            max_tokens: Maximum number of tokens to generate. Default is 1024.
            temperature: Controls randomness in the output.
            Higher values (e.g., 0.8) make output more random,
            lower values (e.g., 0.2) make it more deterministic.
            Default is 0.7.

        Returns:
            A string containing the model's response.

        Raises:
            HTTPException: With appropriate status code when an error occurs.
            LlmConnectionError: When connection to the LLM provider fails.
            LlmAuthenticationError: When authentication with LLM provider fails.
            LlmQuotaExceededError: When API quota or rate limits are exceeded.
            LlmInvalidRequestError: When the request to the LLM provider is invalid.
        """
        # Log the request with relevant context
        log.info(
            "Sending prompt to LLM",
            prompt_length=len(user_prompt),
            max_tokens=max_tokens,
            temperature=temperature,
        )

        headers = self._runpod_headers()

        payload = {
            "input": {
                "prompt": f"""<s>[INST] {system_prompt} [/INST]
{user_prompt}</s>""",
                "sampling_params": {
                    "max_tokens": max_tokens,  # Explicit token limit
                    "stop_token_ids": [2],  # EOS token ID
                    "ignore_eos": False,  # Allow natural termination
                    "temperature": temperature,
                },
            }
        }

        response = requests.post(
            f"{get_settings().RUNPOD_LLM_URL}/runsync",
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text,
            )

        if response.json()["status"] == "IN_QUEUE":
            raise RuntimeError("LLM cound't process our response")

        log.info("Response received from LLM", response=response.json())

        if (
            "output" in response.json()
            and len(response.json()["output"]) > 0
            and "choices" in response.json()["output"][0]
            and len(response.json()["output"][0]["choices"]) > 0
            and "tokens" in response.json()["output"][0]["choices"][0]
            and len(response.json()["output"][0]["choices"][0]["tokens"]) > 0
        ):
            content = response.json()["output"][0]["choices"][0]["tokens"][0]
            clean_content = self._clean_response_text(content)
            return ChatPromptResponse(
                content=clean_content,
                metadata=response.json(),
            )

        raise RuntimeError("LLM returned an unexpected response")

    def _clean_response_text(self, response: str) -> str:
        """Remove instruction tokens and normalise repetitive content."""
        clean_text = response.replace("[INST]", "").replace("[/INST]", "")

        # SPlit into lines and remove duplicates while preserving order
        lines = clean_text.strip().split("\n")
        unique_lines = []
        seen = set()
        for line in lines:
            line_stripped = line.strip()
            if (
                line_stripped
                and line_stripped not in seen
                and not line_stripped.isspace()
            ):
                seen.add(line_stripped)
                unique_lines.append(line)

        return "\n".join(unique_lines)
