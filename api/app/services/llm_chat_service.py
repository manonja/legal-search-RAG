from typing import Any, Dict, Optional, Union

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, validator


# Custom exception classes for LLM service
class LlmServiceError(Exception):
    """Base exception class for LLM service errors."""

    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        self.message = message
        self.detail = detail or {}
        super().__init__(message)


class LlmConnectionError(LlmServiceError):
    """Raised when connection to LLM provider fails."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class LlmAuthenticationError(LlmServiceError):
    """Raised when authentication with LLM provider fails."""

    status_code = status.HTTP_401_UNAUTHORIZED


class LlmQuotaExceededError(LlmServiceError):
    """Raised when API quota or rate limits are exceeded."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS


class LlmInvalidRequestError(LlmServiceError):
    """Raised when the request to the LLM provider is invalid."""

    status_code = status.HTTP_400_BAD_REQUEST


class ChatPromptRequest(BaseModel):
    """
    Model for chat prompt request parameters.
    """

    system_prompt: str = Field(
        ..., description="System instructions that guide the model's behavior"
    )
    user_prompt: str = Field(..., description="The actual user query or message")
    max_tokens: int = Field(1024, description="Maximum number of tokens to generate")
    temperature: float = Field(
        0.7,
        description="Controls randomness in the output. Higher values (e.g., 0.8) make output more random, lower values (e.g., 0.2) make it more deterministic",
    )

    @validator("max_tokens")
    def validate_max_tokens(cls, v):
        if v <= 0:
            raise ValueError("max_tokens must be greater than 0")
        return v

    @validator("temperature")
    def validate_temperature(cls, v):
        if v < 0 or v > 1:
            raise ValueError("temperature must be between 0 and 1")
        return v


class ChatPromptResponse(BaseModel):
    """
    Model for chat prompt response.
    """

    content: str = Field(..., description="The generated text response")
    usage: Optional[Dict[str, Any]] = Field(
        None, description="Token usage statistics if available"
    )


class LlmChatService:
    """
    Service for interacting with language models for chat completion.

    This service provides methods to send prompts to language models and process their responses.
    It handles the communication with the underlying LLM API and provides a consistent interface
    regardless of the specific LLM being used.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the LLM Chat Service.

        Args:
            api_key: API key for the LLM provider. If None, will attempt to use environment variables.
            model: The specific model to use for completions.
        """
        from app.core.struct_logger import log

        self.log = log.bind(component="llm_service", model=model)
        self.api_key = api_key
        self.model = model
        # Additional initialization could include setting up the client for specific LLM providers

    def prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
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
        try:
            # Log the request with relevant context
            self.log.info(
                "Sending prompt to LLM",
                prompt_length=len(user_prompt),
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # Validate input parameters using Pydantic model
            request = ChatPromptRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # This is a placeholder for the actual implementation
            # In a real implementation, this would call the LLM API
            # Example with OpenAI's API:
            # try:
            #     response = openai.ChatCompletion.create(
            #         model=self.model,
            #         messages=[
            #             {"role": "system", "content": request.system_prompt},
            #             {"role": "user", "content": request.user_prompt}
            #         ],
            #         max_tokens=request.max_tokens,
            #         temperature=request.temperature
            #     )
            #     self.log.info("LLM response received", tokens_used=response.usage.total_tokens)
            #     return response.choices[0].message.content
            # except openai.error.APIConnectionError as e:
            #     raise LlmConnectionError("Failed to connect to LLM provider", {"error": str(e)})
            # except openai.error.AuthenticationError as e:
            #     raise LlmAuthenticationError("Invalid API key", {"error": str(e)})
            # except openai.error.RateLimitError as e:
            #     raise LlmQuotaExceededError("Rate limit exceeded", {"error": str(e)})
            # except openai.error.InvalidRequestError as e:
            #     raise LlmInvalidRequestError("Invalid request parameters", {"error": str(e)})

            # For now, return a placeholder
            self.log.info("LLM placeholder response generated")
            return f"This is a placeholder response. In a real implementation, this would be the response from the LLM for system prompt: '{system_prompt}' and user prompt: '{user_prompt}'."

        except ValueError as e:
            # Convert Pydantic validation errors to HTTP 422 errors
            self.log.warning("Validation error", error=str(e))
            # In a FastAPI context, you can directly raise an HTTPException
            # or return this in a format that can be converted to an HTTP response
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "Invalid request parameters", "error": str(e)},
            ) from e
        except LlmServiceError as e:
            # Log and re-raise custom service errors with context
            self.log.error(e.message, error_type=e.__class__.__name__, **e.detail)
            # In a FastAPI context, convert to HTTPException with appropriate status
            raise HTTPException(
                status_code=getattr(
                    e, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail={"message": e.message, **e.detail},
            ) from e
        except Exception as e:
            # Catch truly unexpected errors, log them in detail, and return a generic error
            # This acts as a last resort to prevent exposing sensitive information
            self.log.error(
                "Unexpected error in LLM service",
                error_type=e.__class__.__name__,
                error=str(e),
                exc_info=True,
            )
            # Using from None to hide implementation details for security
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": "An unexpected error occurred while processing your request"
                },
            ) from None

    async def prompt_async(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """
        Asynchronous version of prompt method.

        This method provides the same functionality as prompt() but operates asynchronously,
        which is useful for high-throughput applications.

        Args:
            system_prompt: Instructions that guide the model's behavior.
            user_prompt: The actual user query or message.
            max_tokens: Maximum number of tokens to generate. Default is 1024.
            temperature: Controls randomness in the output. Higher values make output more random. Default is 0.7.

        Returns:
            A string containing the model's response.

        Raises:
            HTTPException: With appropriate status code when an error occurs.
            LlmConnectionError: When connection to the LLM provider fails.
            LlmAuthenticationError: When authentication with LLM provider fails.
            LlmQuotaExceededError: When API quota or rate limits are exceeded.
            LlmInvalidRequestError: When the request to the LLM provider is invalid.
        """
        # This is a placeholder for an async implementation
        # In a real implementation, this would use an async client to call the LLM API
        # Example with OpenAI's async API:
        # try:
        #     async with openai.AsyncOpenAI(api_key=self.api_key) as client:
        #         response = await client.chat.completions.create(
        #             model=self.model,
        #             messages=[...],
        #             max_tokens=max_tokens,
        #             temperature=temperature
        #         )
        #         return response.choices[0].message.content
        # except ... # Same error handling as in the synchronous method

        # For now, just call the synchronous version
        return self.prompt(system_prompt, user_prompt, max_tokens, temperature)
